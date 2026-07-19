# 🧠 The VC Brain — MVP (Reto Maschmeyer Group)

Sistema de **aprobación instantánea de fundadores early-stage**: rastrea señales en la web, evalúa objetivamente con IA y asigna un *Founder Score* (1-100) con justificación basada en evidencia.

## Arquitectura

```
app.py (Streamlit UI)
   └── vcbrain/
        ├── config.py    → lee .env (sin credenciales en duro)
        ├── search.py    → SCOUT: Tavily (búsqueda limpia optimizada para IA)
        ├── llm.py       → motor cognitivo (OpenAI GPT-4o, registro de proveedores extensible)
        ├── judge.py     → JUDGE + SCORE: evaluación VC early-stage (JSON estricto)
        ├── connect.py   → CONNECT: outreach personalizado
        ├── pipeline.py  → orquestador Scout → Judge → Score
        └── models.py    → contrato de datos estable entre capas
```

**Desacoplado:** `llm.py` usa un registro de proveedores — hoy solo OpenAI (GPT-4o); agregar otro proveedor en el futuro no cambia la estructura de datos del resto del sistema.

## Setup

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar credenciales
copy .env.example .env      # (Windows) — luego edita .env con tus claves

# 3. Lanzar el dashboard
streamlit run app.py
```

## Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `OPENAI_API_KEY` | Clave de OpenAI (GPT-4o) |
| `TAVILY_API_KEY` | Clave de Tavily (capa de búsqueda) |
| `LLM_PROVIDER` | `openai` (default) |
| `OPENAI_MODEL` | Modelo (default: `gpt-4o`) |
| `TAVILY_MAX_RESULTS` | Resultados por consulta (default 8) |

## Flujo de uso

1. Escribe un sector/tecnología (p. ej. *"AI agents infrastructure"*).
2. Pulsa **Ejecutar** → Tavily recolecta evidencia limpia de la web.
3. El motor cognitivo identifica fundadores técnicos y les asigna un **Founder Score** justificado con URLs de evidencia.
4. La tabla muestra los resultados ordenados por score; en el detalle puedes generar el **outreach personalizado** listo para enviar.
