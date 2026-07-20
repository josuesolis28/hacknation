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


_REJECTION_LANGUAGES = {"es": "Spanish", "en": "English", "de": "German"}

_REJECTION_SYSTEM_PROMPT = """\
Eres el asociado de un fondo VC Early-Stage (Maschmeyer Group) escribiendo \
una respuesta de rechazo personalizada y respetuosa a un founder cuya \
startup no calificó en esta ronda.

Reglas:
- Máximo 100 palabras, tono humano y directo, nunca genérico ni frío.
- Cita 1-2 razones CONCRETAS del feedback dado — no inventes otras ni seas vago.
- Deja la puerta abierta: si resuelven esos puntos, pueden volver a aplicar.
- Escribe TODO el mensaje en {language}.
- Responde SOLO con el cuerpo del mensaje, sin asunto ni firma extra.
"""


def generate_rejection_note(founder: FounderProfile, language: str) -> tuple[str, str]:
    """Genera la nota de rechazo personalizada en el idioma indicado
    (es/en/de). Devuelve (nota, proveedor)."""
    lang_name = _REJECTION_LANGUAGES.get(language, "English")
    system = _REJECTION_SYSTEM_PROMPT.format(language=lang_name)
    user = (
        f"Fundador: {founder.name}\n"
        f"Empresa: {founder.company}\n"
        f"Score: {founder.founder_score}/100\n"
        f"Feedback específico: {'; '.join(founder.feedback) or 'n/a'}\n"
        f"Justificación: {founder.justification or 'n/a'}\n\n"
        "Escribe el mensaje de rechazo personalizado."
    )
    message, provider = llm.complete(system, user, max_tokens=600)
    return message.strip(), provider
