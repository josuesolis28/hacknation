"""Configuración central: todo se lee desde .env, nada hardcodeado."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))

    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai").lower())
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))

    tavily_max_results: int = field(default_factory=lambda: int(os.getenv("TAVILY_MAX_RESULTS", "8")))

    def validate(self) -> list[str]:
        """Devuelve la lista de variables faltantes (vacía si todo está OK)."""
        missing = []
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        return missing


settings = Settings()
