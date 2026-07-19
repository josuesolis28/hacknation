"""Enriquecimiento de perfiles mediante fuentes públicas indexadas.

No inicia sesión ni extrae contenido privado de LinkedIn, Instagram o X. Los
nodos representan únicamente evidencia pública recuperada por el Scout.
"""

import json
import re
from functools import lru_cache
from urllib.parse import urlparse

from . import llm
from .config import settings
from .cost import CostTracker
from .search import web_search_hits


def _platform_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "linkedin.com" in host:
        return "linkedin"
    if "instagram.com" in host:
        return "instagram"
    if "twitter.com" in host or "x.com" in host:
        return "x"
    if "facebook.com" in host:
        return "facebook"
    if "github.com" in host:
        return "github"
    if "crunchbase.com" in host:
        return "crunchbase"
    return "website"


def _social_from_hits(hits: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    links: list[dict[str, str]] = []
    priority = ("linkedin", "instagram", "website", "x", "github", "facebook", "crunchbase")
    collected: list[dict[str, str]] = []
    for hit in hits:
        url = hit.get("url", "")
        if not url or url in seen:
            continue
        platform = _platform_from_url(url)
        # Incluye LinkedIn, Instagram, web corporativa y perfiles sociales.
        if platform == "website":
            host = urlparse(url).netloc.lower()
            if any(skip in host for skip in ("news", "medium.com", "wikipedia", "crunchbase.com")):
                continue
        seen.add(url)
        label = {
            "linkedin": "LinkedIn",
            "instagram": "Instagram",
            "website": "Website",
            "x": "X",
        }.get(platform, platform.title())
        collected.append({"platform": platform, "url": url, "label": label})
    collected.sort(key=lambda item: priority.index(item["platform"]) if item["platform"] in priority else 99)
    return collected[:8]


def _hits(query: str, budget: CostTracker) -> list[dict[str, str]]:
    suffixes = ("LinkedIn", "X Twitter", "Instagram", "team CTO founder", "Tecnológico de Monterrey OR TecLeap")
    queries = [f"{query} {suffix}" for suffix in suffixes]
    hits = web_search_hits(queries, max_results=3, budget=budget)
    return [
        {"title": h["title"], "url": h["url"], "content": h["content"][:1800]}
        for h in hits[:12]
    ]


@lru_cache(maxsize=256)
def analyze_public_profiles(name: str, company: str, role: str) -> dict:
    """Construye una red de personas y perfiles públicos; el caché evita repetición de APIs."""
    budget = CostTracker(limit_usd=settings.max_search_cost_usd)
    query = f'"{name}" "{company}" {role}'.strip()
    hits = _hits(query, budget)
    evidence = "\n\n".join(f"[{i + 1}] {h['title']}\n{h['url']}\n{h['content']}" for i, h in enumerate(hits))
    system = """Eres analista de talento B2B. A partir de fuentes públicas, arma una red verificable.
No inventes perfiles, cargos, relaciones ni URLs. No infieras cuentas sociales si la URL no aparece.
Devuelve JSON: {
  "summary":"...",
  "nodes":[{"name":"...","role":"...","relationship":"founder|executive|advisor|company","description":"...","skills":["..."],"area":"...","sources":["url"]}],
  "social_links":[{"platform":"linkedin|instagram|x|website|other","url":"...","label":"..."}],
  "citations":[{"title":"...","url":"..."}]
}. Incluye fundador, CTO y ejecutivos relevantes solo cuando tengan evidencia.
social_links solo con URLs explícitas en las fuentes."""
    raw, provider = llm.complete(
        system, f"Objetivo: {query}\n\nFuentes públicas:\n{evidence}", max_tokens=3500, budget=budget, label="profiles"
    )
    try:
        data = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        data = {"summary": "No se pudo estructurar la red automáticamente.", "nodes": [], "citations": [], "social_links": []}
    citations = data.get("citations") or [{"title": hit["title"] or hit["url"], "url": hit["url"]} for hit in hits]
    llm_social = data.get("social_links") or []
    merged: dict[str, dict[str, str]] = {}
    for link in _social_from_hits(hits) + [s for s in llm_social if isinstance(s, dict)]:
        url = str(link.get("url", "")).strip()
        if not url:
            continue
        platform = str(link.get("platform") or _platform_from_url(url)).lower()
        if platform == "twitter":
            platform = "x"
        merged[url] = {
            "platform": platform,
            "url": url,
            "label": str(link.get("label") or platform).strip(),
        }
    return {
        "subject": {"name": name, "company": company, "role": role},
        "summary": str(data.get("summary", "")),
        "nodes": data.get("nodes", []),
        "social_links": list(merged.values()),
        "citations": citations,
        "provider": provider,
    }
