"""Orquestador: Scout → Judge/Score → Decide → (Connect bajo demanda)."""

import logging

from .config import settings
from .cost import CostTracker
from .decision import decide
from .judge import judge
from .models import PipelineResult
from .search import scout, scout_maschmeyer
from .thesis import maschmeyer_scope_label

logger = logging.getLogger(__name__)


def run_pipeline(query: str, max_results: int | None = None) -> PipelineResult:
    """Ejecuta el flujo completo para un sector/tecnología dado."""
    result = PipelineResult(query=query, provider_used="n/a")
    budget = CostTracker(limit_usd=settings.max_search_cost_usd)

    try:
        result.raw_hits = scout(query, max_results=max_results, budget=budget)
    except Exception as exc:
        result.errors.append(f"Scout (OpenAI) falló: {exc}")
        result.cost_usd = budget.total_usd
        return result

    if not result.raw_hits:
        result.errors.append("La búsqueda de OpenAI no devolvió resultados para esta búsqueda.")
        result.cost_usd = budget.total_usd
        return result

    try:
        founders, result.provider_used = judge(query, result.raw_hits, budget=budget)
        result.founders = [decide(f) for f in founders]
    except Exception as exc:
        result.errors.append(f"Judge (LLM) falló: {exc}")

    _report_budget(result, budget)
    return result


def run_maschmeyer_pipeline(max_results: int | None = None) -> PipelineResult:
    """Ejecuta el scouting completo sin que el usuario redacte una consulta."""
    query = maschmeyer_scope_label()
    result = PipelineResult(query=query, provider_used="n/a")
    budget = CostTracker(limit_usd=settings.max_search_cost_usd)

    try:
        result.raw_hits = scout_maschmeyer(max_results=max_results, budget=budget)
    except Exception as exc:
        result.errors.append(f"Scout (OpenAI) falló: {exc}")
        result.cost_usd = budget.total_usd
        return result

    if not result.raw_hits:
        result.errors.append("La búsqueda de OpenAI no devolvió resultados para la tesis de Maschmeyer Group.")
        result.cost_usd = budget.total_usd
        return result

    try:
        founders, result.provider_used = judge(query, result.raw_hits, budget=budget)
        result.founders = [decide(founder) for founder in founders]
    except Exception as exc:
        result.errors.append(f"Judge (LLM) falló: {exc}")

    _report_budget(result, budget)
    return result


def _report_budget(result: PipelineResult, budget: CostTracker) -> None:
    result.cost_usd = budget.total_usd
    logger.info("Costo estimado de la corrida: $%.4f (límite $%.2f)", budget.total_usd, budget.limit_usd)
    if budget.over_limit():
        result.errors.append(
            f"Se alcanzó el presupuesto de ${budget.limit_usd:.2f} en esta búsqueda "
            f"(~${budget.total_usd:.2f} usados) — la cobertura se acotó para no excederlo."
        )
