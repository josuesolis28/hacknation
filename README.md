# 🧠 The VC Brain

An **instant-approval sourcing engine** for early-stage founders: it scans the
public web, evaluates every startup it finds against a fund's real
pre-seed due-diligence rubric, and — for the ones that qualify — issues a
$100,000 check automatically. No manual triage step in between.

Built for Maschmeyer Group Ventures' DACH thesis (Germany, Switzerland,
Austria), but the scoring engine, decision rules, and pipeline are
provider-agnostic and reusable for any fund thesis.

## How it works

1. **Scout** — OpenAI's `web_search` tool searches the web for founders and
   startups matching the fund's thesis (sector × region, plus community
   sources: LinkedIn, Reddit, Discord, Slack, Product Hunt).
2. **Judge** — a single structured-JSON call evaluates every candidate found
   against a weighted rubric (team, product, validation, market, moat) and
   extracts intake-form fields (company, email, section, round size, pitch,
   team, funding rounds, revenue signal) — only when there's real evidence,
   never fabricated.
3. **Decide** — any DACH startup scoring **70+** is qualified. Approved
   candidates get an automatically generated check; rejected ones get
   structured feedback on exactly what's missing to qualify.
4. **Dedup & merge** — every startup found is checked against everything the
   system has ever seen. A repeat match isn't re-created — its record is
   enriched with whatever new evidence this run found (team members,
   funding rounds, clients, etc.) instead of duplicating it.
5. **Tickets pipeline** — reviewed leads get filed into an Approved /
   Follow-up / Completed / Rejected board, so a yellow (potential) lead can
   be tracked through a human review process instead of just sitting in a
   list.
6. **Connect** — on demand, generates a personalized outreach message citing
   concrete evidence already collected.

Every run has a hard cost ceiling (`MAX_SEARCH_COST_USD`, default $2): once a
scan gets close to the limit, it stops launching new search queries instead
of running unbounded.

## Architecture

```
frontend/                React + TypeScript (Vite)
  src/
    App.tsx               workspace shell, scan lifecycle, persisted state
    components/
      FounderCard.tsx      startup tile + detail modal + check/tickets actions
      AnalysisPhases.tsx   simulated progress bar + phase stepper
      TicketsBoard.tsx     approved/follow-up/completed/rejected board
      AnalyzedArchive.tsx  full history of every startup ever found
      Login.tsx            username/password + "Sign in with Google"
    hooks/useTranslatedFounder.ts   batched on-demand EN/ES/DE translation

api.py                    FastAPI app — all HTTP endpoints
vcbrain/
  config.py                reads .env, single source of truth for settings
  search.py                Scout: parallel OpenAI web_search calls
  judge.py                 Judge/Score: structured extraction + rubric
  decision.py              traffic light + instant approval + $100k check
  pipeline.py              orchestrates Scout → Judge → Decide → Dedup
  db.py                    Postgres (prod) / SQLite (local) — same functions
  cost.py                  per-run token/cost tracking and budget cutoff
  auth.py                  JWT bearer auth + Google ID token verification
  translation.py           cached LLM translation (EN/ES/DE)
  llm.py                   provider-agnostic `complete()` used by every layer
  models.py                dataclasses shared end-to-end (mirrors types.ts)
```

**Data contract is provider-agnostic.** `llm.py` exposes a single
`complete(system, user) -> (text, provider)` backed by a provider registry;
today only OpenAI is registered, but nothing downstream depends on that.

## Local setup

```bash
# Backend
pip install -r requirements.txt
copy .env.example .env      # Windows — then fill in your keys
uvicorn api:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                  # http://localhost:5173, proxies /api → :8000
```

Default local login: `admin12345` / `admin12345` (override via
`VCBRAIN_ADMIN_USERNAME` / `VCBRAIN_ADMIN_PASSWORD`). Opening the app runs
the full DACH scan automatically.

## Environment variables (`.env`)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | yes | OpenAI key — powers Scout, Judge, and translation |
| `OPENAI_MODEL` | | Judge/extraction model (default `gpt-4o`) |
| `OPENAI_SEARCH_MODEL` | | Scout model, must support `web_search` (default `gpt-4o`) |
| `OPENAI_TRANSLATE_MODEL` | | Cheap model for on-demand translation (default `gpt-5.4-mini`) |
| `SEARCH_MAX_RESULTS` | | Sources requested per search query (default 8) |
| `SEARCH_CONCURRENCY` | | Parallel search queries (default 8) |
| `MAX_SEARCH_COST_USD` | | Hard budget per scan; stops new queries once reached (default 2.0) |
| `DATABASE_URL` | | Postgres connection string. Empty = falls back to local SQLite |
| `CORS_ORIGINS` | | Comma-separated allowed origins (add your Vercel URL in prod) |
| `VCBRAIN_ADMIN_USERNAME` / `_PASSWORD` | | Local login credentials |
| `VCBRAIN_JWT_SECRET` | | JWT signing secret — set a long random value in production |
| `VCBRAIN_JWT_TTL_SECONDS` | | Session length in seconds (default 28800 = 8h) |
| `GOOGLE_CLIENT_ID` | | Enables the "Sign in with Google" button when set |
| `VCBRAIN_DEFAULT_LANGUAGE` | | UI default: `en` \| `es` \| `de` |

## Deployment

Backend + Postgres on Railway, frontend on Vercel. Full step-by-step
checklist in **[DEPLOY.md](DEPLOY.md)** — config files (`Procfile`,
`railway.json`, `frontend/vercel.json`) are already in the repo.

## License

All rights reserved — see [LICENSE](LICENSE).
