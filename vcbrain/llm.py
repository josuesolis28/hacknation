"""Capa cognitiva: OpenAI (GPT-4o).

Interfaz única `complete()` con registro de proveedores desacoplado: si en
el futuro se agrega otro proveedor, basta registrarlo en _PROVIDERS y el
resto del sistema no cambia.
"""

import logging

from .config import settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Todos los proveedores fallaron."""


def _complete_openai(system: str, user: str, max_tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


_PROVIDERS = {
    "openai": _complete_openai,
}


def _provider_order() -> list[str]:
    """Primario según .env; los demás quedan como fallback. Solo se
    incluyen proveedores con API key configurada."""
    primary = settings.llm_provider if settings.llm_provider in _PROVIDERS else "openai"
    order = [primary] + [p for p in _PROVIDERS if p != primary]
    available = {
        "openai": bool(settings.openai_api_key),
    }
    return [p for p in order if available[p]]


def complete(system: str, user: str, max_tokens: int = 8000) -> tuple[str, str]:
    """Devuelve (texto, proveedor_usado). Lanza LLMError si todos fallan."""
    errors: list[str] = []
    for provider in _provider_order():
        try:
            text = _PROVIDERS[provider](system, user, max_tokens)
            if text.strip():
                return text, provider
            errors.append(f"{provider}: respuesta vacía")
        except Exception as exc:  # conmutación: cualquier fallo pasa al siguiente
            logger.warning("Proveedor %s falló: %s", provider, exc)
            errors.append(f"{provider}: {exc}")

    raise LLMError("Todos los proveedores LLM fallaron: " + " | ".join(errors))
