"""Capa Scout: búsqueda web optimizada para IA vía Tavily.

Tavily devuelve texto limpio y relevante (sin ruido de HTML/ads), ideal
para alimentar directamente al filtro cognitivo.
"""

from tavily import TavilyClient

from .config import settings
from .models import SearchHit
from .thesis import maschmeyer_queries

# Consultas orientadas a founders/startups "jalables" al fondo: etapa
# pre-seed, levantando o por levantar, con producto construido.
QUERY_TEMPLATES = [
    "{query} pre-seed startup founder raising funding 2025 2026",
    "{query} early-stage technical founder launched MVP demo GitHub",
    "{query} startup pre-seed seed looking for investors traction",
]


def scout(query: str, max_results: int | None = None) -> list[SearchHit]:
    """Ejecuta varias búsquedas Tavily y devuelve hits deduplicados por URL."""
    return _search_queries(
        [template.format(query=query) for template in QUERY_TEMPLATES],
        max_results=max_results,
    )


def scout_maschmeyer(max_results: int | None = None) -> list[SearchHit]:
    """Busca automáticamente toda la tesis de Maschmeyer Group.

    Limita cada combinación vertical/región para distribuir la cobertura y
    no agotar la cuota de Tavily con una sola geografía dominante.
    """
    return _search_queries(maschmeyer_queries(), max_results=max_results or 3)


def _search_queries(queries: list[str], max_results: int | None = None) -> list[SearchHit]:
    """Ejecuta consultas Tavily y deduplica los resultados por URL."""
    client = TavilyClient(api_key=settings.tavily_api_key)
    limit = max_results or settings.tavily_max_results

    hits: dict[str, SearchHit] = {}
    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=limit,
                include_answer=False,
            )
        except Exception:
            # Una consulta fallida no debe tumbar el pipeline completo
            continue

        for item in response.get("results", []):
            url = item.get("url", "")
            if not url or url in hits:
                continue
            hits[url] = SearchHit(
                title=item.get("title", ""),
                url=url,
                content=item.get("content", ""),
                score=float(item.get("score", 0.0)),
            )

    # Los más relevantes primero
    return sorted(hits.values(), key=lambda h: h.score, reverse=True)
