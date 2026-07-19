"""Tesis de scouting automatizada para Maschmeyer Group.

La tesis se basa en la información pública del grupo y se complementa con
las fuentes de deal-flow del documento de trabajo entregado por el equipo.
"""

MASCHMEYER_SECTORS = (
    "B2B SaaS",
    "FinTech",
    "InsurTech",
    "HealthTech",
    "RegTech",
    "Cyber Security",
    "New Work",
)

TARGET_REGIONS = (
    "United States",
    "Europe",
    "Latin America",
)

# Fuentes abiertas o con páginas públicas que suelen exponer señales de
# startup temprana. Las bases cerradas (Crunchbase, Harmonic, PitchBook,
# LinkedIn Sales Navigator) se mantienen como enriquecimiento externo.
DISCOVERY_SOURCES = (
    "Y Combinator",
    "Techstars",
    "Antler",
    "F6S",
    "Product Hunt",
    "OpenVC",
    "EU-Startups",
    "Latitud",
    "Start-Up Chile",
    "500 Global",
    "Founder Institute",
    "Wayra",
    "demo day",
    "startup accelerator",
)


def maschmeyer_queries() -> list[str]:
    """Genera una consulta por combinación de vertical y región.

    Mantener las combinaciones separadas evita que FinTech o EE. UU. absorban
    todos los resultados y permite cubrir la tesis completa en cada ejecución.
    """
    source_terms = " OR ".join(f'"{source}"' for source in DISCOVERY_SOURCES)
    return [
        (
            f'"{sector}" startup founder pre-seed OR seed "{region}" '
            f'raising OR launched OR cohort ({source_terms})'
        )
        for sector in MASCHMEYER_SECTORS
        for region in TARGET_REGIONS
    ]


def maschmeyer_scope_label() -> str:
    return (
        "Maschmeyer Group: "
        + ", ".join(MASCHMEYER_SECTORS)
        + " | Regiones: "
        + ", ".join(TARGET_REGIONS)
    )
