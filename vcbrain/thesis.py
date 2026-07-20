"""Tesis MVP: startups based in Germany, Switzerland and Austria (DACH).

Secciones y tamaños de ronda alineados al formulario de intake del fondo.
"""

# Secciones exactas del formulario (requisito de clasificación).
MVP_SECTIONS = (
    "HealthTech & MedTech",
    "FinTech & InsurTech",
    "Food & AgTech",
    "Logistics & Supply Chain",
    "HR Tech",
    "LegalTech & RegTech",
    "Retail & E-Commerce",
    "EdTech",
    "CleanTech & Energy",
    "PropTech & Construction",
    "Cybersecurity",
)

# Alias históricos / internos → se mapean a MVP_SECTIONS en el judge.
MASCHMEYER_SECTORS = MVP_SECTIONS

# País base obligatorio para este MVP (no US / LatAm / resto de Europa).
DACH_COUNTRIES = (
    ("Germany", "DE"),
    ("Switzerland", "CH"),
    ("Austria", "AT"),
)

TARGET_REGIONS = (
    "Germany",
    "Switzerland",
    "Austria",
    "DACH",
)

PRIORITY_COUNTRIES = DACH_COUNTRIES

# Tamaños de ronda del formulario: "How big is the round you are raising?"
ROUND_SIZES = (
    "< EUR 1 mio",
    "EUR 1-2 mio",
    "EUR 2-3 mio",
    "EUR 3-4 mio",
    "EUR 4-5 mio",
    "> EUR 5 mio",
)

DISCOVERY_SOURCES = (
    "EU-Startups",
    "German Accelerator",
    "Techstars Berlin",
    "Startup Autobahn",
    "High-Tech Gründerfonds",
    "Swiss Startup Association",
    "Venture Kick",
    "Austria Wirtschaftsservice",
    "aws Gründung",
    "F6S",
    "OpenVC",
    "demo day",
    "seed round",
    "Series A",
)

# Comunidades donde founders early-stage se mueven y anuncian tracción antes
# de tener cobertura de prensa — se suman a los términos de descubrimiento en
# vez de generar queries nuevas (cada query cuesta, ver vcbrain/cost.py).
COMMUNITY_SOURCES = (
    "reddit.com/r/startups",
    "reddit.com/r/Entrepreneur",
    "Discord community",
    "Slack community",
    "Product Hunt",
)


def maschmeyer_queries() -> list[str]:
    """Una sola consulta por sección (cubre los 3 países DACH, las fuentes de
    descubrimiento y las comunidades en el mismo texto) — antes eran dos
    queries por sección, el doble de llamadas al tool "web_search" de
    OpenAI (que es caro: tarifa por llamada + tokens de contexto). Con esto
    una corrida completa dispara como máximo 1 query × sección, nunca más."""
    source_terms = " OR ".join(f'"{source}"' for source in DISCOVERY_SOURCES)
    community_terms = " OR ".join(f'"{source}"' for source in COMMUNITY_SOURCES)
    queries = []
    for section in MVP_SECTIONS:
        queries.append(
            f'"{section}" startup OR founder (Germany OR Switzerland OR Austria OR DACH) '
            f'(raising OR fundraising OR "seed round" OR "Series A" OR pitch OR email OR contact) '
            f'({source_terms} OR LinkedIn OR Instagram OR website OR {community_terms})'
        )
    return queries


def maschmeyer_scope_label() -> str:
    return (
        "DACH MVP: Germany, Switzerland, Austria | Sections: "
        + ", ".join(MVP_SECTIONS)
    )
