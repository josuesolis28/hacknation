"""Capa de decisión: valida requisitos + score ponderado y ejecuta la salida.

- APROBADO  → se genera automáticamente un cheque de $100,000 USD del fondo.
- RECHAZADO → se conserva el feedback automático (qué falta y qué mejorar).
"""

import secrets
from datetime import date

from .judge import APPROVAL_THRESHOLD
from .models import Check, FounderProfile

FUND_NAME = "Maschmeyer Group Ventures"
CHECK_AMOUNT_USD = 100_000


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


def decide(founder: FounderProfile) -> FounderProfile:
    """Aplica la regla de aprobación instantánea sobre un perfil evaluado."""
    all_gates_met = all(r.met for r in founder.requirements) and founder.requirements
    score_ok = founder.founder_score >= APPROVAL_THRESHOLD

    if all_gates_met and score_ok:
        founder.decision = "approved"
        founder.check = _new_check(founder)
        founder.feedback = []  # aprobado: no aplica feedback de rechazo
    else:
        founder.decision = "rejected"
        founder.check = None
        # Garantiza que el feedback siempre explique el porqué
        reasons = []
        if not score_ok:
            reasons.append(
                f"El score ponderado ({founder.founder_score}/100) está por "
                f"debajo del umbral de aprobación del fondo ({APPROVAL_THRESHOLD})."
            )
        for req in founder.requirements:
            if not req.met:
                reasons.append(f"Requisito no cumplido: {req.name} — {req.detail}")
        founder.feedback = reasons + founder.feedback

    return founder
