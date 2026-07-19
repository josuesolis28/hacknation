"""Persistencia: Postgres en producción (Railway), SQLite en local si no hay
``DATABASE_URL`` configurado — mismo contrato de funciones para ambos.

Tablas:
- scans: historial de corridas completas (evita repetir el costo de una
  corrida solo por refrescar el navegador).
- decisions: anulaciones manuales (aprobar amarillo a la fuerza / descartar).
- users: cuentas de Google que iniciaron sesión.
- companies: una fila por startup ya vista (clave = nombre normalizado +
  país). Cada vez que una corrida nueva encuentra la misma startup, sus
  datos se *fusionan* con lo que ya había (rellena campos vacíos, une listas
  como equipo/evidencia/clientes) en vez de crear una entrada duplicada —
  así una segunda corrida no vuelve a "descubrir" lo mismo desde cero.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from .config import settings
from .models import PipelineResult

_IS_PG = bool(settings.database_url)
_SQLITE_PATH = Path(__file__).resolve().parent.parent / "vcbrain.db"
_lock = threading.Lock()


def _connect():
    if _IS_PG:
        import psycopg
        from psycopg.rows import dict_row

        url = settings.database_url.replace("postgres://", "postgresql://", 1)
        return psycopg.connect(url, row_factory=dict_row)
    else:
        import sqlite3

        conn = sqlite3.connect(_SQLITE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Esquema
# ---------------------------------------------------------------------------

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    query TEXT NOT NULL,
    provider_used TEXT NOT NULL,
    cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
    result_json JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    founder_key TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    google_sub TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    picture TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL,
    last_login_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS companies (
    company_key TEXT PRIMARY KEY,
    founder_json JSONB NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    times_seen INTEGER NOT NULL DEFAULT 1
);
"""

_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    query TEXT NOT NULL,
    provider_used TEXT NOT NULL,
    cost_usd REAL NOT NULL DEFAULT 0,
    result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    founder_key TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_sub TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    picture TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    last_login_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS companies (
    company_key TEXT PRIMARY KEY,
    founder_json TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    times_seen INTEGER NOT NULL DEFAULT 1
);
"""


def init_db() -> None:
    with _lock, _connect() as conn:
        if _IS_PG:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA_PG)
            conn.commit()
        else:
            conn.executescript(_SCHEMA_SQLITE)


def _ph(n: int) -> str:
    """Placeholders de parámetro: %s (Postgres) vs ? (SQLite)."""
    mark = "%s" if _IS_PG else "?"
    return ", ".join([mark] * n)


def _json_dump(value):
    # psycopg necesita el wrapper Jsonb para adaptar un dict/list de Python
    # a una columna JSONB; en SQLite se guarda como TEXT plano.
    if _IS_PG:
        from psycopg.types.json import Jsonb

        return Jsonb(value)
    return json.dumps(value)


def _json_load(value):
    if isinstance(value, str):
        return json.loads(value)
    return value  # psycopg ya lo devuelve deserializado (JSONB)


# ---------------------------------------------------------------------------
# Scans
# ---------------------------------------------------------------------------

def founder_key(company: str, name: str) -> str:
    return f"{company.strip().lower()}|{name.strip().lower()}"


def save_scan(result: PipelineResult) -> int:
    with _lock, _connect() as conn:
        query = f"INSERT INTO scans (created_at, query, provider_used, cost_usd, result_json) VALUES ({_ph(5)})"
        params = (_now(), result.query, result.provider_used, result.cost_usd, _json_dump(result.to_dict()))
        if _IS_PG:
            with conn.cursor() as cur:
                cur.execute(query + " RETURNING id", params)
                new_id = cur.fetchone()["id"]
            conn.commit()
            return int(new_id)
        else:
            cur = conn.execute(query, params)
            return int(cur.lastrowid)


def get_latest_scan() -> dict | None:
    with _lock, _connect() as conn:
        query = "SELECT result_json FROM scans ORDER BY id DESC LIMIT 1"
        if _IS_PG:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                return _json_load(row["result_json"]) if row else None
        else:
            row = conn.execute(query).fetchone()
            return _json_load(row["result_json"]) if row else None


# ---------------------------------------------------------------------------
# Decisiones manuales (aprobar / descartar)
# ---------------------------------------------------------------------------

def set_decision(company: str, name: str, state: str) -> None:
    """``state`` es 'forced', 'discarded', o 'clear' para borrar la anulación."""
    key = founder_key(company, name)
    with _lock, _connect() as conn:
        if state == "clear":
            _exec(conn, f"DELETE FROM decisions WHERE founder_key = {_ph(1)}", (key,))
        else:
            if _IS_PG:
                _exec(
                    conn,
                    "INSERT INTO decisions (founder_key, state, updated_at) VALUES (%s, %s, %s) "
                    "ON CONFLICT (founder_key) DO UPDATE SET state = EXCLUDED.state, updated_at = EXCLUDED.updated_at",
                    (key, state, _now()),
                )
            else:
                _exec(
                    conn,
                    "INSERT INTO decisions (founder_key, state, updated_at) VALUES (?, ?, ?) "
                    "ON CONFLICT(founder_key) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
                    (key, state, _now()),
                )
        conn.commit()


def get_decisions() -> dict[str, str]:
    with _lock, _connect() as conn:
        rows = _fetchall(conn, "SELECT founder_key, state FROM decisions")
        return {row["founder_key"]: row["state"] for row in rows}


# ---------------------------------------------------------------------------
# Usuarios de Google
# ---------------------------------------------------------------------------

def upsert_google_user(google_sub: str, email: str, name: str, picture: str) -> None:
    now = _now()
    with _lock, _connect() as conn:
        if _IS_PG:
            _exec(
                conn,
                "INSERT INTO users (google_sub, email, name, picture, created_at, last_login_at) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (google_sub) DO UPDATE SET email = EXCLUDED.email, name = EXCLUDED.name, "
                "picture = EXCLUDED.picture, last_login_at = EXCLUDED.last_login_at",
                (google_sub, email, name, picture, now, now),
            )
        else:
            _exec(
                conn,
                "INSERT INTO users (google_sub, email, name, picture, created_at, last_login_at) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(google_sub) DO UPDATE SET email = excluded.email, name = excluded.name, "
                "picture = excluded.picture, last_login_at = excluded.last_login_at",
                (google_sub, email, name, picture, now, now),
            )
        conn.commit()


# ---------------------------------------------------------------------------
# Companies: deduplicación entre corridas
# ---------------------------------------------------------------------------

def company_key(company: str, country_code: str = "") -> str:
    return f"{company.strip().lower()}|{(country_code or '').strip().lower()}"


def _merge_lists(old: list, new: list, item_key=lambda x: x) -> list:
    """Une dos listas sin duplicar (por clave), preservando orden: lo viejo
    primero, luego lo nuevo que no estuviera ya."""
    seen = {item_key(x) for x in old if x is not None}
    merged = list(old)
    for item in new:
        k = item_key(item)
        if k not in seen:
            merged.append(item)
            seen.add(k)
    return merged


def _merge_founder(old: dict, new: dict) -> dict:
    """Fusiona dos FounderProfile (dicts) de la misma empresa: rellena
    campos vacíos con la info nueva que antes no se había contemplado, une
    listas (equipo, evidencia, señales, clientes, rondas, redes) sin
    duplicar, y se queda con el score más alto entre las dos corridas."""
    merged = dict(old)
    for key, new_value in new.items():
        old_value = old.get(key)
        if key in ("team", "evidence", "signals", "skills", "clients", "impact_metrics", "feedback"):
            merged[key] = _merge_lists(old_value or [], new_value or [])
        elif key == "social_links":
            merged[key] = _merge_lists(old_value or [], new_value or [], item_key=lambda x: x.get("url"))
        elif key == "funding_rounds":
            merged[key] = _merge_lists(
                old_value or [], new_value or [], item_key=lambda x: (x.get("investor"), x.get("round_name"))
            )
        elif key == "criteria":
            by_name = {c["name"]: c for c in (old_value or [])}
            for c in new_value or []:
                existing = by_name.get(c["name"])
                if not existing or c.get("score", 0) > existing.get("score", 0):
                    by_name[c["name"]] = c
            merged[key] = list(by_name.values())
        elif key == "requirements":
            by_name = {r["name"]: r for r in (old_value or [])}
            for r in new_value or []:
                existing = by_name.get(r["name"])
                if not existing or (r.get("met") and not existing.get("met")):
                    by_name[r["name"]] = r
            merged[key] = list(by_name.values())
        elif key == "founder_score":
            merged[key] = max(old_value or 0, new_value or 0)
        elif not old_value and new_value:
            # Campo vacío en lo que ya teníamos, con dato nuevo → se agrega.
            merged[key] = new_value
        # si old_value ya tenía algo, se preserva (no se pisa con vacío/menos evidencia)
    return merged


def merge_company(founder: dict) -> tuple[dict, bool]:
    """Registra/fusiona una startup contra lo ya monitoreado.

    Devuelve (founder_fusionado, is_new). Si ya existía, el resultado trae
    los campos que antes faltaban rellenados con la corrida nueva, y las
    listas (equipo, evidencia, etc.) unidas sin duplicar — la startup no se
    "vuelve a descubrir" desde cero en cada corrida."""
    key = company_key(founder.get("company", ""), founder.get("country_code", ""))
    if not key.strip("|"):
        return founder, True

    now = _now()
    with _lock, _connect() as conn:
        row = _fetchone(conn, f"SELECT founder_json, times_seen FROM companies WHERE company_key = {_ph(1)}", (key,))
        if row is None:
            _exec(
                conn,
                f"INSERT INTO companies (company_key, founder_json, first_seen, last_seen, times_seen) "
                f"VALUES ({_ph(5)})",
                (key, _json_dump(founder), now, now, 1),
            )
            conn.commit()
            return founder, True

        existing = _json_load(row["founder_json"])
        merged = _merge_founder(existing, founder)
        times_seen = int(row["times_seen"]) + 1
        if _IS_PG:
            _exec(
                conn,
                "UPDATE companies SET founder_json = %s, last_seen = %s, times_seen = %s WHERE company_key = %s",
                (_json_dump(merged), now, times_seen, key),
            )
        else:
            _exec(
                conn,
                "UPDATE companies SET founder_json = ?, last_seen = ?, times_seen = ? WHERE company_key = ?",
                (_json_dump(merged), now, times_seen, key),
            )
        conn.commit()
        return merged, False


def get_known_company_keys() -> set[str]:
    """Claves (empresa+país) ya vistas en corridas anteriores."""
    with _lock, _connect() as conn:
        rows = _fetchall(conn, "SELECT company_key FROM companies")
        return {row["company_key"] for row in rows}


# ---------------------------------------------------------------------------
# Helpers de bajo nivel (compatibilidad psycopg / sqlite3)
# ---------------------------------------------------------------------------

def _exec(conn, query: str, params: tuple = ()) -> None:
    if _IS_PG:
        with conn.cursor() as cur:
            cur.execute(query, params)
    else:
        conn.execute(query, params)


def _fetchone(conn, query: str, params: tuple = ()):
    if _IS_PG:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
    else:
        return conn.execute(query, params).fetchone()


def _fetchall(conn, query: str, params: tuple = ()):
    if _IS_PG:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    else:
        return conn.execute(query, params).fetchall()
