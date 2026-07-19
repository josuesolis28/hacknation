"""Autenticación JWT local para la API B2B.

El proveedor de identidad podrá sustituir este módulo sin cambiar los
endpoints protegidos: todos dependen de ``current_user``.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer = HTTPBearer(auto_error=False)
_attempts: dict[str, deque[float]] = defaultdict(deque)
_WINDOW_SECONDS = 300
_MAX_ATTEMPTS = 5


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(username: str) -> str:
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": username, "iat": now, "exp": now + settings.jwt_ttl_seconds}, separators=(",", ":")).encode())
    signature = hmac.new(settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(signature)}"


def verify_credentials(username: str, password: str, client_id: str) -> bool:
    now = time.time()
    attempts = _attempts[client_id]
    while attempts and attempts[0] < now - _WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= _MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Inténtalo más tarde.")
    valid = secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(password, settings.admin_password)
    if not valid:
        attempts.append(now)
    else:
        attempts.clear()
    return valid


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido.")
    try:
        header, payload, signature = credentials.credentials.split(".")
        expected = hmac.new(settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        if not secrets.compare_digest(_b64(expected), signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido. Vuelve a iniciar sesión (el secreto JWT pudo cambiar tras reiniciar el servidor).",
            )
        claims = json.loads(_unb64(payload))
        if not isinstance(claims.get("sub"), str):
            raise ValueError("sub")
        if int(claims["exp"]) <= time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Vuelve a iniciar sesión.",
            )
        return claims["sub"]
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado.")


def request_client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def verify_google_id_token(credential: str) -> dict:
    """Verifica el ID token que devuelve el botón "Sign in with Google" del
    frontend (Google Identity Services). No hay client secret involucrado:
    el token ya viene firmado por Google, solo se valida la firma y la
    audiencia (nuestro Client ID) contra las claves públicas de Google."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="GOOGLE_CLIENT_ID no está configurado en el servidor.")
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    try:
        claims = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), audience=settings.google_client_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"Token de Google inválido: {exc}")

    if not claims.get("email_verified", False):
        raise HTTPException(status_code=401, detail="El correo de Google no está verificado.")
    return claims
