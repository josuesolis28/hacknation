# VC Brain - Registro de proceso

## 2026-07-18 - Semáforo visible, equipo, capital/fondos y doc técnica

- Bug "token inválido o expirado": causa raíz confirmada — un proceso backend viejo (sin JWT ni /health completo) seguía escuchando en el puerto 8000 desde una sesión previa; el fix de secreto JWT estable (`.vcbrain_jwt_secret`, ya presente en config.py) funciona correctamente una vez el proceso correcto corre. Se añadió `.vcbrain_jwt_secret` y `node_modules/`/`dist/` a `.gitignore`.
- Semáforo (`traffic_light`) ya calculado en backend (`decision.py`) pero no se mostraba en UI: se agregó badge verde/amarillo/rojo en la cabecera de `FounderCard.tsx` con tooltip explicando el criterio.
- Equipo (founders/cofounders/ejecutivos/advisors) ya modelado en backend (`team: TeamMember[]`) pero no renderizado: se agregó sección "Founders & cofounders" en `FounderCard.tsx` con rol, relación, skills y perfil.
- Redes sociales (LinkedIn/Instagram/website) ya funcionando en `ProfileNetworkView` (panel derecho) — validado, sin cambios necesarios.
- Capital total, fondos participantes y clientes/revenue ya modelados en backend (`total_capital`, `funding_rounds[]`, `revenue_signal`, `clients[]`) pero ausentes en `StartupMetrics.tsx`: se agregó sección "Capital & funds" con tabla de inversionistas/montos/fechas y chips de clientes.
- `types.ts` actualizado para reflejar `traffic_light`, `team`, `total_capital`, `funding_rounds`, `revenue_signal` (antes ausentes, causaban que el frontend ignorara datos ya calculados por el backend).
- Documentación técnica de infraestructura en inglés para presentación ante panelistas: `docs/TECHNICAL_OVERVIEW.md` (arquitectura, pipeline, modelo de datos, seguridad, stack, cómo correrlo).
- Archivos clave: `frontend/src/{types,i18n}.ts`, `FounderCard.tsx`, `StartupMetrics.tsx`, `styles.css`, `.gitignore`, `docs/TECHNICAL_OVERVIEW.md`.

### Validación

- `npx tsc --noEmit` sin errores.
- Backend y frontend reiniciados limpios; `/api/health` devuelve `default_language`/`languages`; login con `admin12345/admin12345` emite JWT válido tras persistir `.vcbrain_jwt_secret`.
- Pendiente: corrida live completa del pipeline Maschmeyer (`/api/scout/maschmeyer`) para confirmar que `traffic_light`, `team` y `funding_rounds` llegan poblados con datos reales de Tavily/GPT-4o.


## 2026-07-18 - MVP DACH (formulario de intake)

- Ámbito obligatorio: startups based in Germany, Switzerland o Austria; el judge filtra fuera de DE/CH/AT.
- Secciones del formulario: HealthTech & MedTech, FinTech & InsurTech, Food & AgTech, Logistics & Supply Chain, HR Tech, LegalTech & RegTech, Retail & E-Commerce, EdTech, CleanTech & Energy, PropTech & Construction, Cybersecurity.
- Campos de intake: company, business_email, origin, activity_summary, round_size (`< EUR 1 mio` … `> EUR 5 mio`), pitch, other_info.
- UI: tarjetas con sección / ronda / email; panel inferior alineado al formulario.
- Archivos: `vcbrain/thesis.py`, `judge.py`, `models.py`, `frontend/src/{App,types,i18n}.ts`, `FounderCard.tsx`, `StartupMetrics.tsx`, `README.md`.

### Validación

- Import Python y normalización section/round/email OK.
- Pendiente: corrida live Tavily/LLM sobre queries DACH.

## 2026-07-18 - Presentación de startups (perfiles / redes / capital + Tec)

- Layout de presentación: izquierda perfiles con cuadros de rol, área y habilidades; derecha redes sociales públicas (LinkedIn, Instagram, X, etc.) más nodos de equipo; abajo capital levantado, modelo B2B/B2C, clientes e impacto para outreach a fondos.
- Modelo enriquecido con `skills`, `area`, `social_links`, `capital_*`, `clients`, `business_model`, `impact_*`, `incubation_program`, `tec_related`.
- Scout incluye fuentes Tec de Monterrey / ITESM / incubación Tec; badge Tec cuando hay evidencia explícita.
- Archivos clave: `vcbrain/models.py`, `judge.py`, `profiles.py`, `thesis.py`, `frontend/src/App.tsx`, `FounderCard.tsx`, `ProfileNetwork.tsx`, `StartupMetrics.tsx`, `types.ts`, `i18n.ts`, `styles.css`.

### Validación

- Import de módulos Python (`vcbrain.models`, `judge`, `profiles`, `thesis`) OK.
- Pendiente: corrida live del scout con Tavily/LLM y smoke UI autenticada.

## 2026-07-18 - Cuenta de prueba, i18n y origen de país

- Cuenta local por defecto: usuario y contraseña de desarrollo configurables (ver `.env.example`).
- UI configurable en inglés, español y alemán (selector + `VCBRAIN_DEFAULT_LANGUAGE` + persistencia en navegador).
- Las presentaciones de fundadores incluyen origen de país/región con normalización hacia EE. UU. y Alemania cuando hay evidencia.
- Archivos clave: `vcbrain/config.py`, `vcbrain/judge.py`, `vcbrain/models.py`, `vcbrain/thesis.py`, `api.py`, `frontend/src/i18n.ts`, `Login.tsx`, `FounderCard.tsx`.

### Validación

- Módulos Python importables tras recuperación de disco lleno.
- Pendiente: reinstalar `frontend/node_modules` y probar login en UI.

## 2026-07-18 - Seguridad, perfiles y operación internacional

- Se añadió acceso B2B con JWT, expiración, comparación de credenciales en tiempo constante y limitación de intentos de inicio de sesión.
- Se protegieron scouting, outreach, análisis de perfiles y traducción.
- Se incorporó análisis de nodos mediante evidencia pública indexada; las citas conservan título y URL verificable.
- Se preparó soporte español, inglés y alemán, con traducción por IA almacenada en caché de proceso.
- Pendiente: sustituir las credenciales locales iniciales y el secreto JWT por un proveedor de identidad y secretos administrados antes de producción.

### Validación

- Compilación de TypeScript/Vite y compilación de módulos Python correctas.
- Rutas de inteligencia devuelven `401` sin token; el login local emite JWT y un JWT válido supera la capa de autorización.
- Se validó el agente global `iteration-documenter` con el validador de skills.
