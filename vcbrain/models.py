"""Estructuras de datos compartidas. El contrato es estable sin importar
qué proveedor de LLM esté activo."""

from dataclasses import dataclass, field, asdict


@dataclass
class SearchHit:
    """Un resultado limpio devuelto por Tavily."""
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
    feedback: list[str] = field(default_factory=list)  # qué falta / qué mejorar
    check: Check | None = None               # solo si decision == "approved"

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

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "provider_used": self.provider_used,
            "founders": [f.to_dict() for f in self.founders],
            "raw_hits": [h.to_dict() for h in self.raw_hits],
            "errors": self.errors,
        }
