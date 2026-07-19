"""Traducción LLM con caché de proceso para evitar llamadas repetidas.

Usa un modelo barato (`settings.openai_translate_model`, gpt-5.4-mini por
default) porque traducir no requiere razonamiento — solo idioma.
"""

import json
import threading
from functools import lru_cache

from . import llm
from .config import settings

LANGUAGES = {"es": "Spanish", "en": "English", "de": "German"}

# lru_cache por sí solo no evita que dos requests idénticos y simultáneos
# (misma tarjeta, mismo idioma) ambos fallen el caché y paguen tokens dos
# veces — el segundo llega antes de que el primero termine de escribir el
# resultado. Un lock por clave serializa ese caso puntual sin bloquear
# traducciones de textos distintos entre sí.
_locks: dict[tuple, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(key: tuple) -> threading.Lock:
    with _locks_guard:
        lock = _locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _locks[key] = lock
        return lock


@lru_cache(maxsize=512)
def _translate_cached(text: str, language: str) -> str:
    raw, _ = llm.complete(
        "Translate faithfully. Return only the translated text; keep URLs, names and numbers unchanged.",
        f"Target language: {LANGUAGES[language]}\nText:\n{text}",
        max_tokens=1500,
        model=settings.openai_translate_model,
    )
    return raw.strip() or text


def translate(text: str, language: str) -> str:
    if language not in LANGUAGES or not text.strip():
        return text
    with _lock_for(("t", text, language)):
        return _translate_cached(text, language)


@lru_cache(maxsize=256)
def _translate_many_cached(texts: tuple[str, ...], language: str) -> tuple[str, ...]:
    payload = json.dumps(list(texts), ensure_ascii=False)
    raw, _ = llm.complete(
        "Translate each string in the JSON array faithfully to the target language. "
        "Respond ONLY with a JSON array of the same length and order, no markdown fences. "
        "Keep URLs, proper names, numbers and empty strings unchanged.",
        f"Target language: {LANGUAGES[language]}\nJSON array:\n{payload}",
        max_tokens=4000,
        model=settings.openai_translate_model,
    )
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        if isinstance(data, list) and len(data) == len(texts):
            return tuple(str(x) for x in data)
    except (json.JSONDecodeError, TypeError):
        pass
    return texts


def translate_many(texts: tuple[str, ...], language: str) -> tuple[str, ...]:
    """Traduce varios textos en una sola llamada (una tarjeta = una llamada,
    en vez de una llamada por campo). Devuelve la misma cantidad y orden que
    ``texts``; los strings vacíos se preservan tal cual."""
    if language not in LANGUAGES or not any(t.strip() for t in texts):
        return texts
    with _lock_for(("m", texts, language)):
        return _translate_many_cached(texts, language)
