# Automated Employee Onboarding Workflow

Internal AI Engineering tool that generates **catalog-grounded** 30/60/90-day onboarding plans and manager checklists for five roles. The system selects, sequences, and validates tasks from an authoritative catalog rather than inventing work.

This repository is a product project built with the AAMAD framework 0.7.5 (Define → Build → Deliver). Source: [aprillshowers1992/aamad-project](https://github.com/aprillshowers1992/aamad-project).

## Current status

**Phase 1 (Define) is complete.** Phase 2 (Build) is in progress: CLI, FastAPI wrap, onboarding UI, and tests are runnable. Deliver (`deploy.md`, user guide) and `security.md` are not started.

| Artifact | Path | Status |
| -------- | ---- | ------ |
| Market research | [`project-context/1.define/mrd.md`](project-context/1.define/mrd.md) | Complete |
| Product requirements | [`project-context/1.define/prd.md`](project-context/1.define/prd.md) | Complete (authoritative) |
| Prior PRD (comparison only) | [`project-context/1.define/prd-2026-08-09.md`](project-context/1.define/prd-2026-08-09.md) | Preserved; not authoritative |
| System architecture | [`project-context/1.define/sad.md`](project-context/1.define/sad.md) | Complete (SD-10 UI wrap) |
| Setup | [`project-context/2.build/setup.md`](project-context/2.build/setup.md) | Complete |
| Onboarding HTTP spec | [`project-context/1.define/onboarding-backend-spec.md`](project-context/1.define/onboarding-backend-spec.md) | Implemented (`src/onboarding/api.py`) |
| Backend / frontend / QA / security / deploy | `project-context/2.build/*.md`, `project-context/3.deliver/` | Not yet written as epic artifacts |

**Resolved runtime:** CrewAI (`aamad.config.yml` `runtime.target: crewai`). **Language:** Python 3.11+. **Interfaces:** CLI `onboard` (SD-6) and a minimal UI that wraps the same core (SD-10). **LLM:** OpenAI `gpt-4o` via `OPENAI_API_KEY` (optional; catalog stubs run without a key).

**Catalog:** Developer content is supplied. UI Designer, UX Researcher, Product Manager, Engineer, and shared sets remain placeholders — do not fill them with model-generated tasks.

## What the product does

Given `role`, `department`, and `start_date`, four sequential agents produce two Markdown files under `./output/` (override with `--output-dir` or `ONBOARDING_OUTPUT_DIR`):

1. `onboarding-plan.md` — role-aware 30/60/90-day plan
2. `manager-checklist.md` — matching manager checklist

```text
CLI or UI input
   → Role Analyst        (select applicable catalog task IDs)
   → Plan Builder        (sequence into 30/60/90 buckets)
   → Compliance Checker  (independent PASS / REJECT)
   → Document Writer     (render Markdown only after PASS)
```

A rejected plan returns to the Plan Builder at most **two times** after the first candidate. If validation never passes, the workflow fails closed: no approved plan or checklist is written.

**Supported roles (canonical identifiers only):** `UI Designer` · `UX Researcher` · `Product Manager` · `Developer` · `Engineer`

Developer and Engineer are distinct roles with separate task sets. **Runnable happy path today:** `Developer` only.

## What it does not do

- Live HRIS or identity-provider integration
- Executing, tracking, or reminding about onboarding tasks
- Inventing catalog tasks or inferring legal requirements beyond the catalog
- Extra roles, role aliases, or calendar deadline inference
- Rich chat UI, pause/cancel, or multi-screen workflows (SD-10 is a single form + results page)

`src/frontend/` is a separate **Critical Research Workflow** prototype. It is not the onboarding product.

## Run locally

Need: Python 3.11+ (3.12 recommended), Node.js LTS, a repo-root `.venv`. Details: [`project-context/2.build/setup.md`](project-context/2.build/setup.md).

### CLI

```text
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
onboard --role "Developer" --department "AI Engineering" --start-date "2026-09-01"
```

| Argument | Rule |
| -------- | ---- |
| `--role` | One of the five canonical names; no aliases. Only `Developer` has a catalog |
| `--department` | Required; recorded as metadata; does not filter tasks |
| `--start-date` | `YYYY-MM-DD`; never inferred from the clock |
| `--output-dir` | Optional; default `./output/` |

Invalid input fails before any agent run (non-zero exit, no files generated).

### Onboarding UI + API (SD-10)

```text
.\.venv\Scripts\python.exe -m uvicorn onboarding.api:app --host 127.0.0.1 --port 8000
cd src/onboarding-ui
npm install
npm run dev
```

UI: [http://localhost:5174/](http://localhost:5174/). API: [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Tests

```text
.\.venv\Scripts\python.exe -m pytest tests
```

Secrets are environment variables only (`OPENAI_API_KEY`, optional `GEMINI_API_KEY`). Copy [`.env.example`](.env.example) to `.env`. Do not commit `.env` or API keys.

## Repository structure

Application code lives under `src/`. AAMAD artifacts stay at the repo root and in `project-context/`.

```text
aamad-project/
├── .cursor/                 # AAMAD personas, rules, templates, prompts
├── config/                  # CrewAI agents.yaml and tasks.yaml
├── src/
│   ├── onboarding/          # Python CLI, API, catalog, crew, compliance
│   ├── onboarding-ui/       # Onboarding Vite + React UI (port 5174)
│   └── frontend/            # Critical Research Workflow prototype (port 5173)
├── tests/                   # Python unit and integration tests
├── project-context/
│   ├── 1.define/            # MRD, PRD, SAD, functional specs
│   ├── 2.build/             # setup.md, Developer catalog, task_catalog/
│   └── 3.deliver/           # Deploy runbook and user guide (not started)
├── pyproject.toml
├── .env.example
├── aamad.config.yml
├── AGENTS.md
├── CHECKLIST.md
└── README.md
```

`.venv/` is local-only and is not committed.

## Remaining Build / Deliver work

Follow [`CHECKLIST.md`](CHECKLIST.md). In Cursor, start a **new chat** per epic:

1. `@backend.eng` — record `src/onboarding/` in `backend.md`
2. `@frontend.eng` — record `src/onboarding-ui/` in `frontend.md`
3. `@integration.eng` — record UI ↔ API wiring in `integration.md`
4. `@qa.eng` then `@security.eng` — `qa.md` and `security.md`
5. `@devops.eng` — Deliver (`deploy.md`, user guide)

Catalog YAML (one file per set): `shared_tasks`, `compliance_legal_tasks`, `it_provisioning_tasks`, `ui_designer_tasks`, `ux_researcher_tasks`, `product_manager_tasks`, `developer_tasks`, `engineer_tasks`, `team_integration_tasks`. Only Developer is populated.

## Using AAMAD in your IDE

This project is initialized for **Cursor**. Personas live in `.cursor/agents/`; rules in `.cursor/rules/`.

| What you do | Cursor |
| ----------- | ------ |
| Start a fresh epic | `Cmd+Shift+P` / `Ctrl+Shift+P` → **New Chat** |
| Invoke a persona | `@product-mgr`, `@system.arch`, `@project.mgr`, `@backend.eng`, … |
| Reference a file | `@path/to/file` in chat |

The same AAMAD artifacts (`project-context/`, `.cursor/templates/`) can be used from Claude Code or VS Code + Copilot if you re-run `aamad init --ide …`. See [`AGENTS.md`](AGENTS.md) for the persona list.

## Configuration

[`aamad.config.yml`](aamad.config.yml) sets CrewAI as the target runtime, Python as the primary language, unit + integration tests mapped to acceptance criteria, and `security.require_security_assessment: true` before Deliver.
