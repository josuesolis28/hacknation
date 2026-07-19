"""Capa Connect: genera el outreach personalizado e inmediato.

En el MVP el "envío" es la generación del mensaje listo para copiar/enviar
(el canal real — email, LinkedIn, X — se conecta después). La lógica de
salida queda desacoplada para enchufar cualquier proveedor de mensajería.
"""

from . import llm
from .models import FounderProfile

SYSTEM_PROMPT = """\
Eres el asociado de un fondo VC Early-Stage (Maschmeyer Group). Escribes \
mensajes de primer contacto a fundadores técnicos.

Reglas:
- Máximo 120 palabras, tono directo y humano, sin adulación genérica.
- Menciona 1-2 datos concretos de su trabajo (de la evidencia dada) para \
demostrar que hicimos la tarea.
- Cierra con una propuesta clara: una llamada de 20 minutos esta semana.
- Escribe en el idioma más probable del fundador (inglés por defecto).
- Responde SOLO con el cuerpo del mensaje, sin asunto ni firma extra.
"""


def generate_outreach(founder: FounderProfile) -> tuple[str, str]:
    """Genera el mensaje personalizado. Devuelve (mensaje, proveedor)."""
    user = (
        f"Fundador: {founder.name}\n"
        f"Empresa: {founder.company}\n"
        f"Rol: {founder.role}\n"
        f"Señales técnicas: {'; '.join(founder.signals) or 'n/a'}\n"
        f"Justificación del score: {founder.justification}\n"
        f"Evidencia: {'; '.join(founder.evidence) or 'n/a'}\n\n"
        "Escribe el mensaje de primer contacto."
    )
    message, provider = llm.complete(SYSTEM_PROMPT, user, max_tokens=1000)
    return message.strip(), provider
