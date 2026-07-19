"""Alta directa de startups por el propio founder — sin scraping.

Reutiliza exactamente el mismo Judge/Score/Decide/Dedup que usa el Scout: la
única diferencia es de dónde sale la evidencia. En vez de que OpenAI
busque en la web, la evidencia la entrega directamente quien llena el
formulario (empresa, equipo, redes sociales, pitch, PDF del deck, video
pitch). Los campos son deliberadamente los mismos que el Judge extrae y
pondera del Scout (ver judge.py SYSTEM_PROMPT) — mismo rubro, mismos gates,
mismo semáforo, solo cambia de dónde sale la evidencia.
"""

import logging

from . import db
from .decision import decide
from .judge import judge
from .models import FounderProfile, SearchHit, SocialLink, TeamMember, founder_from_dict

logger = logging.getLogger(__name__)


def extract_pdf_text(data: bytes, max_chars: int = 8000) -> str:
    """Extrae texto plano de un PDF (pitch deck, resumen ejecutivo, etc.)."""
    try:
        from pypdf import PdfReader
        from io import BytesIO

        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()[:max_chars]
    except Exception as exc:
        logger.warning("No se pudo extraer texto del PDF: %s", exc)
        return ""


def _team_relationship(role: str) -> str:
    role_lower = (role or "").lower()
    if "advisor" in role_lower or "asesor" in role_lower:
        return "advisor"
    if "co-founder" in role_lower or "cofounder" in role_lower or "co founder" in role_lower:
        return "cofounder"
    return "executive"


def submit_startup(
    *,
    submitter: str,
    company: str,
    name: str,
    role: str,
    country: str,
    website: str = "",
    section: str = "",
    round_size: str = "",
    pitch: str = "",
    extra_text: str = "",
    video_url: str,
    business_email: str = "",
    linkedin: str = "",
    instagram: str = "",
    x_url: str = "",
    team: list[dict] | None = None,
    pdf: tuple[bytes, str, str] | None = None,  # (data, filename, content_type)
) -> FounderProfile:
    pdf_text = extract_pdf_text(pdf[0]) if pdf else ""
    team = team or []

    team_lines = [f"Founder/contact: {name}" + (f" ({role})" if role else "")]
    for member in team:
        m_name = str(member.get("name", "")).strip()
        m_role = str(member.get("role", "")).strip()
        if m_name:
            team_lines.append(f"Team member: {m_name}" + (f" ({m_role})" if m_role else ""))

    social_lines = []
    if linkedin:
        social_lines.append(f"LinkedIn: {linkedin}")
    if instagram:
        social_lines.append(f"Instagram: {instagram}")
    if x_url:
        social_lines.append(f"X/Twitter: {x_url}")

    content = "\n".join(
        line
        for line in [
            f"Company: {company}",
            *team_lines,
            f"HQ country: {country} (confirmado directamente por el founder al enviar este formulario)",
            f"Website: {website}" if website else "",
            *social_lines,
            f"Business email: {business_email}" if business_email else "",
            f"Suggested section: {section}" if section else "",
            f"Round size: {round_size}" if round_size else "",
            f"Pitch: {pitch}" if pitch else "",
            f"Pitch video: {video_url}",
            extra_text.strip() if extra_text else "",
            f"Pitch deck (extracted from uploaded PDF):\n{pdf_text}" if pdf_text else "",
        ]
        if line
    )
    hit = SearchHit(title=company, url=website or f"self-submitted:{company}", content=content, score=1.0)

    try:
        founders, _provider = judge(f"Startup auto-enviada: {company}", [hit])
    except Exception as exc:
        logger.warning("Judge falló para submission de %s: %s", company, exc)
        founders = []

    if founders:
        founder = founders[0]
    else:
        # Sin evidencia suficiente para el gate DACH u otro filtro — se
        # registra igual como rechazada, para no perder el registro ni dar
        # feedback de qué faltó.
        founder = FounderProfile(
            name=name,
            company=company,
            role=role,
            founder_score=0,
            justification="No se pudo confirmar evidencia suficiente contra la tesis DACH.",
            contact_hint=name,
            country=country,
            section=section,
            round_size=round_size,
            pitch=pitch,
        )

    # Campos que el propio founder ya confirmó explícitamente en el
    # formulario son más confiables que lo que el LLM pudiera re-inferir del
    # texto plano — se imponen sobre lo que haya devuelto el Judge.
    founder.team = [
        TeamMember(name=name, role=role, relationship="founder", skills=[], area=section, profile_url="")
    ] + [
        TeamMember(
            name=str(m.get("name", "")).strip(),
            role=str(m.get("role", "")).strip(),
            relationship=_team_relationship(str(m.get("role", ""))),
            skills=[],
            area=section,
            profile_url="",
        )
        for m in team
        if str(m.get("name", "")).strip()
    ]
    if business_email:
        founder.business_email = business_email
    social_map = {s.platform: s for s in founder.social_links}
    for platform, url in (("linkedin", linkedin), ("instagram", instagram), ("x", x_url)):
        if url:
            social_map[platform] = SocialLink(platform=platform, url=url, label=platform.title())
    founder.social_links = list(social_map.values())
    if video_url and video_url not in founder.evidence:
        founder.evidence.append(video_url)

    founder = decide(founder)
    merged_dict, _is_new = db.merge_company(founder.to_dict())
    merged = decide(founder_from_dict(merged_dict))

    submission_id = db.create_submission(
        submitter=submitter,
        company=merged.company,
        name=merged.name,
        country_code=merged.country_code,
    )

    if pdf is not None:
        data, filename, content_type = pdf
        db.save_submission_file(submission_id, "pdf", filename, content_type, data=data)
    db.save_submission_file(submission_id, "video", video_url, "text/uri-list", url=video_url)

    return merged
