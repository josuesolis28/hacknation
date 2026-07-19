"""Traducción LLM con caché de proceso para evitar llamadas repetidas."""

from functools import lru_cache

from . import llm

LANGUAGES = {"es": "Spanish", "en": "English", "de": "German"}


@lru_cache(maxsize=512)
def translate(text: str, language: str) -> str:
    if language not in LANGUAGES or not text.strip():
        return text
    raw, _ = llm.complete(
        "Translate faithfully. Return only the translated text; keep URLs, names and numbers unchanged.",
        f"Target language: {LANGUAGES[language]}\nText:\n{text}",
        max_tokens=1500,
    )
    return raw.strip() or text
