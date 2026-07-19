# The VC Brain — Technical Infrastructure Overview

**Prepared for:** Maschmeyer Group Ventures — panel / judges presentation
**System:** Automated instant-approval pipeline for pre-seed founder & startup sourcing (DACH MVP: Germany, Switzerland, Austria)
**Status:** Working local MVP, end-to-end validated

---

## 1. Mission

The VC Brain automates the earliest stage of venture sourcing — the equivalent of an "instant credit-card approval" system, but for pre-seed capital:

1. **Scout** — continuously discover technical founders and startups on the public web.
2. **Judge** — evaluate them against the fund's real investment thesis and due-diligence rubric.
3. **Score** — produce a weighted, evidence-backed Founder Score (0–100).
4. **Decide** — apply hard eligibility gates plus the score threshold; if the candidate passes, **automatically issue a $100,000 USD check**. If not, the system **never simply disappears the candidate** — it returns structured, actionable feedback describing exactly what is missing and how to improve.
5. **Connect** — generate a personalized, evidence-grounded outreach message ready to send.

Every claim the system makes is traceable to a public URL. Nothing is invented; low or missing evidence is reflected as a low score and an unmet gate, not as a fabricated fact.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Browser (React + TS)                         │
│  Login → Workspace (candidate list · team roster · social network    │
│  panel · capital/funding board) — all state driven by one pipeline   │
│  response, served through Vite's dev proxy at /api/*                 │
└───────────────────────────────┬────────────────────────────────────-┘
                                 │ HTTPS/JSON, Bearer JWT
┌───────────────────────────────▼──────────────────────────────────────┐
│                     FastAPI backend  (api.py)                        │
│  /api/auth/login   /api/scout   /api/scout/maschmeyer                │
│  /api/outreach     /api/profiles/analyze   /api/translate            │
└───────┬───────────────┬───────────────┬───────────────┬─────────────┘
        │               │               │               │
        ▼               ▼               ▼               ▼
  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌──────────────┐
  │  auth.py  │   │ pipeline  │   │ profiles  │   │ translation  │
  │  JWT/HMAC │   │  .py      │   │  .py      │   │  .py         │
  └───────────┘   └─────┬─────┘   └─────┬─────┘   └──────┬───────┘
                         │               │                │
        ┌────────────────┼───────────────┴────────────────┘
        ▼                ▼
  ┌───────────┐   ┌──────────────┐        ┌────────────────────┐
  │ search.py │   │  judge.py    │        │   decision.py       │
  │ (Scout)   │──▶│ (Judge/Score)│───────▶│ (traffic light +    │
  │ Tavily API│   │  GPT-4o      │        │  gates + $100K check)│
  └───────────┘   └──────────────┘        └────────────────────┘
        │                │                          │
        ▼                ▼                          ▼
  Tavily Search API   OpenAI API              connect.py (outreach)
  (clean, AI-ready     (GPT-4o structured
   web text)            JSON evaluation)
```

**Data contract is provider-agnostic.** The `llm.py` module exposes a single `complete(system, user) -> (text, provider)` function backed by a provider registry (`_PROVIDERS`). Today only OpenAI (GPT-4o) is registered; adding a second model provider is a one-function addition and changes nothing downstream — every consumer (`judge.py`, `connect.py`, `profiles.py`, `translation.py`) only depends on the `complete()` contract, not on a specific vendor SDK.

---

## 3. Pipeline Stages (Detail)

### 3.1 Scout — `vcbrain/search.py` + `vcbrain/thesis.py`

- Uses the **Tavily Search API**, which returns pre-cleaned, LLM-ready web text (no HTML/ad noise), instead of a generic search API that would require our own scraping and cleaning layer.
- Two entry points:
  - `scout(query)` — ad-hoc search for a manually entered sector/technology.
  - `scout_maschmeyer()` — runs the fund's **entire investment thesis** automatically: one query per (section × DACH country) combination, so no single vertical or geography dominates the result set.
- The thesis (`thesis.py`) encodes the fund's real intake form: 11 fixed sections (HealthTech & MedTech, FinTech & InsurTech, Food & AgTech, Logistics & Supply Chain, HR Tech, LegalTech & RegTech, Retail & E-Commerce, EdTech, CleanTech & Energy, PropTech & Construction, Cybersecurity), a mandatory geography gate (Germany / Switzerland / Austria), and the round-size buckets used by the fund's paperwork (`< EUR 1 mio` … `> EUR 5 mio`).
- Results are deduplicated by URL and ranked by Tavily's relevance score before being handed to the Judge.

### 3.2 Judge + Score — `vcbrain/judge.py`

- A single structured-JSON prompt sent to GPT-4o evaluates **every named founder/startup** found in the sourced evidence against a **weighted pre-seed due-diligence rubric**, derived from standard early-stage VC criteria (team/founder-market fit, product, problem validation, market size, moat):

  | Criterion | Weight | What is scored |
  |---|---|---|
  | Team | 30% | Founder-market fit, complementary skill sets, track record |
  | Product | 25% | MVP/demo/repo depth, technical execution |
  | Validation | 20% | Customer traction, validated demand |
  | Market | 15% | Market size and timing |
  | Moat | 10% | Defensible differentiation |

- **The arithmetic is never delegated to the LLM.** The model only returns a 0–100 score per criterion with a rationale; `judge.py` computes the final weighted `founder_score` in Python, guaranteeing the math is deterministic and auditable.
- In parallel, the model extracts structured intake fields with **zero fabrication tolerance**: company, business email, country/region, section, activity summary, round size, pitch, social links, founding team, funding rounds, total capital raised, and revenue signal — all only when explicit evidence is present; anything unverifiable is left empty rather than guessed.
- A normalization layer (`_normalize_section`, `_normalize_round`, `_normalize_email`, `_normalize_origin`) reconciles model output against the fund's controlled vocabularies (exact section names, exact round buckets, DE/CH/AT country codes), so downstream UI and filters never see free-text drift.

### 3.3 Decide — `vcbrain/decision.py`

Two outputs per candidate:

**A. Eligibility traffic light** (`traffic_light: green | yellow | red`)

| Light | Meaning | Rule |
|---|---|---|
| 🟢 Green | Candidate — investment-ready | Based in DACH **and** all hard gates met **and** score ≥ 70 |
| 🟡 Yellow | Potential — not yet qualified | Based in DACH **and** score ≥ 45 with partial gate coverage, or a recognized section fit |
| 🔴 Red | Does not qualify | Outside DACH, or score/gates too low |

**B. Instant decision** — `approved` only when the traffic light is green **and** every hard gate is met **and** the score clears the 70-point threshold:

- **Hard gates** (`GATES` in `judge.py`): based in Germany/Switzerland/Austria, fits one of the 11 intake sections, has an identifiable technical founder, is genuinely early-stage, has a tangible product built, and has a validated problem/demand signal.
- **Approved →** a `Check` object is generated automatically: unique ID (`MGV-<year>-<hex>`), `$100,000 USD`, payee, company, issuing fund, ISO date, status `issued`. Rendered in the UI as a bank-check component.
- **Rejected →** the candidate is never dropped silently. `decision.py` composes structured feedback: which score gap exists, which specific gates failed and why (with the model's own `detail` string), so the founder/analyst knows exactly what to fix to re-qualify on a future pass.

### 3.4 Connect — `vcbrain/connect.py`

- On demand, generates a ≤120-word personalized outreach message citing 1–2 concrete facts from the evidence already collected, closing with a clear call to a 20-minute call — never a generic template.

### 3.5 Profile enrichment — `vcbrain/profiles.py`

- A secondary, cached (`lru_cache`) Tavily + LLM pass builds a **public-evidence-only** network graph around a selected candidate: team nodes (founder/executive/advisor) with role, skills, and area, plus verified social links (LinkedIn, Instagram, X, website, GitHub, Crunchbase) — never inferred, only URLs that literally appear in the sourced material. No private data, no login, no scraping of authenticated content.

### 3.6 Translation — `vcbrain/translation.py`

- Every founder's justification text can be translated on demand (EN/ES/DE) through the same LLM contract, cached per (text, language) pair to avoid repeat API calls.

---

## 4. Data Model (`vcbrain/models.py`)

`FounderProfile` is the single, stable contract shared by every layer and serialized directly to the frontend:

- **Scoring:** `founder_score`, `criteria[]` (weighted breakdown), `requirements[]` (gates), `traffic_light`, `decision`, `feedback[]`, `check`.
- **Identity & origin:** `name`, `company`, `role`, `country`, `country_code`, `origin_region`, `origin_confidence`.
- **Team:** `team[]` — each `TeamMember` has `name`, `role`, `relationship` (founder/cofounder/executive/advisor), `skills[]`, `area`, `profile_url`.
- **Public network:** `social_links[]` — each `SocialLink` has `platform`, `url`, `label`.
- **Capital & traction:** `total_capital`, `capital_raised`, `capital_note`, `funding_rounds[]` (`FundingRound`: investor, amount, round name, date), `revenue_signal`, `clients[]`, `business_model`.
- **Intake-form fields:** `business_email`, `section`, `activity_summary`, `round_size`, `pitch`, `other_info`.

`PipelineResult` wraps a full run: the query used, which LLM provider actually answered, the list of scored `FounderProfile`s, the raw Tavily hits (for transparency/audit), and any partial errors (a single failed sub-query never aborts the whole run).

---

## 5. Security & Access Control

- **Authentication:** stateless JWT-style bearer tokens (`vcbrain/auth.py`), HMAC-SHA256 signed, no external auth dependency for the MVP.
- **Stable signing secret:** the JWT secret is persisted to a local, git-ignored file (`.vcbrain_jwt_secret`) so that restarting the backend (or `--reload` picking up a code change) never invalidates sessions already open in a browser — this was an early MVP bug (*"token inválido o expirado"*) that is now fixed at the root: no more secret regenerated on every process start.
- **Brute-force protection:** login attempts are rate-limited per client IP (5 attempts / 5-minute window) using constant-time credential comparison (`secrets.compare_digest`) to avoid timing attacks.
- **Protected surface:** every business endpoint (`/api/scout*`, `/api/outreach`, `/api/profiles/analyze`, `/api/translate`) requires a valid bearer token via a FastAPI `Depends(current_user)` guard.
- **Secrets hygiene:** all API keys (OpenAI, Tavily) are read exclusively from environment variables (`.env`, git-ignored); nothing is hardcoded in source. `.gitignore` also excludes the JWT secret file, `node_modules`, and build output.
- **CORS:** locked to the known local frontend origin (`http://localhost:5173`) — not a wildcard.

> Production note: local admin credentials and the local JWT secret are placeholders for the MVP/demo and are designed to be swapped for a managed identity provider and secret manager before any real deployment — the `current_user` dependency is the single seam where that swap happens.

---

## 6. Frontend Architecture

- **Stack:** React 18 + TypeScript 5, built and served by Vite (dev server proxies `/api/*` to the FastAPI backend on port 8000, eliminating CORS friction in local development).
- **State model:** a single `PipelineResult` fetched once per run drives the whole workspace — no external state library needed at this scale; component-local `useState`/`useEffect` is sufficient and keeps the codebase easy to reason about.
- **Layout (per candidate, three panels):**
  - **Left — Candidate list (`FounderCard.tsx`):** score badge, traffic-light pill, founding **team roster** (founders/cofounders/executives/advisors with role and skills), weighted criteria bars, gate checklist, evidence links, the issued check or the rejection feedback, and on-demand outreach generation.
  - **Right — Public network (`ProfileNetwork.tsx`):** merged social links (LinkedIn/Instagram/X/website/GitHub) from both the initial scout pass and the on-demand deep profile analysis, plus team nodes and source citations.
  - **Bottom — Capital & funds (`StartupMetrics.tsx`):** intake-form fields (company, business email, section, round size, pitch), **total capital raised**, **participating funds/investors table** (investor, round name, amount, date), **revenue/traction signal**, and **named clients**.
- **Internationalization:** full EN/ES/DE dictionary (`i18n.ts`) with browser-persisted language selection; founder justifications are translated on demand through the backend LLM contract.
- **Type safety:** the TypeScript interfaces in `types.ts` mirror the Python dataclasses in `models.py` field-for-field, so a backend schema change surfaces as a compile error in the frontend rather than a silent runtime `undefined`.

---

## 7. Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript 5, Vite 5 |
| Backend | Python 3, FastAPI, Uvicorn (ASGI) |
| Cognitive engine | OpenAI GPT-4o (pluggable provider registry) |
| Web intelligence | Tavily Search API |
| Auth | Custom HMAC-SHA256 JWT-style bearer tokens |
| Config | `.env` via `python-dotenv`, zero hardcoded secrets |
| Data contract | Python `dataclasses` ⇄ TypeScript `interfaces`, JSON over REST |

---

## 8. Running the System Locally

```bash
# Backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev            # http://localhost:5173, proxies /api → :8000
```

Required `.env` variables: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-4o`. Local demo login defaults to `admin12345` / `admin12345` (override via `VCBRAIN_ADMIN_USERNAME` / `VCBRAIN_ADMIN_PASSWORD`).

---

## 9. Design Principles Applied

1. **Evidence over inference.** Every field the LLM returns is either backed by a cited URL or left empty — the system is explicitly instructed not to fabricate emails, funding amounts, or team members.
2. **Deterministic scoring.** The LLM scores each rubric criterion; the weighted sum and the approve/reject decision are computed in plain Python, not by the model — auditable and reproducible.
3. **No silent rejection.** A candidate that doesn't qualify always receives structured, specific feedback — the product goal of "no application simply disappears" is enforced in code, not just in copy.
4. **Provider independence.** The cognitive layer is a registry, not a hardcoded vendor call — swapping or adding a model provider never touches the Judge, Decision, or Connect logic.
5. **Fail-soft pipeline.** A single failed sub-query (Scout) or malformed model entry (Judge) is skipped and logged, never aborting the full run for the other candidates.

---

## 10. Current Scope & Roadmap

**In scope today:** DACH-region pre-seed sourcing MVP, single-fund thesis, local JWT auth, OpenAI-only cognitive engine, on-demand profile/network enrichment, EN/ES/DE UI.

**Natural next steps:** real outreach delivery (email/LinkedIn API instead of copy-ready text), persistent storage of pipeline runs (currently in-memory per request) for historical deal-flow tracking, managed identity provider for auth, and a second LLM provider registered as an automatic fallback for resilience.
