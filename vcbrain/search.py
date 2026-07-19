"""Capa Scout: búsqueda web vía OpenAI (tool "web_search" de la Responses API).

Tavily dejó de responder de forma confiable, así que el propio ChatGPT hace
ahora la búsqueda: recibe las mismas queries especializadas de la tesis DACH
(vcbrain.thesis) y devuelve URLs y fragmentos reales (citas), que se mapean
al mismo contrato SearchHit que consume el Judge.
"""

import logging

from openai import OpenAI

from .config import settings
from .models import SearchHit
from .thesis import maschmeyer_queries

logger = logging.getLogger(__name__)

# Consultas orientadas a founders/startups "jalables" al fondo: etapa
# pre-seed, levantando o por levantar, con producto construido.
QUERY_TEMPLATES = [
    "{query} pre-seed startup founder raising funding 2025 2026",
    "{query} early-stage technical founder launched MVP demo GitHub",
    "{query} startup pre-seed seed looking for investors traction",
]


def scout(query: str, max_results: int | None = None) -> list[SearchHit]:
    """Ejecuta varias búsquedas vía OpenAI y devuelve hits deduplicados por URL."""
    return _search_queries(
        [template.format(query=query) for template in QUERY_TEMPLATES],
        max_results=max_results,
    )


def scout_maschmeyer(max_results: int | None = None) -> list[SearchHit]:
    """Busca automáticamente toda la tesis de Maschmeyer Group.

    Limita cada combinación vertical/región para distribuir la cobertura y
    no agotar la cuota de la API con una sola geografía dominante.
    """
    return _search_queries(maschmeyer_queries(), max_results=max_results or 3)


def _search_queries(queries: list[str], max_results: int | None = None) -> list[SearchHit]:
    """Ejecuta consultas de búsqueda web con ChatGPT y deduplica por URL."""
    hits: dict[str, SearchHit] = {}
    for item in web_search_hits(queries, max_results=max_results):
        url = item["url"]
        if url in hits:
            continue
        hits[url] = SearchHit(
            title=item["title"],
            url=url,
            content=item["content"],
            score=item["score"],
        )

    # Los más relevantes primero (orden de aparición como proxy de relevancia)
    return sorted(hits.values(), key=lambda h: h.score, reverse=True)


def web_search_hits(queries: list[str], max_results: int | None = None) -> list[dict]:
    """Ejecuta N consultas contra la tool "web_search" de OpenAI y devuelve
    dicts {title, url, content, score} deduplicados por URL. Reutilizable por
    cualquier capa que necesite evidencia web (Scout, enriquecimiento de perfiles)."""
    client = OpenAI(api_key=settings.openai_api_key)
    limit = max_results or settings.search_max_results

    results: dict[str, dict] = {}
    for query in queries:
        try:
            response = client.responses.create(
                model=settings.openai_search_model,
                tools=[{"type": "web_search"}],
                input=(
                    "Busca en la web fuentes reales, públicas y recientes para: "
                    f"{query}\n"
                    f"Devuelve hasta {limit} fuentes distintas y relevantes, cada una "
                    "con URL pública verificable."
                ),
            )
        except Exception as exc:
            # Una consulta fallida no debe tumbar el pipeline completo
            logger.warning("Búsqueda OpenAI falló para %r: %s", query, exc)
            continue

        for item in _extract_citations(response):
            if item["url"] not in results:
                results[item["url"]] = item

    return list(results.values())


def _line_span(text: str, start: int, end: int) -> str:
    """Expande un tramo (start..end) a la línea/viñeta completa que lo contiene.

    Las anotaciones `url_citation` solo marcan el marcador de la cita en el
    texto (p. ej. "([startbase.de](url))"), no el hecho que la sustenta. La
    frase con la información real está en la misma línea, así que se toma el
    bloque completo entre el salto de línea anterior y el siguiente.
    """
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()


def _extract_citations(response) -> list[dict]:
    """Extrae citas (título/url/fragmento) de una respuesta de la Responses API.

    El tool "web_search" adjunta anotaciones `url_citation` a los bloques de
    texto del mensaje de salida; cada anotación referencia el tramo de texto
    (start_index..end_index) que la sustenta. Como una misma URL puede citarse
    varias veces (distintos hechos), se acumula el contenido por URL.
    """
    by_url: dict[str, dict] = {}
    order: list[str] = []
    for item in getattr(response, "output", None) or []:
        for block in getattr(item, "content", None) or []:
            text = getattr(block, "text", "") or ""
            for ann in getattr(block, "annotations", None) or []:
                if getattr(ann, "type", "") != "url_citation":
                    continue
                url = str(getattr(ann, "url", "") or "").strip()
                if not url:
                    continue
                start = getattr(ann, "start_index", None)
                end = getattr(ann, "end_index", None)
                if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text):
                    line = _line_span(text, start, end)
                else:
                    line = text[:600].strip()

                title = str(getattr(ann, "title", "") or url).strip()
                if url not in by_url:
                    order.append(url)
                    by_url[url] = {"title": title, "url": url, "lines": []}
                if line and line not in by_url[url]["lines"]:
                    by_url[url]["lines"].append(line)

    results = []
    for rank, url in enumerate(order, start=1):
        entry = by_url[url]
        results.append(
            {
                "title": entry["title"],
                "url": url,
                "content": "\n".join(entry["lines"]).strip(),
                "score": 1.0 / rank,
            }
        )
    return results
