"""Configuración central: todo se lee desde .env, nada hardcodeado."""

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_ROOT = Path(__file__).resolve().parent.parent
_JWT_SECRET_FILE = _ROOT / ".vcbrain_jwt_secret"


def _stable_jwt_secret() -> str:
    """Evita invalidar sesiones en cada reload de uvicorn.

    Si falta ``VCBRAIN_JWT_SECRET``, se reutiliza un secreto local persistente
    (archivo gitignored). Antes se regeneraba en cada arranque y el frontend
    recibía «Token inválido o expirado» con un JWT aún vigente en el navegador.
    """
    env = os.getenv("VCBRAIN_JWT_SECRET", "").strip()
    if env and env not in {"replace-with-a-long-random-secret", "changeme"}:
        return env
    try:
        if _JWT_SECRET_FILE.exists():
            stored = _JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
            if stored:
                return stored
        secret = secrets.token_urlsafe(48)
        _JWT_SECRET_FILE.write_text(secret, encoding="utf-8")
        return secret
    except OSError:
        return secrets.token_urlsafe(48)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai").lower())
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    # Modelo usado para el Scout (búsqueda web vía la tool "web_search" de OpenAI).
    openai_search_model: str = field(default_factory=lambda: os.getenv("OPENAI_SEARCH_MODEL", "gpt-4o"))
    # Modelo barato para traducción (no necesita razonamiento, solo idioma).
    openai_translate_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_TRANSLATE_MODEL", "gpt-5.4-mini")
    )

    search_max_results: int = field(default_factory=lambda: int(os.getenv("SEARCH_MAX_RESULTS", "8")))
    # Cuántas queries de búsqueda se disparan en paralelo hacia OpenAI.
    search_concurrency: int = field(default_factory=lambda: int(os.getenv("SEARCH_CONCURRENCY", "8")))
    # Tope de costo estimado (USD) por corrida de búsqueda (Scout + Judge).
    # Al acercarse al límite se dejan de lanzar nuevas queries de búsqueda.
    max_search_cost_usd: float = field(default_factory=lambda: float(os.getenv("MAX_SEARCH_COST_USD", "2.0")))

    # Secreto de licencia: sin el valor correcto, el backend no arranca.
    # Ver vcbrain/license_gate.py — el hash esperado vive en el código, el
    # valor en texto plano solo lo tiene el autor.
    license_key: str = field(default_factory=lambda: os.getenv("LICENSE_KEY", ""))

    # Postgres (Railway u otro host) para producción. Si se deja vacío, la
    # app cae de vuelta a un archivo SQLite local (útil en desarrollo sin
    # tener que levantar Postgres).
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    # Orígenes permitidos por CORS, separados por coma. Agrega aquí tu URL
    # de Vercel en producción (p. ej. https://tu-app.vercel.app).
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
            ).split(",")
            if o.strip()
        )
    )
    # Client ID de OAuth de Google (público, no es secreto) para "Sign in with Google".
    # Se crea en https://console.cloud.google.com/apis/credentials — tipo "Web application".
    google_client_id: str = field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID", ""))

    admin_username: str = field(default_factory=lambda: os.getenv("VCBRAIN_ADMIN_USERNAME", "admin12345"))
    admin_password: str = field(default_factory=lambda: os.getenv("VCBRAIN_ADMIN_PASSWORD", "admin12345"))
    # Cuenta de prueba fija para el lado startup (para demos/QA, igual que el
    # admin de arriba pero con rol "startup"). Cambiar antes de producción.
    startup_test_username: str = field(default_factory=lambda: os.getenv("VCBRAIN_STARTUP_USERNAME", "startup1"))
    startup_test_password: str = field(default_factory=lambda: os.getenv("VCBRAIN_STARTUP_PASSWORD", "startup1"))
    jwt_secret: str = field(default_factory=_stable_jwt_secret)
    # MVP: 8h para no cortar sesiones de demo; override con VCBRAIN_JWT_TTL_SECONDS
    jwt_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("VCBRAIN_JWT_TTL_SECONDS", "28800")))
    default_language: str = field(default_factory=lambda: os.getenv("VCBRAIN_DEFAULT_LANGUAGE", "en").lower())

    def validate(self) -> list[str]:
        """Devuelve la lista de variables faltantes (vacía si todo está OK)."""
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        return missing


settings = Settings()
