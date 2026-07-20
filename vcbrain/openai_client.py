"""Cliente OpenAI compartido + diagnóstico de conectividad de red.

En Railway, api.openai.com también resuelve por IPv6, y la salida IPv6 del
contenedor puede estar rota o inestable — resultando en que TODAS las
llamadas fallen con "Connection error" aunque en local funcione sin
problema. Se fuerza el socket local a bindear IPv4 para evitar esa ruta.
"""

import socket
import time

import httpx
from openai import OpenAI

from .config import settings

_http_client = httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key, http_client=_http_client)


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
        result["dns_error"] = f"{type(exc).__name__}: {exc}"

    try:
        t0 = time.monotonic()
        with httpx.Client(timeout=8.0, transport=httpx.HTTPTransport(local_address="0.0.0.0")) as c:
            r = c.get("https://api.openai.com/")
        result["https_ipv4_ok"] = True
        result["https_ipv4_status"] = r.status_code
        result["https_ipv4_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["https_ipv4_ok"] = False
        result["https_ipv4_error"] = f"{type(exc).__name__}: {exc}"

    try:
        t0 = time.monotonic()
        with httpx.Client(timeout=8.0) as c:
            r = c.get("https://api.openai.com/")
        result["https_default_ok"] = True
        result["https_default_status"] = r.status_code
        result["https_default_ms"] = round((time.monotonic() - t0) * 1000, 1)
    except Exception as exc:
        result["https_default_ok"] = False
        result["https_default_error"] = f"{type(exc).__name__}: {exc}"

    return result
