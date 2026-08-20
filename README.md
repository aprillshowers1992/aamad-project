# Automated Employee Onboarding Workflow

Internal AI Engineering tool that generates **catalog-grounded** 30/60/90-day onboarding plans and manager checklists for five roles. Operators run a CLI; the system selects, sequences, and validates tasks from an authoritative catalog rather than inventing work.

This repository is a product project built with the AAMAD framework 0.7.5 (Define → Build → Deliver). Source: [aprillshowers1992/aamad-project](https://github.com/aprillshowers1992/aamad-project).

## Current status

**Phase 1 (Define) is complete.** Phase 2 (Build) has not started — there is no runnable `onboard` application yet.

| Artifact | Path | Status |
| -------- | ---- | ------ |
| Market research | [`project-context/1.define/mrd.md`](project-context/1.define/mrd.md) | Complete |
| Product requirements | [`project-context/1.define/prd.md`](project-context/1.define/prd.md) | Complete (authoritative) |
| Prior PRD (comparison only) | [`project-context/1.define/prd-2026-08-09.md`](project-context/1.define/prd-2026-08-09.md) | Preserved; not authoritative |
| System architecture | [`project-context/1.define/sad.md`](project-context/1.define/sad.md) | Complete |
| Setup / backend / QA / deploy | `project-context/2.build/`, `project-context/3.deliver/` | Not started |

**Resolved runtime:** CrewAI (`aamad.config.yml` `runtime.target: crewai`). **Language:** Python 3.11+. **MVP interface:** CLI `onboard`. **LLM (when implemented):** OpenAI `gpt-4o` via `OPENAI_API_KEY`.

## What the MVP does

Given `role`, `department`, and `start_date`, four sequential agents produce two Markdown files under `./output/` (override with `--output-dir` or `ONBOARDING_OUTPUT_DIR`):

1. `onboarding-plan.md` — role-aware 30/60/90-day plan
2. `manager-checklist.md` — matching manager checklist

```text
CLI Input
   → Role Analyst        (select applicable catalog task IDs)
   → Plan Builder        (sequence into 30/60/90 buckets)
   → Compliance Checker  (independent PASS / REJECT)
   → Document Writer     (render Markdown only after PASS)
```

A rejected plan returns to the Plan Builder at most **two times** after the first candidate. If validation never passes, the workflow fails closed: no approved plan or checklist is written.

**Supported roles (canonical identifiers only):** `UI Designer` · `UX Researcher` · `Product Manager` · `Developer` · `Engineer`

Developer and Engineer are distinct roles with separate task sets.

## What the MVP does not do

Marked as **Future Work** in the PRD/SAD — do not treat these as current scope:

- Web or chat UI
- Live HRIS or identity-provider integration
- Executing, tracking, or reminding about onboarding tasks
- Inventing catalog tasks or inferring legal requirements beyond the catalog
- Extra roles, role aliases, or calendar deadline inference

The task catalog is **interfaces and placeholders only** until stakeholders supply approved YAML content. Build agents must not fill placeholders with model-generated tasks.

## Planned CLI (after Build)

```text
onboard --role "Developer" --department "AI Engineering" --start-date "YYYY-MM-DD" [--output-dir PATH]
```

| Argument | Rule |
| -------- | ---- |
| `--role` | One of the five canonical names; no aliases |
| `--department` | Required; recorded as metadata; does not filter tasks in MVP |
| `--start-date` | `YYYY-MM-DD`; never inferred from the clock |
| `--output-dir` | Optional; default `./output/` |

Invalid input fails before any agent run (non-zero exit, no files generated).

## Repository structure

```text
aamad-project/
├── .cursor/                 # AAMAD personas, rules, templates, prompts
├── project-context/
│   ├── 1.define/            # MRD, PRD, SAD (complete)
│   ├── 2.build/             # Setup, backend, QA, security (not started)
│   └── 3.deliver/           # Deploy runbook and user guide (not started)
├── aamad.config.yml         # Runtime, language, testing, security preferences
├── AGENTS.md                # Persona index
├── CHECKLIST.md             # Define → Build → Deliver execution checklist
└── README.md
```

`.venv/` is local-only and is not committed.

## Next step: Phase 2 Build

Follow [`CHECKLIST.md`](CHECKLIST.md). In Cursor, start a **new chat** per epic and invoke the persona:

1. `@project.mgr` — scaffold Python/CrewAI environment (`setup.md`)
2. `@backend.eng` — CLI, catalog loader, agents, validation gate (`backend.md`)
3. `@frontend.eng` — **not required for MVP** (CLI is the interface)
4. `@integration.eng` — wire CLI to crew (`integration.md`)
5. `@qa.eng` then `@security.eng` — tests and security assessment
6. `@devops.eng` — Deliver (`deploy.md`, user guide)

Optional gate: `aamad validate --phase define` before Build.

Catalog YAML (one file per set, stakeholder-supplied): `shared_tasks`, `compliance_legal_tasks`, `it_provisioning_tasks`, `ui_designer_tasks`, `ux_researcher_tasks`, `product_manager_tasks`, `developer_tasks`, `engineer_tasks`, `team_integration_tasks`.

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

Runtime secrets are environment variables only (`OPENAI_API_KEY`). Do not commit `.env` files or API keys.
