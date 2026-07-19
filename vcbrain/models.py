"""Estructuras de datos compartidas. El contrato es estable sin importar
qué proveedor de LLM esté activo."""

from dataclasses import dataclass, field, asdict


@dataclass
class SearchHit:
    """Un resultado limpio devuelto por el Scout (búsqueda web vía OpenAI)."""
    title: str
    url: str
    content: str
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CriterionScore:
    """Puntuación de un criterio pre-seed ponderado."""
    name: str
    weight: int          # porcentaje del score total (los pesos suman 100)
    score: int           # 0-100 en ese criterio
    rationale: str


@dataclass
class Requirement:
    """Requisito duro (gate) de elegibilidad al fondo."""
    name: str
    met: bool
    detail: str


@dataclass
class Check:
    """Cheque emitido automáticamente al aprobar."""
    check_id: str
    amount_usd: int
    issued_to: str
    company: str
    issued_by: str
    date: str            # ISO
    status: str          # "issued"


@dataclass
class SocialLink:
    """Enlace a red social pública verificada en fuentes."""
    platform: str   # linkedin | instagram | x | twitter | website | other
    url: str
    label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TeamMember:
    """Founder / cofounder / ejecutivo identificado en fuentes públicas."""
    name: str
    role: str
    relationship: str = "founder"  # founder | cofounder | executive | advisor
    skills: list[str] = field(default_factory=list)
    area: str = ""
    profile_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FundingRound:
    """Ronda o fondo participante con monto público si existe."""
    investor: str
    amount: str = ""
    round_name: str = ""
    date: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FounderProfile:
    """Un fundador/startup evaluado contra la rúbrica pre-seed del fondo."""
    name: str
    company: str
    role: str
    founder_score: int                       # 1-100 (suma ponderada de criterios)
    justification: str
    criteria: list[CriterionScore] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    contact_hint: str = ""
    decision: str = "rejected"               # "approved" | "rejected"
    feedback: list[str] = field(default_factory=list)
    check: Check | None = None
    country: str = ""
    country_code: str = ""
    origin_region: str = ""
    origin_confidence: str = "unknown"
    skills: list[str] = field(default_factory=list)
    area: str = ""
    social_links: list[SocialLink] = field(default_factory=list)
    capital_raised: str = ""
    capital_note: str = ""
    clients: list[str] = field(default_factory=list)
    business_model: str = ""
    impact_summary: str = ""
    impact_metrics: list[str] = field(default_factory=list)
    incubation_program: str = ""
    tec_related: bool = False
    business_email: str = ""
    section: str = ""
    activity_summary: str = ""
    round_size: str = ""
    pitch: str = ""
    other_info: str = ""
    # Semáforo de elegibilidad: green | yellow | red
    traffic_light: str = "red"
    # Equipo: founders / cofounders
    team: list[TeamMember] = field(default_factory=list)
    # Capital e inversores
    total_capital: str = ""
    funding_rounds: list[FundingRound] = field(default_factory=list)
    revenue_signal: str = ""                 # ARR / revenue / facturación pública

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineResult:
    """Resultado completo de una ejecución Scout → Judge → Score → Decide."""
    query: str
    provider_used: str
    founders: list[FounderProfile] = field(default_factory=list)
    raw_hits: list[SearchHit] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    cost_usd: float = 0.0  # costo estimado de esta corrida (ver vcbrain.cost)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "provider_used": self.provider_used,
            "founders": [f.to_dict() for f in self.founders],
            "raw_hits": [h.to_dict() for h in self.raw_hits],
            "errors": self.errors,
            "cost_usd": round(self.cost_usd, 4),
        }
