"""Cliente OpenAI compartido: fuerza salida IPv4.

En Railway (y algunos otros hosts), api.openai.com también resuelve por
IPv6, y la salida IPv6 del contenedor puede estar rota o inestable —
resultando en que TODAS las llamadas fallen con "Connection error" aunque
en local (que sale por IPv4) funcione sin problema. Se fuerza el socket
local a bindear IPv4 para evitar esa ruta.
"""

import httpx
from openai import OpenAI

from .config import settings

_http_client = httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key, http_client=_http_client)
