"""Capa de decisión: semáforo + aprobación instantánea.

Semáforo (traffic_light):
- green  → candidato: gates críticos cumplidos y score ≥ umbral
- yellow → potencial: DACH ok y score/gates parciales
- red    → no cumple de plano (fuera de tesis o score/gates muy bajos)

- APROBADO  → cheque $100k (solo green + decision rules)
- RECHAZADO → feedback de qué falta
"""

import secrets
from datetime import date

from .judge import APPROVAL_THRESHOLD
from .models import Check, FounderProfile

FUND_NAME = "Maschmeyer Group Ventures"
CHECK_AMOUNT_USD = 100_000

# Umbrales del semáforo (estándar MVP)
GREEN_SCORE = APPROVAL_THRESHOLD  # 70
YELLOW_SCORE = 45


def _new_check(founder: FounderProfile) -> Check:
    return Check(
        check_id=f"MGV-{date.today().year}-{secrets.token_hex(3).upper()}",
        amount_usd=CHECK_AMOUNT_USD,
        issued_to=founder.name,
        company=founder.company,
        issued_by=FUND_NAME,
        date=date.today().isoformat(),
        status="issued",
    )


def _is_dach(founder: FounderProfile) -> bool:
    return founder.country_code in {"DE", "CH", "AT"} or founder.country in {
        "Germany",
        "Switzerland",
        "Austria",
    }


def assign_traffic_light(founder: FounderProfile) -> str:
    """Asigna semáforo según el score ponderado.

    Regla del fondo: cualquier startup DACH con score >= 70 califica, sin
    excepción — los gates (requirements) son diligencia informativa para la
    ficha interna, pero ya no bloquean la aprobación (antes exigían also
    "todos los gates cumplidos", lo que rechazaba startups de 70+ puntos por
    un solo requisito no confirmado, contradiciendo la regla real del fondo).
    """
    if not _is_dach(founder):
        return "red"

    score = founder.founder_score
    if score >= GREEN_SCORE:
        return "green"
    if score >= YELLOW_SCORE:
        return "yellow"
    return "red"


def decide(founder: FounderProfile) -> FounderProfile:
    """Aplica semáforo y regla de aprobación instantánea: DACH + score >= 70."""
    founder.traffic_light = assign_traffic_light(founder)
    score_ok = founder.founder_score >= APPROVAL_THRESHOLD

    if founder.traffic_light == "green" and score_ok:
        founder.decision = "approved"
        founder.check = _new_check(founder)
        founder.feedback = []
    else:
        founder.decision = "rejected"
        founder.check = None
        reasons = []
        if founder.traffic_light == "red":
            reasons.append(
                "Semáforo rojo: no cumple los criterios base (DACH / score)."
            )
        elif founder.traffic_light == "yellow":
            reasons.append(
                "Semáforo amarillo: hay potencial, pero aún no califica como candidato."
            )
        if not score_ok:
            reasons.append(
                f"El score ponderado ({founder.founder_score}/100) está por "
                f"debajo del umbral ({APPROVAL_THRESHOLD})."
            )
        for req in founder.requirements:
            if not req.met:
                reasons.append(f"Requisito no cumplido: {req.name} — {req.detail}")
        founder.feedback = reasons + founder.feedback

    return founder
