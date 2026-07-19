"""Estructuras de datos compartidas. El contrato es estable sin importar
qué proveedor de LLM esté activo (Anthropic u OpenAI)."""

from dataclasses import dataclass, field, asdict


@dataclass
class SearchHit:
    """Un resultado limpio devuelto por Tavily."""
    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class FounderProfile:
    """Un fundador evaluado por el motor cognitivo (Judge + Score)."""
    name: str
    company: str
    role: str
    founder_score: int          # 1-100
    justification: str          # por qué ese score, basado en evidencia
    evidence: list[str] = field(default_factory=list)   # URLs / hechos concretos
    signals: list[str] = field(default_factory=list)    # señales técnicas (repos, lanzamientos, velocidad)
    contact_hint: str = ""      # dónde contactarlo (perfil, email público, etc.)
    outreach_message: str = ""  # mensaje personalizado generado (Connect)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineResult:
    """Resultado completo de una ejecución Scout → Judge → Score."""
    query: str
    provider_used: str          # "anthropic" | "openai" — cuál respondió realmente
    founders: list[FounderProfile] = field(default_factory=list)
    raw_hits: list[SearchHit] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
