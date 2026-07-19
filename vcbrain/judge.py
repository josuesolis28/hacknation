"""Capa Judge + Score: evalúa evidencia contra la tesis MVP DACH.

Requisito indispensable: sede/base en Germany, Switzerland o Austria.
Clasifica en las secciones del formulario y estima el tamaño de ronda en EUR.
"""

import json
import re

from . import llm
from .cost import CostTracker
from .models import (
    CriterionScore,
    FounderProfile,
    FundingRound,
    Requirement,
    SearchHit,
    SocialLink,
    TeamMember,
)
from .thesis import MVP_SECTIONS, ROUND_SIZES

RUBRIC = [
    ("team", "Equipo y founder-market fit", 30),
    ("product", "Producto y capacidad técnica demostrada (MVP/código)", 25),
    ("validation", "Validación del problema y tracción temprana", 20),
    ("market", "Tamaño de mercado y timing", 15),
    ("moat", "Diferenciación / moat defendible", 10),
]

GATES = [
    (
        "dach_based",
        "Based in Germany, Switzerland or Austria (requisito indispensable)",
    ),
    (
        "section_fit",
        "Encaja en una sección del formulario (HealthTech, FinTech, Food & AgTech, …)",
    ),
    ("technical_founder", "Fundador técnico o equipo identificable con evidencia real"),
    ("early_stage", "Etapa early (pre-seed / seed / Series A temprana)"),
    ("product_built", "Producto tangible: MVP, demo, repo o prototipo funcional"),
    ("problem_validated", "Problema validado: usuarios, clientes o señal de demanda"),
]

APPROVAL_THRESHOLD = 70

_SECTIONS_LIST = " | ".join(MVP_SECTIONS)
_ROUNDS_LIST = " | ".join(ROUND_SIZES)

_CRITERIA_JSON = ",\n        ".join(
    f'"{key}": {{"score": 0, "rationale": "string"}}' for key, _, _ in RUBRIC
)
_GATES_JSON = ",\n        ".join(
    f'"{key}": {{"met": true, "detail": "string"}}' for key, _ in GATES
)

SYSTEM_PROMPT = f"""\
Eres el motor de análisis de "The VC Brain" para el MVP DACH de Maschmeyer Group.

SOLO incluye startups con evidencia de estar BASED IN Germany, Switzerland \
o Austria. Si el HQ no está en DE/CH/AT, NO las incluyas.

Secciones válidas (elige exactamente una por empresa):
{_SECTIONS_LIST}

Tamaños de ronda (elige exactamente uno si hay evidencia de fundraising; \
si no, deja vacío):
{_ROUNDS_LIST}

Criterios (0-100, solo evidencia):
- team (30%): trayectoria, founder-market fit, equipo.
- product (25%): MVP, demos, profundidad técnica.
- validation (20%): clientes, tracción, demanda.
- market (15%): tamaño de mercado y timing.
- moat (10%): diferenciación defendible.

Gates:
- dach_based: evidencia de sede/base en Germany, Switzerland o Austria.
- section_fit: la actividad encaja en UNA de las secciones listadas.
- technical_founder / early_stage / product_built / problem_validated:
  como due diligence early-stage estándar.

Campos de intake (solo evidencia pública; no inventes emails ni montos):
- company: nombre de la empresa.
- name / role: fundador o contacto si aparece.
- business_email: email de negocio público (contacto@empresa.com, press@, \
hello@, etc.). Preferir dominio corporativo; si solo hay Gmail de negocio \
público y verificable, úsalo. Si no hay email público, "".
- country / country_code: Germany|Switzerland|Austria y DE|CH|AT.
- origin_region: siempre "DACH" si el país es DE/CH/AT.
- origin_confidence: confirmed|inferred|unknown.
- section: exactamente una de las secciones válidas.
- activity_summary: 1-2 frases de a qué se dedica la empresa.
- round_size: exactamente uno de los buckets EUR, o "" si no hay dato.
- pitch: pitch / one-liner público si aparece.
- other_info: otra info útil (clientes, tracción, aceleradora, etc.).
- skills, area, social_links (prioriza LinkedIn, Instagram, website con URL),
  capital_raised, capital_note, clients, business_model, impact_summary,
  impact_metrics, incubation_program: solo con evidencia.
- team: lista de founders/cofounders [{{"name","role","relationship":"founder|cofounder|executive","skills":[],"area":"","profile_url":""}}].
- total_capital: capital total levantado si aparece (p. ej. "EUR 3.2 mio").
- funding_rounds: fondos/inversores [{{"investor","amount","round_name","date"}}].
- revenue_signal: ARR, revenue o tracción económica pública si existe.
- tec_related: siempre false en este MVP.

Reglas:
1. Extrae cada startup DACH nombrada en las fuentes.
2. Descarta cualquier candidata sin evidencia creíble de DE/CH/AT.
3. No inventes business_email ni round_size.
4. feedback: 3-5 acciones concretas si faltan datos del formulario.
5. Intenta 3-8 candidatos cuando las fuentes lo permitan.

Responde ÚNICAMENTE con JSON válido, sin markdown:
{{
  "founders": [
    {{
      "name": "string",
      "company": "string",
      "role": "string",
      "business_email": "string",
      "country": "Germany | Switzerland | Austria",
      "country_code": "DE | CH | AT",
      "origin_region": "DACH",
      "origin_confidence": "confirmed | inferred | unknown",
      "section": "exact section string",
      "activity_summary": "string",
      "round_size": "exact EUR bucket or empty",
      "pitch": "string",
      "other_info": "string",
      "justification": "string (2-4 frases en español citando evidencia y origen DACH)",
      "criteria": {{
        {_CRITERIA_JSON}
      }},
      "gates": {{
        {_GATES_JSON}
      }},
      "evidence": ["url1", "url2"],
      "signals": ["señal concreta"],
      "contact_hint": "string",
      "feedback": ["acción concreta", "..."],
      "skills": ["habilidad1"],
      "area": "string",
      "social_links": [{{"platform": "linkedin", "url": "https://...", "label": "LinkedIn"}}],
      "capital_raised": "string",
      "capital_note": "string",
      "clients": ["cliente"],
      "business_model": "B2B | B2C | B2B2C | hybrid | unknown",
      "impact_summary": "string",
      "impact_metrics": ["métrica"],
      "incubation_program": "string",
      "tec_related": false,
      "team": [{{"name": "string", "role": "CEO", "relationship": "founder", "skills": ["..."], "area": "...", "profile_url": ""}}],
      "total_capital": "string",
      "funding_rounds": [{{"investor": "string", "amount": "string", "round_name": "Seed", "date": ""}}],
      "revenue_signal": "string"
    }}
  ]
}}
Si no hay fundadores DACH identificables, devuelve {{"founders": []}}.
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
        f"Sector/sección buscada: {query}\n"
        "Ámbito obligatorio: Germany, Switzerland, Austria (DACH).\n\n"
        f"Evidencia web recolectada por el Scout:\n\n{sources}\n\n"
        "Identifica startups DACH, founders/cofounders, redes (LinkedIn/Instagram/web), "
        "capital total, fondos participantes, clientes/revenue si hay evidencia pública. "
        "Devuelve solo el JSON."
    )


def _extract_json(text: str) -> dict:
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


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

_SECTION_ALIASES = {
    "healthtech": "HealthTech & MedTech",
    "medtech": "HealthTech & MedTech",
    "healthtech & medtech": "HealthTech & MedTech",
    "fintech": "FinTech & InsurTech",
    "insurtech": "FinTech & InsurTech",
    "fintech & insurtech": "FinTech & InsurTech",
    "food": "Food & AgTech",
    "agtech": "Food & AgTech",
    "food & agtech": "Food & AgTech",
    "logistics": "Logistics & Supply Chain",
    "supply chain": "Logistics & Supply Chain",
    "logistics & supply chain": "Logistics & Supply Chain",
    "hr tech": "HR Tech",
    "hrtech": "HR Tech",
    "legaltech": "LegalTech & RegTech",
    "regtech": "LegalTech & RegTech",
    "legaltech & regtech": "LegalTech & RegTech",
    "retail": "Retail & E-Commerce",
    "e-commerce": "Retail & E-Commerce",
    "ecommerce": "Retail & E-Commerce",
    "retail & e-commerce": "Retail & E-Commerce",
    "edtech": "EdTech",
    "cleantech": "CleanTech & Energy",
    "energy": "CleanTech & Energy",
    "cleantech & energy": "CleanTech & Energy",
    "proptech": "PropTech & Construction",
    "construction": "PropTech & Construction",
    "proptech & construction": "PropTech & Construction",
    "cybersecurity": "Cybersecurity",
    "cyber security": "Cybersecurity",
    "cyber": "Cybersecurity",
}


def _normalize_section(raw: str, area: str = "") -> str:
    candidates = [raw, area]
    for value in candidates:
        text = str(value or "").strip()
        if not text:
            continue
        if text in MVP_SECTIONS:
            return text
        mapped = _SECTION_ALIASES.get(text.lower())
        if mapped:
            return mapped
        for section in MVP_SECTIONS:
            if section.lower() in text.lower() or text.lower() in section.lower():
                return section
    return ""


def _normalize_round(raw: str, capital: str = "") -> str:
    text = f"{raw} {capital}".lower().replace("€", "eur").replace("million", "mio")
    text = text.replace("m€", "mio").replace("mio.", "mio")
    if not str(raw or "").strip() and not str(capital or "").strip():
        return ""
    exact = str(raw or "").strip()
    if exact in ROUND_SIZES:
        return exact
    # Heurística sobre montos públicos
    nums = re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:mio|m|million)?", text)
    amount = None
    for n in nums:
        try:
            amount = float(n.replace(",", "."))
            break
        except ValueError:
            continue
    if amount is None:
        if "<" in text and "1" in text:
            return "< EUR 1 mio"
        if ">" in text and "5" in text:
            return "> EUR 5 mio"
        return exact if exact in ROUND_SIZES else ""
    if amount < 1:
        return "< EUR 1 mio"
    if amount < 2:
        return "EUR 1-2 mio"
    if amount < 3:
        return "EUR 2-3 mio"
    if amount < 4:
        return "EUR 3-4 mio"
    if amount <= 5:
        return "EUR 4-5 mio"
    return "> EUR 5 mio"


def _normalize_email(raw: str, contact_hint: str = "") -> str:
    for source in (raw, contact_hint):
        match = _EMAIL_RE.search(str(source or ""))
        if match:
            return match.group(0).lower()
    return ""


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

    country, country_code, origin_region, origin_confidence = _normalize_origin(item)

    social_links = []
    for link in item.get("social_links", []) or []:
        if not isinstance(link, dict):
            continue
        url = str(link.get("url", "")).strip()
        if not url:
            continue
        platform = str(link.get("platform", "other") or "other").strip().lower()
        if platform == "twitter":
            platform = "x"
        social_links.append(
            SocialLink(
                platform=platform,
                url=url,
                label=str(link.get("label", "") or platform).strip(),
            )
        )

    business = str(item.get("business_model", "") or "unknown").strip()
    if business.lower() not in {"b2b", "b2c", "b2b2c", "hybrid", "unknown"}:
        business = "unknown"
    else:
        business = business.upper() if business.lower() in {"b2b", "b2c", "b2b2c"} else business.lower()

    area = str(item.get("area", "")).strip()
    section = _normalize_section(str(item.get("section", "")).strip(), area)
    if section and not area:
        area = section

    capital_raised = str(item.get("capital_raised", "")).strip()
    round_size = _normalize_round(str(item.get("round_size", "")).strip(), capital_raised)
    business_email = _normalize_email(
        str(item.get("business_email", "")).strip(),
        str(item.get("contact_hint", "")).strip(),
    )
    activity = str(item.get("activity_summary", "")).strip() or str(item.get("justification", "")).strip()
    pitch = str(item.get("pitch", "")).strip()

    team: list[TeamMember] = []
    for member in item.get("team") or []:
        if not isinstance(member, dict):
            continue
        mname = str(member.get("name", "")).strip()
        if not mname:
            continue
        rel = str(member.get("relationship", "founder") or "founder").strip().lower()
        if rel not in {"founder", "cofounder", "executive", "advisor"}:
            rel = "founder"
        team.append(
            TeamMember(
                name=mname,
                role=str(member.get("role", "")).strip(),
                relationship=rel,
                skills=[str(s).strip() for s in (member.get("skills") or []) if str(s).strip()][:6],
                area=str(member.get("area", "")).strip(),
                profile_url=str(member.get("profile_url", "")).strip(),
            )
        )
    if not team and str(item.get("name", "")).strip():
        team.append(
            TeamMember(
                name=str(item.get("name", "")).strip(),
                role=str(item.get("role", "")).strip() or "Founder",
                relationship="founder",
                skills=[str(s).strip() for s in (item.get("skills") or []) if str(s).strip()][:6],
                area=area or section,
            )
        )

    funding_rounds: list[FundingRound] = []
    for round_item in item.get("funding_rounds") or []:
        if not isinstance(round_item, dict):
            continue
        investor = str(round_item.get("investor", "")).strip()
        if not investor:
            continue
        funding_rounds.append(
            FundingRound(
                investor=investor,
                amount=str(round_item.get("amount", "")).strip(),
                round_name=str(round_item.get("round_name", "")).strip(),
                date=str(round_item.get("date", "")).strip(),
            )
        )

    total_capital = str(item.get("total_capital", "")).strip() or capital_raised or round_size
    revenue_signal = str(item.get("revenue_signal", "")).strip()

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
        contact_hint=str(item.get("contact_hint", "")).strip() or business_email,
        feedback=[str(f) for f in item.get("feedback", []) or []],
        country=country,
        country_code=country_code,
        origin_region=origin_region,
        origin_confidence=origin_confidence,
        skills=[str(s).strip() for s in (item.get("skills") or []) if str(s).strip()][:8],
        area=area,
        social_links=social_links,
        capital_raised=capital_raised or round_size,
        capital_note=str(item.get("capital_note", "")).strip(),
        clients=[str(c).strip() for c in (item.get("clients") or []) if str(c).strip()][:8],
        business_model=business,
        impact_summary=str(item.get("impact_summary", "")).strip(),
        impact_metrics=[str(m).strip() for m in (item.get("impact_metrics") or []) if str(m).strip()][:8],
        incubation_program=str(item.get("incubation_program", "")).strip(),
        tec_related=False,
        business_email=business_email,
        section=section,
        activity_summary=activity,
        round_size=round_size,
        pitch=pitch,
        other_info=str(item.get("other_info", "")).strip(),
        team=team,
        total_capital=total_capital,
        funding_rounds=funding_rounds,
        revenue_signal=revenue_signal,
    )


_REGION_ALIASES = {
    "dach": "DACH",
    "europe": "DACH",
    "eu": "DACH",
    "germany": "DACH",
    "switzerland": "DACH",
    "austria": "DACH",
}

_COUNTRY_ALIASES = {
    "germany": ("Germany", "DE", "DACH"),
    "deutschland": ("Germany", "DE", "DACH"),
    "de": ("Germany", "DE", "DACH"),
    "switzerland": ("Switzerland", "CH", "DACH"),
    "schweiz": ("Switzerland", "CH", "DACH"),
    "suisse": ("Switzerland", "CH", "DACH"),
    "ch": ("Switzerland", "CH", "DACH"),
    "austria": ("Austria", "AT", "DACH"),
    "österreich": ("Austria", "AT", "DACH"),
    "oesterreich": ("Austria", "AT", "DACH"),
    "at": ("Austria", "AT", "DACH"),
}

_DACH_CODES = {"DE", "CH", "AT"}


def _normalize_origin(item: dict) -> tuple[str, str, str, str]:
    """Normaliza país hacia Germany / Switzerland / Austria."""
    raw_country = str(item.get("country", "") or "").strip()
    raw_code = str(item.get("country_code", "") or "").strip().upper()
    raw_region = str(item.get("origin_region", "") or "").strip()
    confidence = str(item.get("origin_confidence", "") or "unknown").strip().lower()
    if confidence not in {"confirmed", "inferred", "unknown"}:
        confidence = "unknown"

    country, country_code, region = "", "", "Unknown"
    alias = _COUNTRY_ALIASES.get(raw_country.lower())
    if alias:
        country, country_code, region = alias
    elif raw_code in _DACH_CODES:
        for _key, (name, code, reg) in _COUNTRY_ALIASES.items():
            if code == raw_code:
                country, country_code, region = name, code, reg
                break
    elif raw_country:
        country = raw_country
        country_code = raw_code[:2] if raw_code else ""
        region = _REGION_ALIASES.get(raw_region.lower(), "Unknown")
    else:
        blob = f"{raw_region} {raw_country}".lower()
        if "switzerland" in blob or "schweiz" in blob or "zurich" in blob or "geneva" in blob:
            country, country_code, region = "Switzerland", "CH", "DACH"
            if confidence == "unknown":
                confidence = "inferred"
        elif "austria" in blob or "österreich" in blob or "vienna" in blob or "wien" in blob:
            country, country_code, region = "Austria", "AT", "DACH"
            if confidence == "unknown":
                confidence = "inferred"
        elif "german" in blob or "berlin" in blob or "munich" in blob or "deutschland" in blob:
            country, country_code, region = "Germany", "DE", "DACH"
            if confidence == "unknown":
                confidence = "inferred"
        else:
            region = _REGION_ALIASES.get(raw_region.lower(), "Unknown")

    if country_code in _DACH_CODES:
        region = "DACH"
    if region not in {"DACH", "Unknown"}:
        region = "Unknown"
    return country, country_code, region, confidence


def _is_dach(founder: FounderProfile) -> bool:
    return founder.country_code in _DACH_CODES or (
        founder.country in {"Germany", "Switzerland", "Austria"} and founder.origin_region == "DACH"
    )


def judge(
    query: str, hits: list[SearchHit], budget: CostTracker | None = None
) -> tuple[list[FounderProfile], str]:
    """Evalúa hits y devuelve solo fundadores DACH ordenados por score."""
    if not hits:
        return [], "n/a"

    raw, provider = llm.complete(
        SYSTEM_PROMPT, _build_user_prompt(query, hits), max_tokens=12000, budget=budget, label="judge"
    )
    data = _extract_json(raw)

    founders = []
    for item in data.get("founders", []):
        try:
            founder = _parse_founder(item)
        except (TypeError, ValueError, AttributeError):
            continue
        if not _is_dach(founder):
            continue
        # Refuerza el gate de sede DACH si el filtro pasó
        for req in founder.requirements:
            if req.name.startswith("Based in Germany"):
                req.met = True
                if not req.detail:
                    req.detail = f"{founder.country} ({founder.country_code})"
        founders.append(founder)

    founders.sort(key=lambda f: f.founder_score, reverse=True)
    return founders, provider
