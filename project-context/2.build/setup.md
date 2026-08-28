# Setup — Automated Employee Onboarding Workflow

**Persona:** `project-mgr`  
**Actions:** `setup-project`, `configure-env`, `document-setup`  
**Phase:** Build  
**Intended path:** `project-context/2.build/setup.md`  
**Product:** Automated Employee Onboarding Workflow  
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (environment unset; `aamad.config.yml` `runtime.target: crewai`)  
**Status:** Application code consolidated under `src/`

---

## Purpose

Record the repository layout, installed dependencies, and environment contract so `@backend.eng`, `@frontend.eng`, `@integration.eng`, `@qa.eng`, `@security.eng`, and `@devops.eng` can work from a single source tree.

This artifact does not add product logic. It documents a folder restructure: all application code lives under `src/`.

---

## Directory layout

SAD §4.1 recommends a `src/` application tree. The implemented layout keeps that contract and places both Vite apps under `src/` as well (operator request 2026-08-28). Python remains a src-layout package (`pyproject.toml` `package-dir = src`). Vite apps are excluded from the Python package finder via `include = ["onboarding*"]`.

```text
aamad-project/
├── config/                         # CrewAI agents.yaml, tasks.yaml
├── src/
│   ├── onboarding/                 # Python package (CLI, API, catalog, crew, compliance)
│   │   ├── cli.py                  # onboard entrypoint (SD-6)
│   │   ├── api.py                  # FastAPI wrap of run_onboarding
│   │   ├── catalog.py
│   │   ├── models.py
│   │   ├── compliance.py
│   │   ├── workflow.py
│   │   ├── rendering.py
│   │   ├── crew_runtime.py
│   │   └── stubs.py
│   ├── onboarding-ui/              # Onboarding Vite + React UI (port 5174)
│   └── frontend/                   # Critical Research Workflow prototype (port 5173)
├── tests/                          # Python unit and integration tests (repo root)
├── project-context/
│   ├── 1.define/
│   └── 2.build/
│       ├── setup.md                # this file
│       ├── developer-tasks.yaml
│       └── task_catalog/
├── pyproject.toml
├── .env.example
└── aamad.config.yml
```

**Not moved:** `tests/` stays at repo root (SAD §4.1). `config/` stays at repo root (CrewAI adapter). `project-context/` stays at repo root (AAMAD artifacts). Task catalog YAML remains under `project-context/2.build/` (current loader default), not `config/task_catalog/` (SAD recommended path; see Open Questions).

**SAD §4.1 nested packages** (`src/cli/`, `src/adapters/`, `src/catalog/`, …) are not used. The Python package is `src/onboarding/` with a flat module set. Exact paths are an implementation detail per SAD §4.1.

---

## Prerequisites

| Tool | Version | Notes |
| ---- | ------- | ----- |
| Python | 3.11+ (3.12 used locally) | `requires-python = ">=3.11"`; CrewAI extra is skipped on 3.14 |
| Node.js | LTS 18+ | Both Vite apps |
| npm | bundled with Node | `src/onboarding-ui/` and `src/frontend/` |

Local virtualenv: `.venv/` (gitignored).

---

## Dependencies

Declared in `pyproject.toml`. Install from repo root:

```text
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip install -e ".[crew]"
```

| Extra | Packages | When |
| ----- | -------- | ---- |
| (default) | click, fastapi, pydantic, pyyaml, uvicorn | CLI + HTTP API |
| `dev` | pytest, httpx | Tests |
| `crew` | crewai>=0.80.0 (Python < 3.14) | Live Role Analyst / Plan Builder |

UI apps (from their directories under `src/`):

```text
cd src/onboarding-ui
npm install

cd src/frontend
npm install
```

| App | Port | Stack |
| --- | ---- | ----- |
| `src/onboarding-ui` | 5174 | Vite, React, TypeScript, react-markdown |
| `src/frontend` | 5173 | Vite, React, TypeScript, Playwright e2e |

---

## Environment variables

Source of names: `.env.example`. Never commit secret values.

| Name | Required | Use |
| ---- | -------- | --- |
| `OPENAI_API_KEY` | For live CrewAI (SD-1) | Server-side only. If unset, API/CLI use catalog stubs (SAD OQ-13) |
| `GEMINI_API_KEY` | Alternative provider | Used only when `OPENAI_API_KEY` is blank |
| `ONBOARDING_OUTPUT_DIR` | No | CLI output directory override (SAD SD-3); default `./output/` |
| `VITE_API_BASE` | No | Onboarding UI: call API without the Vite `/runs` proxy |

Copy `.env.example` to `.env` and fill keys locally. `load_project_dotenv()` in `src/onboarding/crew_runtime.py` reads repo-root `.env`.

---

## Local run

**CLI** (from repo root, after editable install):

```text
onboard --role "Developer" --department "AI Engineering" --start-date "2026-09-01"
```

**Onboarding UI + API:**

```text
.\.venv\Scripts\python.exe -m uvicorn onboarding.api:app --host 127.0.0.1 --port 8000
cd src/onboarding-ui
npm run dev
```

UI: http://localhost:5174/ — API: http://127.0.0.1:8000

**Research prototype (not the onboarding product):**

```text
cd src/frontend
npm run dev
```

UI: http://localhost:5173/

**Tests:**

```text
.\.venv\Scripts\python.exe -m pytest tests
```

---

## Next for downstream agents

| Persona | Next |
| ------- | ---- |
| `@backend.eng` | Document existing `src/onboarding/` in `backend.md`. Do not invent catalog tasks. Optional: split the flat package toward SAD §4.1 nested modules only if that does not change behavior. |
| `@frontend.eng` | Document `src/onboarding-ui/` in `frontend.md`. Keep `src/frontend/` as the separate Critical Research Workflow prototype. |
| `@integration.eng` | Confirm Vite proxy `/runs` → `127.0.0.1:8000` still holds after the move; record in `integration.md`. |
| `@qa.eng` | Re-run `pytest tests` and onboarding-ui happy path from `src/onboarding-ui/`. Playwright for the research app is `src/frontend/` (`npm run test:e2e`). |
| `@security.eng` | Assess secrets handling (`.env` / `.env.example`) and UI/API CORS origins after the path change. |
| `@devops.eng` | Wait for `qa.md` (and `security.md` if required). Point start commands at `src/onboarding-ui` and `uvicorn onboarding.api:app`. |

---

## Sources

| Source | Path | Use |
| ------ | ---- | --- |
| PRD | `project-context/1.define/prd.md` | CLI MVP, FR-001–FR-016 |
| SAD | `project-context/1.define/sad.md` | §4.1 `src/` scaffold; SD-1, SD-3, SD-6, SD-10 |
| Config | `aamad.config.yml` | `runtime.target: crewai`, Python, testing/security gates |
| CrewAI adapter | `.cursor/rules/adapter-crewai.mdc` | YAML under `config/`, env secrets |
| Package manifest | `pyproject.toml` | Dependencies and src-layout |
| Env template | `.env.example` | Secret names only |
| Onboarding API spec | `project-context/1.define/onboarding-backend-spec.md` | HTTP wrap; UI at `src/onboarding-ui/` |

---

## Assumptions

| ID | Assumption | Impact if wrong |
| -- | ---------- | --------------- |
| SU-1 | Operator request “code under src folder” means all application code (Python package + both Vite apps), not a rewrite into SAD’s nested `src/cli` / `src/catalog` packages | Nested split would be `@backend.eng` work |
| SU-2 | `tests/` stays at repo root | Pytest collection paths stay `tests/` |
| SU-3 | `catalog.py` and `crew_runtime.py` resolve repo root as `Path(__file__).parents[2]` (`src/onboarding/*.py` → repo root) | Still valid after this move |
| SU-4 | Python 3.12 local venv satisfies SAD SA-3 (3.11+) | Recorded here; not pinned in CI yet |
| SU-5 | LLM temperature `0.2` and model `gpt-4o` in `crew_runtime.py` are the recorded runtime values (SAD ≤ 0.3) | Live crew still gated on API keys |

---

## Open Questions

1. Should production task YAML move from `project-context/2.build/task_catalog/` to SAD’s `config/task_catalog/`?
2. **Resolved (2026-08-28):** SAD §4.1 now documents the implemented `src/` tree (`src/onboarding/`, `src/onboarding-ui/`, `src/frontend/`). Nested `src/cli` / `src/catalog` remains unused.
3. Is `src/frontend/` (Critical Research Workflow) still in scope, or should it be archived now that onboarding UI lives under `src/onboarding-ui/`?

---

## Audit

**Timestamp:** 2026-08-28T16:24:00-04:00  
**Persona ID:** `project-mgr`  
**Action:** `setup-project` (restructure application code under `src/`); `configure-env`; `document-setup`  
**Artifact:** `project-context/2.build/setup.md`  
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`)  
**LLM:** OpenAI `gpt-4o`; temperature `0.2`; Gemini fallback `gemini/gemini-3.6-flash` when `OPENAI_API_KEY` is unset and `GEMINI_API_KEY` is set  
**Prompt Trace:** Omitted — no agent prompts rendered; this epic is folder layout, env names, and documentation only  
**Tool log:** Moved `frontend/` → `src/frontend/`, `onboarding-ui/` → `src/onboarding-ui/`; constrained setuptools find to `onboarding*`; updated path references in README, UI READMEs, and define-phase specs

---

## Audit (sync-docs 2026-08-28)

**Timestamp:** 2026-08-28
**Persona ID:** `project-mgr`
**Action:** `sync-docs`
**What changed:** Remaining docs (README, SAD §4.1, PRD SD-10 notes, CHECKLIST, AGENTS.md, functional specs) aligned to `src/` layout. Open Question 2 resolved.  
