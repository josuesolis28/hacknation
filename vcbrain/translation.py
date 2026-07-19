"""Traducción LLM con caché de proceso para evitar llamadas repetidas.

Usa un modelo barato (`settings.openai_translate_model`, gpt-4o-mini por
default) porque traducir no requiere razonamiento — solo idioma.
"""

import json
from functools import lru_cache

from . import llm
from .config import settings

LANGUAGES = {"es": "Spanish", "en": "English", "de": "German"}


@lru_cache(maxsize=512)
def translate(text: str, language: str) -> str:
    if language not in LANGUAGES or not text.strip():
        return text
    raw, _ = llm.complete(
        "Translate faithfully. Return only the translated text; keep URLs, names and numbers unchanged.",
        f"Target language: {LANGUAGES[language]}\nText:\n{text}",
        max_tokens=1500,
        model=settings.openai_translate_model,
    )
    return raw.strip() or text


@lru_cache(maxsize=256)
def translate_many(texts: tuple[str, ...], language: str) -> tuple[str, ...]:
    """Traduce varios textos en una sola llamada (una tarjeta = una llamada,
    en vez de una llamada por campo). Devuelve la misma cantidad y orden que
    ``texts``; los strings vacíos se preservan tal cual."""
    if language not in LANGUAGES or not any(t.strip() for t in texts):
        return texts

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
