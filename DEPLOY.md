# Despliegue: backend + Postgres en Railway, frontend en Vercel

No puedo ejecutar estos pasos yo mismo — requieren tu cuenta de Railway y de
Vercel. Todo el código y los archivos de configuración ya están listos; esto
es la checklist para conectarlos.

## 0. Probar Postgres en local primero

1. Instala Postgres local (o usa Docker: `docker run --name vcbrain-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=vcbrain -p 5432:5432 -d postgres:16`).
2. En tu `.env`, agrega:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vcbrain
   ```
3. Corre el backend normal (`uvicorn api:app --reload --port 8000`). Al
   arrancar, `db.init_db()` crea las tablas solo (`scans`, `decisions`,
   `users`, `companies`) — no hace falta correr migraciones a mano.
4. Si dejas `DATABASE_URL` vacío, sigue usando SQLite local (`vcbrain.db`) sin
   tocar nada más — útil si todavía no tienes Postgres a la mano.

## 1. Backend + Postgres en Railway

1. Crea un proyecto nuevo en [railway.app](https://railway.app), conecta este
   repo (o `railway up` desde la CLI apuntando a la raíz del repo).
2. En el proyecto, **"+ New" → "Database" → "Add PostgreSQL"**. Railway
   provisiona el Postgres e inyecta `DATABASE_URL` automáticamente al
   servicio del backend — no hay que copiarla a mano.
3. En el servicio del backend, pestaña **Variables**, agrega el resto del
   `.env` (todo excepto `DATABASE_URL`, que ya la puso Railway):
   `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_SEARCH_MODEL`,
   `OPENAI_TRANSLATE_MODEL`, `SEARCH_MAX_RESULTS`, `MAX_SEARCH_COST_USD`,
   `VCBRAIN_ADMIN_USERNAME`, `VCBRAIN_ADMIN_PASSWORD`, `VCBRAIN_JWT_SECRET`
   (genera uno nuevo y largo, no reuses el de local), `GOOGLE_CLIENT_ID` (si
   ya lo tienes), `CORS_ORIGINS` (la URL de Vercel del paso 2 — puedes
   dejarla pendiente y volver a este paso después).
4. Railway detecta `requirements.txt` y usa Nixpacks automáticamente; el
   comando de arranque ya está en `railway.json`/`Procfile`
   (`uvicorn api:app --host 0.0.0.0 --port $PORT`) — no hay que configurar
   nada más ahí.
5. Deploy. Anota la URL pública que te da Railway
   (`https://tu-servicio.up.railway.app`) — la necesitas en el paso 2.

## 2. Frontend en Vercel

1. Crea un proyecto nuevo en [vercel.com](https://vercel.com), conecta este
   repo, y en **"Root Directory"** selecciona `frontend/`.
2. Abre `frontend/vercel.json` y reemplaza
   `REPLACE-WITH-YOUR-RAILWAY-URL.up.railway.app` con la URL real de Railway
   del paso 1 (commit + push para que Vercel la tome).
3. Deploy. Vercel construye con `npm run build` y sirve `dist/`; las
   llamadas del frontend a `/api/*` se reescriben hacia tu backend de
   Railway (así el código de `api.ts` no necesita saber la URL del backend).
4. Copia la URL que te da Vercel (`https://tu-app.vercel.app`) y vuelve al
   paso 1.3 para agregarla a `CORS_ORIGINS` en Railway (si no lo hiciste ya),
   y si usas login con Google, agrégala también en "Authorized JavaScript
   origins" del OAuth Client ID en Google Cloud Console.

## 3. Verificación

- `https://tu-servicio.up.railway.app/api/health` debe responder
  `{"ok": true, ...}`.
- `https://tu-app.vercel.app` debe cargar el login y, tras entrar, disparar
  el escaneo normalmente (revisa la consola del navegador si algo falla —
  casi siempre es `CORS_ORIGINS` sin la URL de Vercel, o el rewrite de
  `vercel.json` con la URL de Railway equivocada).

## Notas

- El límite de gasto por corrida (`MAX_SEARCH_COST_USD`, default $2) aplica
  igual en producción — cada persona que entre y dispare un escaneo gasta de
  la misma cuota de OpenAI.
- La tabla `companies` (deduplicación de startups ya monitoreadas) vive en el
  mismo Postgres — persiste entre corridas y entre deploys, a diferencia del
  SQLite local que se reinicia si el filesystem de donde corre no es
  persistente.
