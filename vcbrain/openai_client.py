"""Cliente OpenAI compartido + diagnóstico de conectividad de red.

Causa raíz real del "Connection error" en Railway (encontrada con
diagnose_openai_live_call): OPENAI_API_KEY tenía un salto de línea (\n)
pegado al final en las variables de entorno de Railway. httpx rechaza
construir el header "Authorization: Bearer ...\n" (LocalProtocolError:
Illegal header value), y openai-python disfraza CUALQUIER excepción de
httpx como un genérico "Connection error." — de ahí que pareciera un
problema de red/DNS/IPv6 cuando en realidad era la propia API key. El fix
real es el .strip() sobre OPENAI_API_KEY en config.py; esto no era ni
IPv4/IPv6 ni timeout (ambas cosas se probaron y no lo eran).
"""

import socket
import time

import httpx
from openai import OpenAI

from .config import settings


def _full_error(exc: BaseException) -> str:
    """openai-python envuelve CUALQUIER excepción de httpx en un genérico
    APIConnectionError("Connection error.") — sin esto no se ve la causa
    real (ConnectError, ReadTimeout, SSLError, LocalProtocolError, etc).
    Camina la cadena __cause__/__context__ para exponerla."""
    parts = []
    seen = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        parts.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or current.__context__
    return " <- ".join(parts)


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def diagnose_openai_connectivity() -> dict:
    """Prueba DNS y HTTPS reales hacia api.openai.com desde este proceso,
    SIN gastar en una llamada real de la API (solo un GET a la raíz, que
    responde 404 pero confirma que la conexión/TLS funcionan). Sirve para
    aislar en qué capa exacta falla la conectividad en Railway (DNS vs TCP
    vs TLS) sin tener que correr un Scout completo cada vez."""
    result: dict = {}

    try:
        t0 = time.monotonic()
        infos = socket.getaddrinfo("api.openai.com", 443, proto=socket.IPPROTO_TCP)
        result["dns_ok"] = True
        result["dns_ms"] = round((time.monotonic() - t0) * 1000, 1)
        result["resolved_ips"] = sorted({info[4][0] for info in infos})
    except Exception as exc:
        result["dns_ok"] = False
        result["dns_error"] = _full_error(exc)

    try:
        t0 = time.monotonic()
        with httpx.Client(timeout=8.0, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as c:
            r = c.get("https://api.openai.com/")
        result["https_ipv4_ok"] = True
        result["https_ipv4_status"] = r.status_code
        result["https_ipv4_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["https_ipv4_ok"] = False
        result["https_ipv4_error"] = _full_error(exc)

    try:
        t0 = time.monotonic()
        with httpx.Client(timeout=8.0) as c:
            r = c.get("https://api.openai.com/")
        result["https_default_ok"] = True
        result["https_default_status"] = r.status_code
        result["https_default_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["https_default_ok"] = False
        result["https_default_error"] = _full_error(exc)

    return result


def diagnose_openai_live_call() -> dict:
    """Prueba llamadas REALES y autenticadas contra OpenAI (gastan unos
    centavos de USD, por eso NO corren automáticamente al arrancar):

    0. Un POST crudo con httpx puro (SIN pasar por el SDK de OpenAI) —
       aísla si el problema es del SDK/su wrapper de errores o del
       transporte/red en sí para requests POST con body+auth.
    1. Un chat completion trivial y rápido vía el SDK.
    2. Una llamada real con el tool "web_search" (la misma que usa el
       Scout) — mucho más lenta porque el modelo navega la web antes de
       responder.

    Cada error se reporta con la cadena completa de causas (no solo el
    genérico "Connection error." que expone el SDK)."""
    result: dict = {}

    try:
        t0 = time.monotonic()
        with httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            transport=httpx.HTTPTransport(local_address="0.0.0.0"),
        ) as c:
            r = c.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
        result["raw_post_ok"] = True
        result["raw_post_status"] = r.status_code
        result["raw_post_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["raw_post_ok"] = False
        result["raw_post_error"] = _full_error(exc)

    client = get_openai_client()

    try:
        t0 = time.monotonic()
        client.chat.completions.create(
            model="gpt-4o-mini",
            max_completion_tokens=5,
            messages=[{"role": "user", "content": "hi"}],
        )
        result["chat_completion_ok"] = True
        result["chat_completion_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["chat_completion_ok"] = False
        result["chat_completion_error"] = _full_error(exc)

    try:
        t0 = time.monotonic()
        client.responses.create(
            model=settings.openai_search_model,
            tools=[{"type": "web_search"}],
            input="Busca 1 fuente pública reciente sobre 'OpenAI'. Responde en una frase.",
        )
        result["web_search_ok"] = True
        result["web_search_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["web_search_ok"] = False
        result["web_search_error"] = _full_error(exc)

    return result
