"""Orquestador: Scout → Judge/Score → (Connect bajo demanda)."""

import logging

from .judge import judge
from .models import PipelineResult
from .search import scout

logger = logging.getLogger(__name__)


def run_pipeline(query: str, max_results: int | None = None) -> PipelineResult:
    """Ejecuta el flujo completo para un sector/tecnología dado."""
    result = PipelineResult(query=query, provider_used="n/a")

    try:
        result.raw_hits = scout(query, max_results=max_results)
    except Exception as exc:
        result.errors.append(f"Scout (Tavily) falló: {exc}")
        return result

    if not result.raw_hits:
        result.errors.append("Tavily no devolvió resultados para esta búsqueda.")
        return result

    try:
        result.founders, result.provider_used = judge(query, result.raw_hits)
    except Exception as exc:
        result.errors.append(f"Judge (LLM) falló: {exc}")

    return result
