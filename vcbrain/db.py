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

import hashlib
import json
import os
import secrets
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
CREATE TABLE IF NOT EXISTS tickets (
    founder_key TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_notes (
    founder_key TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    language TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    submitter TEXT NOT NULL,
    company TEXT NOT NULL,
    name TEXT NOT NULL,
    company_key TEXT NOT NULL,
    founder_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS submission_files (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    data BYTEA,
    url TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS invite_codes (
    code TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    used_by TEXT,
    used_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS accounts (
    email TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    invite_code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
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
CREATE TABLE IF NOT EXISTS tickets (
    founder_key TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_notes (
    founder_key TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    language TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submitter TEXT NOT NULL,
    company TEXT NOT NULL,
    name TEXT NOT NULL,
    company_key TEXT NOT NULL,
    founder_key TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submission_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    data BLOB,
    url TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invite_codes (
    code TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    used_by TEXT,
    used_at TEXT
);
CREATE TABLE IF NOT EXISTS accounts (
    email TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    invite_code TEXT NOT NULL,
    created_at TEXT NOT NULL
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
# Tickets: tablero de aprobados / rechazados (binario, sin estados intermedios)
# ---------------------------------------------------------------------------
# El checkbox "revisar" de cada tarjeta pasa el lead de "sin ticket" a:
#   approved  → se generó/emitió el cheque
#   rejected  → se rechaza y se genera automáticamente una nota de feedback
#               personalizada (ver ticket_notes / generate_rejection_note)

def set_ticket_status(company: str, name: str, status: str) -> None:
    """``status`` es 'approved' | 'rejected' | 'clear'. Al limpiar (clear)
    también se borra cualquier nota de rechazo asociada."""
    key = founder_key(company, name)
    with _lock, _connect() as conn:
        if status == "clear":
            _exec(conn, f"DELETE FROM tickets WHERE founder_key = {_ph(1)}", (key,))
            _exec(conn, f"DELETE FROM ticket_notes WHERE founder_key = {_ph(1)}", (key,))
        elif _IS_PG:
            _exec(
                conn,
                "INSERT INTO tickets (founder_key, status, updated_at) VALUES (%s, %s, %s) "
                "ON CONFLICT (founder_key) DO UPDATE SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at",
                (key, status, _now()),
            )
        else:
            _exec(
                conn,
                "INSERT INTO tickets (founder_key, status, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(founder_key) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at",
                (key, status, _now()),
            )
        conn.commit()


def get_tickets() -> dict[str, str]:
    with _lock, _connect() as conn:
        rows = _fetchall(conn, "SELECT founder_key, status FROM tickets")
        return {row["founder_key"]: row["status"] for row in rows}


def save_ticket_note(company: str, name: str, note: str, language: str) -> None:
    key = founder_key(company, name)
    with _lock, _connect() as conn:
        if _IS_PG:
            _exec(
                conn,
                "INSERT INTO ticket_notes (founder_key, note, language, created_at) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (founder_key) DO UPDATE SET note = EXCLUDED.note, language = EXCLUDED.language, "
                "created_at = EXCLUDED.created_at",
                (key, note, language, _now()),
            )
        else:
            _exec(
                conn,
                "INSERT INTO ticket_notes (founder_key, note, language, created_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(founder_key) DO UPDATE SET note = excluded.note, language = excluded.language, "
                "created_at = excluded.created_at",
                (key, note, language, _now()),
            )
        conn.commit()


def get_ticket_notes() -> dict[str, dict]:
    with _lock, _connect() as conn:
        rows = _fetchall(conn, "SELECT founder_key, note, language FROM ticket_notes")
        return {row["founder_key"]: {"note": row["note"], "language": row["language"]} for row in rows}


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
# Códigos de invitación y cuentas B2B (email + contraseña)
# ---------------------------------------------------------------------------
# En vez de depender de "Sign in with Google" (poco natural para B2B), el
# acceso se controla con códigos de un solo uso que genera quien ya está
# adentro (el fondo) y comparte manualmente (WhatsApp, email, etc.) con la
# startup/inversionista que quiere invitar. El código fija el rol de la
# cuenta que se registre con él.

_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O/1/I para evitar confusión al copiarlo a mano


def _generate_code(length: int = 8) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def create_invite_code(role: str, note: str, created_by: str) -> str:
    code = _generate_code()
    with _lock, _connect() as conn:
        _exec(
            conn,
            f"INSERT INTO invite_codes (code, role, note, created_by, created_at) VALUES ({_ph(5)})",
            (code, role, note, created_by, _now()),
        )
        conn.commit()
    return code


def list_invite_codes() -> list[dict]:
    with _lock, _connect() as conn:
        rows = _fetchall(
            conn,
            "SELECT code, role, note, created_by, created_at, used_by, used_at "
            "FROM invite_codes ORDER BY created_at DESC",
        )
        return [dict(row) for row in rows]


def get_invite_code(code: str) -> dict | None:
    with _lock, _connect() as conn:
        row = _fetchone(
            conn,
            f"SELECT code, role, note, used_by FROM invite_codes WHERE code = {_ph(1)}",
            (code,),
        )
        return dict(row) if row else None


def mark_invite_used(code: str, used_by: str) -> None:
    mark = "%s" if _IS_PG else "?"
    with _lock, _connect() as conn:
        _exec(
            conn,
            f"UPDATE invite_codes SET used_by = {mark}, used_at = {mark} WHERE code = {mark}",
            (used_by, _now(), code),
        )
        conn.commit()


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000).hex()


def create_account(email: str, password: str, role: str, name: str, invite_code: str) -> None:
    salt = os.urandom(16)
    password_hash = _hash_password(password, salt)
    with _lock, _connect() as conn:
        _exec(
            conn,
            f"INSERT INTO accounts (email, password_hash, salt, role, name, invite_code, created_at) "
            f"VALUES ({_ph(7)})",
            (email.lower(), password_hash, salt.hex(), role, name, invite_code, _now()),
        )
        conn.commit()


def get_account(email: str) -> dict | None:
    with _lock, _connect() as conn:
        row = _fetchone(
            conn,
            f"SELECT email, password_hash, salt, role, name FROM accounts WHERE email = {_ph(1)}",
            (email.lower(),),
        )
        return dict(row) if row else None


def verify_account_password(email: str, password: str) -> dict | None:
    """Devuelve {email, role, name} si la contraseña es correcta, si no None."""
    account = get_account(email)
    if account is None:
        return None
    expected = _hash_password(password, bytes.fromhex(account["salt"]))
    if not secrets.compare_digest(expected, account["password_hash"]):
        return None
    return {"email": account["email"], "role": account["role"], "name": account["name"]}


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
        if key in ("evidence", "signals", "skills", "clients", "impact_metrics", "feedback"):
            merged[key] = _merge_lists(old_value or [], new_value or [])
        elif key == "team":
            # Objetos (dict), no strings — hay que indexar por nombre en vez
            # de usar el valor completo como clave (los dicts no son hashables).
            merged[key] = _merge_lists(old_value or [], new_value or [], item_key=lambda x: x.get("name"))
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


def list_companies() -> list[dict]:
    """Todas las startups vistas alguna vez (para la sección "ya
    analizadas"), más recientes primero."""
    with _lock, _connect() as conn:
        rows = _fetchall(
            conn,
            "SELECT founder_json, first_seen, last_seen, times_seen FROM companies ORDER BY last_seen DESC",
        )
        return [
            {
                "founder": _json_load(row["founder_json"]),
                "first_seen": row["first_seen"],
                "last_seen": row["last_seen"],
                "times_seen": row["times_seen"],
            }
            for row in rows
        ]


def get_company_by_key(key: str) -> dict | None:
    with _lock, _connect() as conn:
        row = _fetchone(conn, f"SELECT founder_json FROM companies WHERE company_key = {_ph(1)}", (key,))
        return _json_load(row["founder_json"]) if row else None


# ---------------------------------------------------------------------------
# Submissions: alta directa de startups por el propio founder (sin scraping)
# ---------------------------------------------------------------------------

def create_submission(submitter: str, company: str, name: str, country_code: str) -> int:
    with _lock, _connect() as conn:
        query = (
            f"INSERT INTO submissions (submitter, company, name, company_key, founder_key, created_at) "
            f"VALUES ({_ph(6)})"
        )
        params = (submitter, company, name, company_key(company, country_code), founder_key(company, name), _now())
        if _IS_PG:
            with conn.cursor() as cur:
                cur.execute(query + " RETURNING id", params)
                new_id = cur.fetchone()["id"]
            conn.commit()
            return int(new_id)
        else:
            cur = conn.execute(query, params)
            conn.commit()
            return int(cur.lastrowid)


def list_submissions(submitter: str | None = None) -> list[dict]:
    with _lock, _connect() as conn:
        if submitter is not None:
            rows = _fetchall(
                conn,
                f"SELECT id, submitter, company, name, company_key, founder_key, created_at "
                f"FROM submissions WHERE submitter = {_ph(1)} ORDER BY created_at DESC",
                (submitter,),
            )
        else:
            rows = _fetchall(
                conn,
                "SELECT id, submitter, company, name, company_key, founder_key, created_at "
                "FROM submissions ORDER BY created_at DESC",
            )
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Archivos adjuntos de una submission: PDF/imagen (bytes) o video (URL)
# ---------------------------------------------------------------------------

def save_submission_file(
    submission_id: int, kind: str, filename: str, content_type: str, data: bytes | None = None, url: str | None = None
) -> int:
    with _lock, _connect() as conn:
        query = (
            f"INSERT INTO submission_files (submission_id, kind, filename, content_type, data, url, created_at) "
            f"VALUES ({_ph(7)})"
        )
        params = (submission_id, kind, filename, content_type, data, url, _now())
        if _IS_PG:
            with conn.cursor() as cur:
                cur.execute(query + " RETURNING id", params)
                new_id = cur.fetchone()["id"]
            conn.commit()
            return int(new_id)
        else:
            cur = conn.execute(query, params)
            conn.commit()
            return int(cur.lastrowid)


def list_submission_files(submission_id: int) -> list[dict]:
    """Metadata únicamente (sin el blob) — para listar adjuntos sin traer
    megabytes de datos en cada respuesta."""
    with _lock, _connect() as conn:
        rows = _fetchall(
            conn,
            f"SELECT id, kind, filename, content_type, url FROM submission_files "
            f"WHERE submission_id = {_ph(1)} ORDER BY id",
            (submission_id,),
        )
        return [dict(row) for row in rows]


def get_submission_file(file_id: int) -> dict | None:
    """Trae el archivo completo (con el blob) para servirlo/descargarlo."""
    with _lock, _connect() as conn:
        row = _fetchone(
            conn,
            f"SELECT filename, content_type, data, url FROM submission_files WHERE id = {_ph(1)}",
            (file_id,),
        )
        return dict(row) if row else None


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
