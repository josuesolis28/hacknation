"""Capa Scout: búsqueda web optimizada para IA vía Tavily.

Tavily devuelve texto limpio y relevante (sin ruido de HTML/ads), ideal
para alimentar directamente al filtro cognitivo.
"""

from tavily import TavilyClient

from .config import settings
from .models import SearchHit

# Consultas complementarias para triangular señales de fundadores técnicos
QUERY_TEMPLATES = [
    "{query} early-stage startup technical founder 2024 2025",
    "{query} founder launched open source GitHub demo",
    "{query} pre-seed seed startup founder building",
]


def scout(query: str, max_results: int | None = None) -> list[SearchHit]:
    """Ejecuta varias búsquedas Tavily y devuelve hits deduplicados por URL."""
    client = TavilyClient(api_key=settings.tavily_api_key)
    limit = max_results or settings.tavily_max_results

    hits: dict[str, SearchHit] = {}
    for template in QUERY_TEMPLATES:
        q = template.format(query=query)
        try:
            response = client.search(
                query=q,
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
