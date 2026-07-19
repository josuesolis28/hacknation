"""Orquestador: Scout → Judge/Score → Decide → Dedup/Merge → (Connect bajo demanda)."""

import logging

from . import db
from .config import settings
from .cost import CostTracker
from .decision import decide
from .judge import judge
from .models import FounderProfile, PipelineResult, founder_from_dict
from .search import scout, scout_maschmeyer
from .thesis import maschmeyer_scope_label

logger = logging.getLogger(__name__)


def _decide_and_merge(founders: list[FounderProfile]) -> list[FounderProfile]:
    """Aplica el semáforo/aprobación y fusiona cada startup contra lo que ya
    se había monitoreado en corridas anteriores (tabla ``companies``): si ya
    existía, no se duplica — se le agregan los campos/listas que esta
    corrida encontró y antes no se habían contemplado, y se vuelve a decidir
    con la evidencia combinada. Si es nueva, se registra tal cual."""
    merged: list[FounderProfile] = []
    new_count = 0
    for founder in founders:
        decided = decide(founder)
        try:
            merged_dict, is_new = db.merge_company(decided.to_dict())
            result_founder = decide(founder_from_dict(merged_dict))
            new_count += 1 if is_new else 0
        except Exception as exc:  # la persistencia no debe tumbar el pipeline
            logger.warning("No se pudo fusionar %s contra companies: %s", decided.company, exc)
            result_founder = decided
        merged.append(result_founder)
    if merged:
        logger.info("Dedup: %d nuevas, %d ya monitoreadas (fusionadas)", new_count, len(merged) - new_count)
    return merged


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
        result.founders = _decide_and_merge(founders)
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
        result.founders = _decide_and_merge(founders)
    except Exception as exc:
        result.errors.append(f"Judge (LLM) falló: {exc}")

    _report_budget(result, budget)
    return result


def refresh_decisions(result_dict: dict) -> dict:
    """Vuelve a aplicar la regla de decisión vigente a un resultado ya
    guardado (``scans``/``companies``). Necesario porque la regla de negocio
    puede cambiar (p. ej. "score >= 70 siempre califica") después de que una
    corrida ya se guardó — sin esto, un resultado cacheado seguiría
    mostrando la decisión calculada con la regla vieja hasta la próxima
    corrida nueva."""
    result_dict = dict(result_dict)
    result_dict["founders"] = [
        decide(founder_from_dict(f)).to_dict() for f in result_dict.get("founders", [])
    ]
    return result_dict


def _report_budget(result: PipelineResult, budget: CostTracker) -> None:
    result.cost_usd = budget.total_usd
    logger.info("Costo estimado de la corrida: $%.4f (límite $%.2f)", budget.total_usd, budget.limit_usd)
    if budget.over_limit():
        result.errors.append(
            f"Se alcanzó el presupuesto de ${budget.limit_usd:.2f} en esta búsqueda "
            f"(~${budget.total_usd:.2f} usados) — la cobertura se acotó para no excederlo."
        )
