# Onboarding plan UI

Single-route Vite + React + TypeScript app for the **Automated Employee Onboarding Workflow**. It wraps the existing CLI/API core (`src/onboarding/`) and is **not** the Critical Research Workflow prototype in `src/frontend/`.

Contract: [`../../project-context/1.define/onboarding-backend-spec.md`](../../project-context/1.define/onboarding-backend-spec.md). Environment and repo layout: [`../../project-context/2.build/setup.md`](../../project-context/2.build/setup.md).

## Need

- Node.js LTS (18+) and npm
- Python 3.12 recommended (project `.venv`) with the onboarding package installed
- Both processes below must run at the same time

## 1. Start the FastAPI backend

From the **repo root** (`aamad-project/`):

```text
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn onboarding.api:app --host 127.0.0.1 --port 8000
```

API: [http://127.0.0.1:8000](http://127.0.0.1:8000)

`OPENAI_API_KEY` is optional. If unset, the server uses the catalog stubs (OQ-13) and still returns a Developer plan.

## 2. Start this UI

From `src/onboarding-ui/`:

```text
npm install
npm run dev
```

Open [http://localhost:5174/](http://localhost:5174/). Port **5174** is pinned so it does not collide with the research app on **5173**.

Vite proxies `/runs` to `http://127.0.0.1:8000`. To call the API without the proxy, set `VITE_API_BASE=http://127.0.0.1:8000` before `npm run dev`.

| Script | What it does |
| ------ | ------------ |
| `npm run dev` | Vite dev server with HMR on port 5174 |
| `npm run build` | Typecheck (`tsc -b`) then production bundle |
| `npm run preview` | Serve the production bundle locally |

This app does not read `OPENAI_API_KEY`. Do not add keys to the frontend.

## What to enter

Happy path (Developer catalog):

- Role: `Developer`
- Department: `AI Engineering`
- Start date: `2026-09-01`

Other canonical roles stay on the form and show **not yet supported** (no `POST /runs`). That matches the backend’s Developer-only catalog.

## Boundary

```text
Browser (src/onboarding-ui/)
  Run / Retry
    → POST /runs          → onboarding.api → run_onboarding
    → GET /runs/{runId}   → poll every 2s until done | error (60s timeout)
  Reset
    → local FSM only (stops polling; no backend cancel)
```
