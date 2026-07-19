"""Orquestador: Scout → Judge/Score → Decide → (Connect bajo demanda)."""

import logging

from .decision import decide
from .judge import judge
from .models import PipelineResult
from .search import scout, scout_maschmeyer
from .thesis import maschmeyer_scope_label

logger = logging.getLogger(__name__)


def run_pipeline(query: str, max_results: int | None = None) -> PipelineResult:
    """Ejecuta el flujo completo para un sector/tecnología dado."""
    result = PipelineResult(query=query, provider_used="n/a")

    try:
        result.raw_hits = scout(query, max_results=max_results)
    except Exception as exc:
        result.errors.append(f"Scout (OpenAI) falló: {exc}")
        return result

    if not result.raw_hits:
        result.errors.append("La búsqueda de OpenAI no devolvió resultados para esta búsqueda.")
        return result

    try:
        founders, result.provider_used = judge(query, result.raw_hits)
        result.founders = [decide(f) for f in founders]
    except Exception as exc:
        result.errors.append(f"Judge (LLM) falló: {exc}")

    return result


def run_maschmeyer_pipeline(max_results: int | None = None) -> PipelineResult:
    """Ejecuta el scouting completo sin que el usuario redacte una consulta."""
    query = maschmeyer_scope_label()
    result = PipelineResult(query=query, provider_used="n/a")

    try:
        result.raw_hits = scout_maschmeyer(max_results=max_results)
    except Exception as exc:
        result.errors.append(f"Scout (OpenAI) falló: {exc}")
        return result

    if not result.raw_hits:
        result.errors.append("La búsqueda de OpenAI no devolvió resultados para la tesis de Maschmeyer Group.")
        return result

    try:
        founders, result.provider_used = judge(query, result.raw_hits)
        result.founders = [decide(founder) for founder in founders]
    except Exception as exc:
        result.errors.append(f"Judge (LLM) falló: {exc}")

    return result
