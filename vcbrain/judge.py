"""Capa Judge + Score: evalúa la evidencia contra la rúbrica pre-seed del
fondo Maschmeyer Group y produce criterios ponderados + requisitos + feedback.

Rúbrica basada en criterios estándar de due diligence pre-seed (equipo /
founder-market fit, producto, validación del problema, mercado, moat).
"""

import json
import re

from . import llm
from .models import CriterionScore, FounderProfile, Requirement, SearchHit

# Pesos de la rúbrica pre-seed (suman 100). El score final se calcula en
# Python como suma ponderada — no se le pide al LLM que haga la aritmética.
RUBRIC = [
    ("team", "Equipo y founder-market fit", 30),
    ("product", "Producto y capacidad técnica demostrada (MVP/código)", 25),
    ("validation", "Validación del problema y tracción temprana", 20),
    ("market", "Tamaño de mercado y timing (TAM ≥ $1B)", 15),
    ("moat", "Diferenciación / moat defendible", 10),
]

# Requisitos duros (gates) de elegibilidad al fondo
GATES = [
    (
        "thesis_fit",
        "Encaja con la tesis: B2B SaaS, FinTech, InsurTech, HealthTech, RegTech, ciberseguridad o New Work",
    ),
    (
        "target_region",
        "Opera en Estados Unidos, Europa o Latinoamérica con evidencia verificable",
    ),
    ("technical_founder", "Fundador técnico identificable con evidencia real"),
    ("early_stage", "Etapa pre-seed/seed temprana (no Serie A+ levantada)"),
    ("product_built", "Producto tangible: MVP, demo, repo o prototipo funcional"),
    ("problem_validated", "Problema validado: usuarios, clientes o señal de demanda"),
]

APPROVAL_THRESHOLD = 70  # score ponderado mínimo, además de cumplir todos los gates

_CRITERIA_JSON = ",\n        ".join(
    f'"{key}": {{"score": 0, "rationale": "string"}}' for key, _, _ in RUBRIC
)
_GATES_JSON = ",\n        ".join(
    f'"{key}": {{"met": true, "detail": "string"}}' for key, _ in GATES
)

SYSTEM_PROMPT = f"""\
Eres el motor de análisis de "The VC Brain", el sistema de aprobación \
instantánea del fondo venture capital pre-seed de Maschmeyer Group.

Tu trabajo: a partir de evidencia web real, identificar FUNDADORES y \
STARTUPS en etapa temprana que puedan ser incorporados al pipeline del \
fondo, y evaluarlos objetivamente contra la rúbrica de inversión.

Criterios (puntúa cada uno de 0 a 100, basándote SOLO en la evidencia):
- team (peso 30%): trayectoria de los fundadores, founder-market fit, \
equipo complementario (técnico + negocio). Equipos consolidados > solitarios.
- product (peso 25%): qué han construido — MVP, código público, demos, \
profundidad técnica, velocidad de shipping.
- validation (peso 20%): problema validado con clientes reales, tracción \
temprana, usuarios, ingresos o cartas de intención.
- market (peso 15%): tamaño de mercado (ideal TAM ≥ $1B), timing, relevancia.
- moat (peso 10%): diferenciación defendible — IP, datos propietarios, \
posicionamiento difícil de replicar.

Requisitos duros (gates) — evalúa cada uno como cumplido o no:
- thesis_fit: la empresa pertenece a B2B SaaS, FinTech, InsurTech, HealthTech,
  RegTech, ciberseguridad o New Work. No infieras el sector sin evidencia.
- target_region: existe evidencia de operación en Estados Unidos, Europa o
  Latinoamérica. No asumas la región por el idioma de la fuente.
- technical_founder: hay un fundador técnico identificable con evidencia.
- early_stage: la empresa está en pre-seed/seed temprana (excluye Serie A+).
- product_built: existe un producto tangible (MVP, demo, repo, prototipo).
- problem_validated: hay señal real de demanda o validación del problema.

Reglas:
1. Recorre TODAS las fuentes (incluidas listas y rankings) y extrae CADA \
fundador o startup early-stage nombrado, aunque se mencione brevemente. \
Las startups nombradas sin fundador identificado también cuentan (usa el \
nombre de la startup como "company" y deja "name" con el fundador si se \
conoce o el nombre de la startup si no). No inventes datos que no aparezcan \
en el material.
2. Descarta candidatos que no tengan evidencia de sector Y región dentro de la
tesis. Para los demás, la evidencia parcial es normal en scouting: incluye al
candidato y refleja la incertidumbre con scores bajos y gates en false — NO
lo omitas. Devuelve lista vacía SOLO si ninguna persona/startup concreta y
elegible aparece nombrada.
3. Cada afirmación debe estar respaldada por la evidencia (cita URLs).
4. En "feedback" lista 3-5 acciones CONCRETAS que el fundador debería \
ejecutar para calificar al fondo (qué le falta y cómo mejorarlo).
5. Intenta devolver entre 3 y 8 candidatos cuando las fuentes lo permitan.

Responde ÚNICAMENTE con JSON válido, sin markdown, con esta estructura:
{{
  "founders": [
    {{
      "name": "string",
      "company": "string",
      "role": "string",
      "justification": "string (2-4 frases en español citando evidencia)",
      "criteria": {{
        {_CRITERIA_JSON}
      }},
      "gates": {{
        {_GATES_JSON}
      }},
      "evidence": ["url1", "url2"],
      "signals": ["señal técnica concreta"],
      "contact_hint": "string (canal público de contacto, o vacío)",
      "feedback": ["acción concreta de mejora", "..."]
    }}
  ]
}}
Si no hay fundadores identificables, devuelve {{"founders": []}}.
"""


def _build_user_prompt(query: str, hits: list[SearchHit]) -> str:
    blocks = []
    for i, hit in enumerate(hits, 1):
        blocks.append(
            f"[Fuente {i}]\nTítulo: {hit.title}\nURL: {hit.url}\n"
            f"Contenido: {hit.content[:3000]}"
        )
    sources = "\n\n".join(blocks) if blocks else "(sin resultados)"
    return (
        f"Sector/tecnología buscada: {query}\n\n"
        f"Evidencia web recolectada por el Scout:\n\n{sources}\n\n"
        "Identifica y evalúa a los fundadores/startups según la rúbrica. "
        "Devuelve solo el JSON."
    )


def _extract_json(text: str) -> dict:
    """Parseo robusto: tolera fences de markdown o texto alrededor del JSON."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _clamp(value, lo=0, hi=100) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return lo


def _parse_founder(item: dict) -> FounderProfile:
    raw_criteria = item.get("criteria", {}) or {}
    criteria = []
    weighted = 0.0
    for key, label, weight in RUBRIC:
        entry = raw_criteria.get(key, {}) or {}
        score = _clamp(entry.get("score", 0))
        weighted += score * weight / 100.0
        criteria.append(
            CriterionScore(
                name=label,
                weight=weight,
                score=score,
                rationale=str(entry.get("rationale", "")).strip(),
            )
        )

    raw_gates = item.get("gates", {}) or {}
    requirements = []
    for key, label in GATES:
        entry = raw_gates.get(key, {}) or {}
        requirements.append(
            Requirement(
                name=label,
                met=bool(entry.get("met", False)),
                detail=str(entry.get("detail", "")).strip(),
            )
        )

    return FounderProfile(
        name=str(item.get("name", "")).strip(),
        company=str(item.get("company", "")).strip(),
        role=str(item.get("role", "")).strip(),
        founder_score=max(1, round(weighted)),
        justification=str(item.get("justification", "")).strip(),
        criteria=criteria,
        requirements=requirements,
        evidence=[str(u) for u in item.get("evidence", []) or []],
        signals=[str(s) for s in item.get("signals", []) or []],
        contact_hint=str(item.get("contact_hint", "")).strip(),
        feedback=[str(f) for f in item.get("feedback", []) or []],
    )


def judge(query: str, hits: list[SearchHit]) -> tuple[list[FounderProfile], str]:
    """Evalúa los hits y devuelve (fundadores ordenados por score, proveedor)."""
    if not hits:
        return [], "n/a"

    raw, provider = llm.complete(
        SYSTEM_PROMPT, _build_user_prompt(query, hits), max_tokens=12000
    )
    data = _extract_json(raw)

    founders = []
    for item in data.get("founders", []):
        try:
            founders.append(_parse_founder(item))
        except (TypeError, ValueError, AttributeError):
            continue  # entrada malformada: se descarta, no rompe el pipeline

    founders.sort(key=lambda f: f.founder_score, reverse=True)
    return founders, provider
