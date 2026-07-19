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

# 3. Arrancar la API
uvicorn api:app --reload --port 8000

# 4. En otra terminal, arrancar el frontend
cd frontend
npm install
npm run dev
```

## Sourcing automático MVP DACH

Al abrir el frontend, el Scout inicia automáticamente la tesis **DACH**:
solo startups **based in Germany, Switzerland or Austria**. Clasifica en las
secciones del formulario (HealthTech & MedTech, FinTech & InsurTech, Food &
AgTech, Logistics & Supply Chain, HR Tech, LegalTech & RegTech, Retail &
E-Commerce, EdTech, CleanTech & Energy, PropTech & Construction, Cybersecurity)
y busca campos de intake: nombre de empresa, email de negocio, origen,
resumen de actividad, tamaño de ronda (`< EUR 1 mio` … `> EUR 5 mio`), pitch
y otra información pública.

```bash
curl -X POST "http://localhost:8000/api/scout/maschmeyer?max_results=3" \
  -H "Authorization: Bearer <token>"
```

La búsqueda usa fuentes EU/DACH (EU-Startups, German Accelerator, Venture Kick,
HTGF, etc.). Email y tamaño de ronda solo se rellenan si aparecen en fuentes
públicas (no se inventan).

## Acceso B2B y perfiles

La interfaz solicita inicio de sesión antes de consultar cualquier dato de
scouting. Para el entorno local inicial usa `admin12345` / `admin12345`; cambia
`VCBRAIN_ADMIN_PASSWORD` y `VCBRAIN_JWT_SECRET` en `.env` antes de desplegar.

El selector de idioma (EN / ES / DE) se guarda en el navegador y también puede
definirse con `VCBRAIN_DEFAULT_LANGUAGE`. Cada presentación muestra origen
DACH (DE / CH / AT), sección del formulario, email de negocio y tamaño de
ronda cuando hay evidencia pública.

El botón **Analizar nodos de perfil y fuentes** construye una red de fundador,
CTO y ejecutivos mediante resultados públicos indexados y muestra citas con
enlaces verificables. No inicia sesión ni extrae contenido privado de
LinkedIn, Instagram o X. Las traducciones dinámicas al inglés y alemán se
realizan con el LLM una sola vez por texto e idioma durante la ejecución y se
reutilizan desde caché.

## Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `OPENAI_API_KEY` | Clave de OpenAI (GPT-4o) |
| `TAVILY_API_KEY` | Clave de Tavily (capa de búsqueda) |
| `LLM_PROVIDER` | `openai` (default) |
| `OPENAI_MODEL` | Modelo (default: `gpt-4o`) |
| `TAVILY_MAX_RESULTS` | Resultados por consulta (default 8) |
| `VCBRAIN_ADMIN_USERNAME` | Usuario local (default `admin12345`) |
| `VCBRAIN_ADMIN_PASSWORD` | Contraseña local (default `admin12345`) |
| `VCBRAIN_DEFAULT_LANGUAGE` | Idioma UI: `en` \| `es` \| `de` (default `en`) |

## Flujo de uso

1. Escribe un sector/tecnología (p. ej. *"AI agents infrastructure"*).
2. Pulsa **Ejecutar** → Tavily recolecta evidencia limpia de la web.
3. El motor cognitivo identifica fundadores técnicos y les asigna un **Founder Score** justificado con URLs de evidencia.
4. La tabla muestra los resultados ordenados por score; en el detalle puedes generar el **outreach personalizado** listo para enviar.
