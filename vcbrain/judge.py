"""Capa Judge + Score: evalúa la evidencia web y asigna el Founder Score.

Criterios VC Early-Stage (estilo aprobación instantánea):
- Quiénes son: trayectoria técnica verificable, equipo consolidado.
- Qué han construido: código público, demos, lanzamientos reales.
- Velocidad de ejecución: cadencia de shipping, tracción temprana.
"""

import json
import re

from . import llm
from .models import FounderProfile, SearchHit

SYSTEM_PROMPT = """\
Eres el motor de análisis de "The VC Brain", un sistema de aprobación \
instantánea de inversión para un fondo VC Early-Stage (pre-seed/seed).

Tu trabajo: a partir de evidencia web real, identificar FUNDADORES TÉCNICOS \
en etapa temprana y evaluarlos objetivamente.

Criterios de scoring (Founder Score, 1-100):
- 35 pts — Capacidad técnica demostrada: código público, arquitectura, \
profundidad del producto construido.
- 25 pts — Velocidad de ejecución: qué tan rápido lanzan, cadencia de \
releases/demos, tracción temprana.
- 20 pts — Equipo: co-fundadores complementarios, equipos consolidados \
puntúan más alto que fundadores solitarios.
- 20 pts — Señal de mercado: relevancia del problema, timing, usuarios o \
interés verificable.

Reglas estrictas:
1. SOLO incluye personas con evidencia real en el material proporcionado. \
No inventes nombres, empresas ni datos.
2. Cada afirmación en la justificación debe estar respaldada por la evidencia \
(cita las URLs en el campo "evidence").
3. Si la evidencia es débil, refleja eso en un score bajo — no infles scores.
4. Excluye empresas en etapas tardías (Serie B+) y ejecutivos no fundadores.

Responde ÚNICAMENTE con JSON válido, sin markdown ni texto adicional, con \
esta estructura exacta:
{
  "founders": [
    {
      "name": "string",
      "company": "string",
      "role": "string",
      "founder_score": 0,
      "justification": "string (2-4 frases, en español, citando evidencia)",
      "evidence": ["url1", "url2"],
      "signals": ["señal técnica concreta", "..."],
      "contact_hint": "string (perfil/canal público donde contactarlo, o vacío)"
    }
  ]
}
Si no hay fundadores identificables, devuelve {"founders": []}.
"""


def _build_user_prompt(query: str, hits: list[SearchHit]) -> str:
    blocks = []
    for i, hit in enumerate(hits, 1):
        blocks.append(
            f"[Fuente {i}]\nTítulo: {hit.title}\nURL: {hit.url}\n"
            f"Contenido: {hit.content[:2000]}"
        )
    sources = "\n\n".join(blocks) if blocks else "(sin resultados)"
    return (
        f"Sector/tecnología buscada: {query}\n\n"
        f"Evidencia web recolectada por el Scout:\n\n{sources}\n\n"
        "Identifica y evalúa a los fundadores según los criterios. "
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
        # último recurso: primer objeto { ... } en el texto
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def judge(query: str, hits: list[SearchHit]) -> tuple[list[FounderProfile], str]:
    """Evalúa los hits y devuelve (fundadores ordenados por score, proveedor)."""
    if not hits:
        return [], "n/a"

    raw, provider = llm.complete(SYSTEM_PROMPT, _build_user_prompt(query, hits))
    data = _extract_json(raw)

    founders = []
    for item in data.get("founders", []):
        try:
            score = max(1, min(100, int(item.get("founder_score", 0))))
            founders.append(
                FounderProfile(
                    name=str(item.get("name", "")).strip(),
                    company=str(item.get("company", "")).strip(),
                    role=str(item.get("role", "")).strip(),
                    founder_score=score,
                    justification=str(item.get("justification", "")).strip(),
                    evidence=[str(u) for u in item.get("evidence", [])],
                    signals=[str(s) for s in item.get("signals", [])],
                    contact_hint=str(item.get("contact_hint", "")).strip(),
                )
            )
        except (TypeError, ValueError):
            continue  # entrada malformada: se descarta, no rompe el pipeline

    founders.sort(key=lambda f: f.founder_score, reverse=True)
    return founders, provider
