# System Architecture Document — Automated Employee Onboarding Workflow

**Persona:** `system-arch`
**Action:** `create-sad`
**Phase:** Define
**Intended path:** `project-context/1.define/sad.md`
**Product:** Automated Employee Onboarding Workflow
**Target organization:** AI Engineering
**Selected runtime:** CrewAI
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai`
**Primary interface:** Command-line interface (CLI)
**Status:** Architecture handoff candidate; stakeholder decisions recorded; task catalog content unresolved

---

## Stakeholder Decisions (2026-08-19)

| # | Decision | Value |
| - | -------- | ----- |
| SD-1 | LLM provider / model | OpenAI `gpt-4o` |
| SD-2 | Task catalog format | YAML, one file per task set |
| SD-3 | Default output directory | `./output/` (override via `--output-dir` or `ONBOARDING_OUTPUT_DIR`) |
| SD-4 | Task ID visibility in Markdown | Audit appendix only — not inline in plan body or checklist |
| SD-5 | Developer vs Engineer | Distinct supported roles; separate role-specific task sets (`developer_tasks.yaml`, `engineer_tasks.yaml`) |
| SD-6 | CLI executable name | `onboard` |
| SD-7 | Department applicability | Metadata only for MVP; does not filter task selection |
| SD-8 | `source_reference` format | URL string |

---

## Context & Instructions

This SAD specifies the MVP system architecture for a CrewAI-based multi-agent application that generates role-aware 30/60/90-day onboarding plans and manager checklists from an authoritative task catalog. It aligns with the PRD's sequential agent workflow, deterministic validation gate, and zero-invention task policy.

**Input artifacts:**

| Artifact | Path | Status |
| -------- | ---- | ------ |
| PRD | `project-context/1.define/prd.md` | Complete |
| MRD | `project-context/1.define/mrd.md` | Complete |
| User stories | `project-context/1.define/user-stories/` | Not present |
| Project config | `aamad.config.yml` | Present (`runtime.target: crewai`, `language.primary: python`) |

---

# 1. MVP Architecture Philosophy & Principles

## 1.1 MVP Design Principles

| Principle | Architectural implication |
| --------- | ------------------------- |
| **Catalog authority over model inference** | Task definitions live in version-controlled configuration; agents manipulate `task_id` references only. Titles and descriptions are resolved at render time from the catalog. |
| **Separation of construction and validation** | Plan Builder constructs candidates; Compliance Checker independently validates. The Builder never self-certifies. |
| **Deterministic control boundaries** | Input validation, retry counting, schema validation, PASS eligibility, and document-write gating are implemented in application code—not delegated to LLM discretion. |
| **Fail closed** | Terminal compliance failure produces no approved onboarding artifacts. |
| **Observable by default** | Each workflow run records `workflow_id`, handoff payloads, validation findings, retry count, and final status for auditability. |
| **Adapter isolation** | Employee context acquisition and future HRIS/IdP integrations are isolated behind `EmployeeContextProvider`; agent logic remains vendor-agnostic. |
| **Minimal viable surface** | MVP is a CLI batch tool with local Markdown output. No web UI, no live enterprise integrations, no task execution. |

## 1.2 Core vs Future Features

### MVP (in scope)

- CLI accepting `role`, `department`, `start_date`
- Pre-flight input and task-catalog structural validation
- Authoritative task-catalog loader with startup validation
- Placeholder task-set interfaces (content supplied by stakeholder)
- Four specialized CrewAI agents in sequential process
- Structured Pydantic handoffs between all agent boundaries
- Deterministic retry controller (max 2 Builder retries after initial candidate)
- Compliance Checker as mandatory validation gate
- Markdown outputs: `onboarding-plan.md`, `manager-checklist.md`
- `CliEmployeeContextProvider` adapter
- Structured run diagnostics on failure
- Unit and integration test fixtures for all five supported roles

### Future Work (explicit deferrals)

| Capability | Rationale for deferral |
| ---------- | ---------------------- |
| Web chat UI | PRD specifies CLI-only MVP |
| Live HRIS integration | PRD §6.1; adapter boundary only |
| Live identity-provider integration | PRD §6.4 |
| Account provisioning and permission assignment | PRD non-goals |
| Task completion tracking and notifications | PRD non-goals |
| Exact calendar deadline inference | PRD §5.3 bucket rules |
| Additional roles beyond five named | PRD §3.3 |
| Dynamic task creation by agents | PRD §4.3 zero-invention policy |
| Performance evaluation or employment decisions | PRD non-goals |
| Enterprise AuthN/AuthZ for CLI | No live integrations in MVP |
| Horizontal scaling and multi-region deployment | Internal moderate volume (MRD A6) |
| Advanced APM and cost dashboards | Baseline logging sufficient for MVP |
| JSON machine-readable result alongside Markdown | PRD Could Have |
| Role alias configuration | PRD Could Have |
| Catalog linting CLI command | PRD Could Have |

## 1.3 Technical Architecture Decisions

| Decision | Choice | Rationale | PRD trace |
| -------- | ------ | --------- | --------- |
| Runtime | CrewAI | PRD §8.1; sequential process and structured outputs fit validation-gate workflow | §8.1, §5.1 |
| Language | Python 3.11+ | `aamad.config.yml` `language.primary: python`; CrewAI ecosystem | Config |
| Process model | Sequential | Ordered Role Analyst → Plan Builder → Compliance Checker → Document Writer; retry loop managed by orchestrator | §5.1, §9 |
| Agent count | 4 | PRD-defined specialization with distinct validation boundaries | §5.2–§5.5 |
| Interface | CLI only | No frontend MVP; operator invokes batch generation | §7.1 |
| Persistence | None (filesystem only) | Task catalog and outputs are local files; no database required by PRD | §6.1, §12.3 |
| Inter-agent data format | Pydantic models / JSON schemas | Reduces parsing ambiguity; enables deterministic schema validation | §8.1, §12.5 |
| Streaming | Not required | Batch CLI workflow; success/failure reported after completion | §7.4–§7.6 |
| Memory | Disabled (`memory=False`) | Reproducibility per CrewAI adapter rules; each run is stateless aside from persisted diagnostics | Adapter rule |
| Compliance retry limit | Application invariant `max_builder_retries = 2` | Explicit product rule; not delegated to CrewAI defaults | §5.4, §9 |
| LLM provider | OpenAI | Stakeholder decision SD-1 | SD-1 |
| LLM model | `gpt-4o` | Stakeholder decision SD-1 | SD-1 |
| Task catalog format | YAML, one file per task set | Stakeholder decision SD-2; matches PRD placeholder task sets | SD-2, §4.1 |
| Default output path | `./output/` | Stakeholder decision SD-3 | SD-3 |
| CLI executable | `onboard` | Stakeholder decision SD-6 | SD-6 |
| Department filtering | None in MVP | Department recorded in outputs; task selection by role only | SD-7 |
| Task ID presentation | Audit appendix only | End-user sections show titles/descriptions; IDs in appendix | SD-4 |
| `source_reference` | URL string | Catalog field holds a URL to authoritative policy/doc | SD-8 |

### Frontend decision (N/A with rationale)

The PRD explicitly scopes MVP to a command-line interface. **No web frontend is in MVP scope.** The Integration and Frontend build epics for a chat UI do not apply to this product unless a future PRD revision adds a UI surface. Build-phase `@frontend.eng` work is **not required** for MVP acceptance per current PRD.

---

# 2. Multi-Agent System Specification

## 2.1 Agent Architecture

Four specialized agents operate within a single CrewAI crew. Each agent has a narrow responsibility boundary aligned with PRD §5.

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Workflow Orchestrator                        │
│  (application code — NOT a CrewAI agent)                        │
│  - workflow_id, retry_count, schema validation, state machine   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            v
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   ┌─────────────────┐
│ Role Analyst │ → │ Plan Builder │ → │ Compliance       │ → │ Document Writer │
│              │   │              │   │ Checker          │   │                 │
│ Applicability│   │ Sequencing & │   │ Independent      │   │ Markdown render │
│ selection    │   │ bucketing    │   │ validation gate  │   │ from catalog    │
└──────────────┘   └──────────────┘   └──────────────────┘   └─────────────────┘
                            ↑                    │
                            └──── REJECT ────────┘
                                 (max 2 retries)
```

### Agent 1 — Role Analyst

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Determine exactly which authoritative task definitions apply to the onboarding scenario |
| **Inputs** | `OnboardingRequest`, authoritative task catalog, `WorkflowContext` |
| **Output** | `RoleAnalysis` (task IDs + metadata only) |
| **Allowed actions** | Select active tasks from shared, compliance/legal, IT provisioning, role-specific, and team-integration task sets filtered by **role only**; `department` is carried as metadata and does not affect applicability in MVP (SD-7) |
| **Prohibited** | Create tasks, alter descriptions, sequence, assign buckets, omit mandatory applicable tasks, perform compliance approval |
| **Tools** | Read-only access to task catalog repository; no write, network, or shell tools |
| **Memory** | None |

### Agent 2 — Plan Builder

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Transform applicable task set into ordered 30/60/90 onboarding plan |
| **Inputs** | `RoleAnalysis`, task catalog, priority rules, optional `PlanRevisionRequest` on retry |
| **Output** | `CandidatePlan` |
| **Allowed actions** | Assign each task to exactly one bucket (`30_DAY`, `60_DAY`, `90_DAY`); sequence within priority hierarchy |
| **Prohibited** | Invent tasks, infer calendar deadlines, remove correctly selected mandatory tasks to fix unrelated failures |
| **Priority order** | `COMPLIANCE_LEGAL` > `IT_PROVISIONING` > `ROLE_ENABLEMENT` > `TEAM_INTEGRATION` |
| **Tools** | Read-only task catalog access |
| **Memory** | None |

### Agent 3 — Compliance Checker

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Independent validation gate; return `PASS` or `REJECT` with machine-readable findings |
| **Inputs** | `RoleAnalysis`, `CandidatePlan`, task catalog, priority rules, current retry count |
| **Output** | `ComplianceResult` |
| **Validation checks** | Mandatory compliance coverage, mandatory provisioning coverage, traceability, applicability, uniqueness, bucket validity, priority integrity, role integrity |
| **Prohibited** | Modify plans, bypass checks, return `PASS` with error-level findings |
| **Tools** | Read-only task catalog access; deterministic validation helpers (implemented in code, not LLM-only) |
| **Memory** | None |

**Architecture note:** Critical validation logic (task ID existence, mandatory coverage counts, bucket rule enforcement, duplicate detection) SHOULD be implemented as **deterministic Python functions** invoked by or alongside the Checker agent. The LLM may assist with priority-integrity assessment, but PASS eligibility MUST be computed deterministically from boolean check results (PRD §8.7).

### Agent 4 — Document Writer

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Render approved plan into human-readable Markdown |
| **Precondition** | `ComplianceResult.status == PASS` |
| **Inputs** | `ApprovedPlan`, task catalog |
| **Outputs** | `onboarding-plan.md`, `manager-checklist.md` |
| **Allowed actions** | Resolve task titles/descriptions from catalog; format presentation; append **Audit Appendix** with task IDs, catalog version, and hash |
| **Prohibited** | Execute without PASS; introduce new tasks; alter authoritative task meaning; expose raw `task_id` inline in 30/60/90 sections or checklist items (SD-4) |
| **Tools** | Read-only catalog access; filesystem write to configured output directory only |
| **Memory** | None |

## 2.2 Task / Turn Orchestration

### Execution flow

```text
1. CLI parses and validates inputs
2. Load and validate task catalog (structural + schema)
3. Initialize WorkflowContext (workflow_id, catalog version/hash)
4. CliEmployeeContextProvider → EmployeeContext
5. CREW: Role Analyst → RoleAnalysis
6. Application validates RoleAnalysis schema + task_id existence
7. LOOP (build_attempt = 1..3):
   a. CREW: Plan Builder → CandidatePlan
   b. Application validates CandidatePlan schema + task_id existence
   c. CREW: Compliance Checker → ComplianceResult
   d. Application validates ComplianceResult schema + deterministic checks
   e. IF PASS → break
   f. IF REJECT AND build_attempt < 3 → PlanRevisionRequest → retry
   g. IF REJECT AND build_attempt == 3 → TERMINAL FAILURE
8. IF PASS: CREW Document Writer → Markdown files
9. Emit CLI success/failure message; persist diagnostics
```

### Context passing

All stages receive `WorkflowContext`:

```text
WorkflowContext
- workflow_id: string          # UUID; unique per generation attempt
- role: SupportedRole
- department: string
- start_date: date
- task_catalog_version: string
- task_catalog_hash: string    # SHA-256 of canonical catalog content
- supported_roles: list
- priority_rules: ordered list
- retry_count: integer
- max_builder_retries: 2        # invariant
```

CrewAI task context chaining (`Task.context`) passes prior structured outputs forward within the crew execution path. The **Workflow Orchestrator** remains responsible for injecting retry state and re-invoking Plan Builder outside the linear crew sequence when compliance rejects.

### Handoff schemas (canonical)

| Handoff | Schema | PRD reference |
| ------- | ------ | ------------- |
| A: CLI → Role Analyst | `OnboardingRequest` | §8.4 |
| B: Role Analyst → Plan Builder | `RoleAnalysis` | §8.5 |
| C: Plan Builder → Compliance Checker | `CandidatePlan` | §8.6 |
| D: Checker decision | `ComplianceResult` | §8.7 |
| E: Rejection → Plan Builder | `PlanRevisionRequest` | §8.8 |
| F: Approved → Document Writer | `ApprovedPlan` | §8.9 |

All schemas SHALL be implemented as Pydantic v2 models with strict validation. Unknown fields rejected.

### Error handling, retries, and timeouts

| Control | Behavior |
| ------- | -------- |
| Invalid CLI input | Fail before crew invocation; exit non-zero; no files generated |
| Malformed agent output | Treat as stage failure; do not silently parse or guess |
| Compliance REJECT | Return structured findings to Plan Builder; increment `build_attempt` |
| Max retries exhausted | Terminal failure; no Document Writer; diagnostic artifact optional |
| Agent timeout | Configurable per-task `max_execution_time`; failure treated as stage error |
| CrewAI `max_iter` | ≤ 12 per agent task (adapter default) |
| CrewAI `max_retry_limit` | ≥ 2 at task level; product retry limit remains orchestrator-controlled |
| Cancellation | CLI SIGINT → abort run; no partial approved outputs |

### Performance budgets

| Budget | MVP target | Notes |
| ------ | ---------- | ----- |
| End-to-end CLI run (happy path) | No hard SLA; monitor during pilot | No PRD throughput requirement |
| Max build attempts | 3 | Product invariant |
| Max agent iterations | 12 per task | CrewAI adapter baseline |
| Concurrent workflows | 1 per CLI invocation | No multi-tenant server in MVP |
| Token budget | Configure per OpenAI `gpt-4o` usage; log per run | Record in setup.md Audit |

## 2.3 Runtime-Conditional Configuration — CrewAI

### Crew composition

```yaml
# config/agents.yaml (conceptual)
role_analyst:
  role: "Role Analyst"
  goal: "Select applicable task IDs from authoritative catalog for role (department is metadata only in MVP)"
  backstory: "Expert in onboarding applicability; never invents tasks"
  allow_delegation: false
  max_iter: 12

plan_builder:
  role: "Plan Builder"
  goal: "Sequence applicable tasks into 30/60/90 buckets respecting priority rules"
  backstory: "Expert onboarding planner; uses catalog IDs only"
  allow_delegation: false
  max_iter: 12

compliance_checker:
  role: "Compliance Checker"
  goal: "Independently validate candidate plans against mandatory coverage and traceability rules"
  backstory: "Independent auditor; never modifies plans"
  allow_delegation: false
  max_iter: 12

document_writer:
  role: "Document Writer"
  goal: "Render approved plans into Markdown using catalog-resolved titles and descriptions"
  backstory: "Technical writer; presentation only, no new tasks"
  allow_delegation: false
  max_iter: 12
```

```yaml
# config/tasks.yaml (conceptual)
analyze_role:
  agent: role_analyst
  context: []
  output_pydantic: RoleAnalysis

build_plan:
  agent: plan_builder
  context: [analyze_role]
  output_pydantic: CandidatePlan

check_compliance:
  agent: compliance_checker
  context: [analyze_role, build_plan]
  output_pydantic: ComplianceResult

write_documents:
  agent: document_writer
  context: [build_plan, check_compliance]
  output_pydantic: DocumentWriteResult  # paths + metadata
```

### Process type

- **Sequential** for the forward path within a single build attempt
- **Retry loop** implemented in `crew.py` / orchestrator application code wrapping partial crew re-execution (Plan Builder + Compliance Checker only on retry; Role Analyst does not rerun unless applicability error indicates configuration fault)

### Task context chaining

- `build_plan` receives `RoleAnalysis` via context
- `check_compliance` receives both `RoleAnalysis` and `CandidatePlan`
- `write_documents` receives `ApprovedPlan` assembled by orchestrator after deterministic PASS confirmation

### Guardrails

- CrewAI task guardrails MAY validate output schema size and required fields
- Product-level PASS eligibility and retry limits remain in application code per PRD §5.4

### LLM configuration

| Setting | Value |
| ------- | ----- |
| Provider | OpenAI (SD-1) |
| Model | `gpt-4o` (SD-1) |
| API key env var | `OPENAI_API_KEY` |
| Temperature | ≤ 0.3 for reproducibility unless Audit justifies otherwise |
| Agent scope | Same provider/model for all four agents unless setup.md documents a justified exception |

Secrets MUST NOT appear in task catalogs, Markdown outputs, or Prompt Trace.

---

# 3. Frontend Architecture Specification

## 3.1 Scope determination

**Not applicable for MVP.** The PRD specifies a command-line interface as the sole operator surface (PRD §7.1). No web application, chat UI, or graphical frontend is required.

## 3.2 CLI as the primary interface

The CLI layer fulfills the "frontend" responsibility for operator interaction.

### Technology stack

| Component | Selection | Source |
| --------- | --------- | ------ |
| CLI framework | TBD (`argparse` stdlib minimum; `typer` or `click` acceptable per `@project.mgr` setup) | Implementation decision |
| Language | Python 3.11+ | `aamad.config.yml` |
| Output | stdout/stderr + local Markdown files | PRD §7.4–§7.6 |

### Interface contract

**Invocation:**

```text
onboard --role "Developer" --department "AI Engineering" --start-date "YYYY-MM-DD" [--output-dir PATH]
```

- **Executable name:** `onboard` (SD-6); registered as console script entry point in `pyproject.toml`
- **Default output directory:** `./output/` (SD-3); overridable via `--output-dir` or `ONBOARDING_OUTPUT_DIR`

**Required arguments:**

| Argument | Validation |
| -------- | ---------- |
| `--role` | Must match one of five canonical `SupportedRole` values |
| `--department` | Required; non-whitespace; trim leading/trailing whitespace |
| `--start-date` | ISO `YYYY-MM-DD`; reject invalid calendar dates |

**Optional arguments (Should Have):**

| Argument | Purpose |
| -------- | ------- |
| `--output-dir` | Override default `./output/` (SD-3) |
| `--verbose` | Future Work (PRD Could Have) |

### User experience states

| State | CLI behavior | Exit code |
| ----- | ------------ | --------- |
| Success | Display role, department, date, validation PASS, retries used, output paths | 0 |
| Input failure | Error message, supported roles listed, "No files were generated" | non-zero |
| Terminal compliance failure | Attempt counts, structured human-readable findings, no approved outputs | non-zero |
| Configuration error | Catalog load/validation failure before agent execution | non-zero |

### Accessibility and responsive design

Not applicable to CLI MVP. Future web UI would require WCAG considerations.

---

# 4. Backend Architecture Specification

## 4.1 Application structure

The MVP is a **Python CLI application** with no HTTP server. "Backend" refers to the orchestration, validation, and CrewAI runtime layer.

```text
onboarding-workflow/                 # generated application root (TBD naming)
├── pyproject.toml
├── .env.example
├── config/
│   ├── agents.yaml
│   ├── tasks.yaml
│   └── task_catalog/                # authoritative task sets (stakeholder-populated)
│       ├── shared_tasks.yaml
│       ├── compliance_legal_tasks.yaml
│       ├── it_provisioning_tasks.yaml
│       ├── ui_designer_tasks.yaml
│       ├── ux_researcher_tasks.yaml
│       ├── product_manager_tasks.yaml
│       ├── developer_tasks.yaml
│       ├── engineer_tasks.yaml
│       └── team_integration_tasks.yaml
├── src/
│   ├── cli/
│   │   └── main.py                  # entrypoint, argument parsing
│   ├── adapters/
│   │   ├── employee_context.py      # EmployeeContextProvider protocol
│   │   └── cli_employee_context.py  # CliEmployeeContextProvider
│   ├── catalog/
│   │   ├── loader.py
│   │   ├── validator.py
│   │   └── repository.py
│   ├── models/
│   │   ├── enums.py                 # SupportedRole, TaskCategory, Bucket
│   │   ├── task_definition.py
│   │   ├── handoffs.py              # OnboardingRequest, RoleAnalysis, etc.
│   │   └── workflow_context.py
│   ├── validation/
│   │   ├── compliance_rules.py      # deterministic checks
│   │   └── schema_validators.py
│   ├── orchestrator/
│   │   ├── workflow.py              # state machine, retry controller
│   │   └── diagnostics.py
│   ├── rendering/
│   │   └── markdown_templates.py
│   └── crew/
│       ├── crew.py                    # CrewAI crew factory
│       └── tools/
│           └── catalog_reader.py      # read-only catalog tool
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
        └── task_catalog/              # test fixtures (not production content)
```

Directory layout is a **recommended scaffold** for build personas; exact paths are an implementation detail unless stakeholder specifies otherwise.

## 4.2 API architecture

**No HTTP API in MVP.** PRD §6.1 specifies CLI input and local Markdown output only.

Future adapter boundary (not implemented):

```text
EmployeeContextProvider
  get_employee_context(input_reference) -> EmployeeContext

EmployeeContext (MVP subset)
  role: SupportedRole
  department: string
  start_date: date
```

Future HRIS adapter may extend `EmployeeContext` with additional fields (PRD §6.3) without modifying agent business logic.

## 4.3 Data architecture

| Data | Storage | MVP persistence |
| ---- | ------- | ----------------- |
| Task catalog | Version-controlled YAML files (one file per task set) | Filesystem |
| Workflow diagnostics | JSON log per run | Filesystem under `project-context/2.build/logs/` or configurable path |
| Generated plans | Markdown files under `./output/` by default | Filesystem output directory |
| Workflow state | In-memory during run | None across runs |

**No database** is required for MVP. PRD auditability requirements (§12.3) are satisfied by structured diagnostic logs and catalog version/hash embedded in outputs.

### Task catalog schema

Each task conforms to PRD §4.2 `TaskDefinition`:

```text
task_id, title, description, task_set, category, applicable_roles,
applicable_departments, mandatory, allowed_buckets, source_reference,
active, version
```

**Format decisions (SD-2, SD-8):**

- One YAML file per task set under `config/task_catalog/` (nine files per PRD §4.1)
- `source_reference` MUST be a URL string pointing to the authoritative policy or document (SD-8)
- `applicable_departments` remains in schema for future use; MVP Role Analyst ignores department for filtering (SD-7)

**Role-specific task sets (SD-5):** `Developer` and `Engineer` are distinct `SupportedRole` values. Applicability uses `developer_tasks.yaml` vs `engineer_tasks.yaml` respectively—never a shared ambiguous role bucket.

Startup validation SHALL fail if:

- Required task-set YAML files are missing
- Any task lacks required fields
- Duplicate `task_id` values exist
- `task_id` format is invalid
- `source_reference` is not a valid URL string

## 4.4 Runtime integration layer

```text
CLI main()
  → InputValidator.validate()
  → TaskCatalogRepository.load_and_validate()
  → CliEmployeeContextProvider.get_employee_context()
  → WorkflowOrchestrator.run(EmployeeContext)
       → crew.kickoff() [Role Analyst]
       → SchemaValidator.validate(RoleAnalysis)
       → retry loop:
            → crew partial kickoff [Plan Builder, Compliance Checker]
            → DeterministicComplianceRules.evaluate()
            → if PASS: break
            → if retries exhausted: terminal failure
       → crew.kickoff() [Document Writer]  (only on PASS)
  → CLIReporter.emit(result)
```

Logging hooks per CrewAI adapter:

- Prompt Trace captured before agent execution (redact secrets)
- Lifecycle events (task start/stop, retries, guardrail outcomes) in Trace Log
- Persist under `project-context/2.build/logs/{workflow_id}/`

## 4.5 Authentication and secrets

| Secret / config | Env var | Notes |
| --------------- | ------- | ----- |
| OpenAI API key | `OPENAI_API_KEY` | Required for CrewAI LLM (SD-1) |
| Output directory override | `ONBOARDING_OUTPUT_DIR` (optional) | Default: `./output/` (SD-3) |
| Catalog path override | `ONBOARDING_CATALOG_PATH` (optional) | Default: `./config/task_catalog/` |

MVP requires **no HRIS, IdP, or operator authentication** (PRD §12.4, Assumption A5).

---

# 5. DevOps & Deployment Architecture

## 5.1 Deployment model

The MVP deploys as a **standalone Python CLI tool** runnable on a developer or coordinator workstation, or in CI for automated acceptance tests.

| Aspect | MVP approach |
| ------ | ------------ |
| Hosting | Local execution; no server deployment required |
| Containerization | Optional Docker image for reproducibility (Future Work unless `@devops.eng` scopes it in Deliver) |
| Health check | CLI `--version` and catalog validation subcommand (recommended Should Have) |
| Process model | Single-shot batch; one workflow per invocation |

## 5.2 CI/CD (minimal MVP)

Per `aamad.config.yml` and delivery workflow, CI pipeline stages:

1. **Lint** — `ruff` or project-standard linter
2. **Type check** — `mypy` or `pyright` (`type_checking: true`)
3. **Unit tests** — schema validation, compliance rules, input validation
4. **Integration tests** — full crew workflow against test fixtures for all five roles
5. **Build** — package installable artifact (`pip install .` or equivalent)

No live deploy stage without explicit operator authorization.

## 5.3 Observability

| Signal | MVP | Future |
| ------ | --- | ------ |
| Structured run logs | Yes — workflow_id, handoffs, findings | |
| Prompt Trace | Yes — per agent, redacted | |
| Metrics/APM | No | Datadog/similar if product evolves to service |
| Cost/token telemetry | Log per run when provider supports | Dashboards |

## 5.4 IaC and multi-region

**Future Work.** MVP is a local CLI with no cloud infrastructure requirement.

---

# 6. Data Flow & Integration Architecture

## 6.1 End-to-end data flow

```text
Operator
  │  role, department, start_date
  v
CLI Layer ──────────────────────────────────────────────┐
  │ validated OnboardingRequest                          │
  v                                                      │
EmployeeContextProvider (CliAdapter)                     │
  │ EmployeeContext                                      │
  v                                                      │
Task Catalog Repository ◄────────────────────────────────┤
  │ TaskDefinition[] + version + hash                    │
  v                                                      │
Workflow Orchestrator                                    │
  │                                                      │
  ├─► Role Analyst ──► RoleAnalysis                      │
  │       (task_ids only)                                │
  │                                                      │
  ├─► Plan Builder ──► CandidatePlan                     │
  │       (task_ids + buckets + sequence)                │
  │                                                      │
  ├─► Compliance Checker ──► ComplianceResult            │
  │       (PASS | REJECT + findings)                     │
  │       + Deterministic Rules Engine                   │
  │                                                      │
  └─► Document Writer ──► ./output/onboarding-plan.md   │
          (catalog-resolved text;     ./output/manager-checklist.md
           task IDs in audit appendix only — SD-4)
  │                                                      │
  v                                                      │
Local Filesystem ◄───────────────────────────────────────┘
  + diagnostic JSON log
```

## 6.2 External integrations (MVP)

**None.** PRD §6.1.

## 6.3 Future integration adapters

| Adapter | Interface | MVP status |
| ------- | --------- | ---------- |
| CLI | `CliEmployeeContextProvider` | Implemented |
| HRIS | `HrisEmployeeContextProvider` | Future Work — PRD §6.3 |
| Identity Provider | `IdpProvisioningContextProvider` | Future Work — PRD §6.4 |

Agent business logic MUST NOT depend on vendor-specific field names, authentication, or transport (PRD §6.5).

## 6.4 Error propagation

| Layer | Error type | Operator-visible result |
| ----- | ---------- | ----------------------- |
| CLI validation | Invalid role/date/department | Immediate error message; no crew run |
| Catalog load | Missing/malformed task set | Configuration error; no crew run |
| Agent output | Schema violation | Stage failure; diagnostic log |
| Compliance | REJECT after 3 attempts | Terminal failure message with findings |
| Document Writer | Precondition violation (not PASS) | Blocked by orchestrator; should not occur if state machine is correct |

---

# 7. Performance & Scalability Specifications

## 7.1 MVP targets

| Metric | Target | Status |
| ------ | ------ | ------ |
| Mandatory compliance coverage | 100% | PRD §13.2 — test-enforced |
| Zero invented tasks | 0 invalid task IDs in approved output | PRD §13.3 — test-enforced |
| Ramp-time reduction | ≥ 30% vs 3-week manual baseline | Pilot-measured; not automated in MVP |
| Response time | Not specified in PRD | Open Question |
| Concurrent users | N/A — CLI batch tool | |

## 7.2 Scalability path

MRD Assumption A6: internal onboarding volume is moderate; **correctness and observability take priority over throughput**.

Future scaling considerations (deferred):

- Service-ify CLI into an API if multi-operator or HRIS-triggered runs are needed
- Cache catalog in memory (already expected for single run)
- Parallel plan generation for batch hires

## 7.3 Token and cost controls

- Set `max_rpm` at crew level for budget stability (CrewAI adapter)
- Low temperature for deterministic agent behavior
- Model: OpenAI `gpt-4o` (SD-1); log token usage per run for pilot cost tracking
- Exact cost ceiling: not specified; establish during pilot if needed

---

## 7.4 Markdown output structure (Document Writer)

Both output files SHALL follow SD-4 presentation rules.

### `onboarding-plan.md`

| Section | Content |
| ------- | ------- |
| Header | Role, department, start date, task-catalog version |
| 30-day / 60-day / 90-day | Task **title**, description, category, source URL (`source_reference`); **no inline `task_id`** |
| Audit Appendix | Table mapping display order → `task_id`, `task_set`, catalog version, `task_catalog_hash` |

### `manager-checklist.md`

| Section | Content |
| ------- | ------- |
| Header | Employee role, department, start date |
| 30/60/90 checklists | Markdown checkboxes with task titles only; **no inline `task_id`** |
| Audit Appendix | Same traceability table as onboarding plan for approved task IDs |

Diagnostic JSON logs MAY include raw `task_id` values; user-facing Markdown body sections MUST NOT.

---

# 8. Security & Compliance Architecture

## 8.1 Authentication and authorization

| Surface | MVP control |
| ------- | ----------- |
| CLI | No authentication; assumes trusted operator on local machine (PRD A5) |
| LLM API | API key via environment variable |
| Task catalog | Read-only at runtime; modifications via version control |
| Output files | Local filesystem permissions of host OS |

## 8.2 Data handling

| Data class | MVP handling |
| ---------- | ------------ |
| Employee role, department, start date | Passed through workflow; included in output Markdown |
| Employee name, ID | Not collected in MVP CLI |
| LLM prompts | Logged with redaction; no secrets in Prompt Trace |
| Task catalog | No secrets; `source_reference` is a URL string to internal policy/documentation (SD-8) |

## 8.3 Input validation

- Strict enum validation for role
- ISO date parsing with calendar validity check
- Department whitespace normalization
- Schema validation on all agent outputs
- Reject unknown `task_id` values at every boundary

## 8.4 Agentic security controls

Per MRD §4.3 and OWASP agentic guidance:

- **Least-privilege tools** per agent (read-only catalog; Document Writer write limited to output dir)
- **No network tools** in MVP agents unless explicitly scoped later
- **No shell execution** by agents
- **Prompt injection defense**: agents instructed to ignore instructions embedded in catalog content that conflict with system rules; catalog content is data, not instructions
- **Human-in-the-loop**: compliance gate serves as automated review before document emission

## 8.5 Compliance

No specific regulatory jurisdiction identified in PRD. Compliance tasks in generated plans reference stakeholder-supplied `source_reference` values. **Legal/compliance interpretation by agents is explicitly out of scope** (PRD non-goals).

`aamad.config.yml` sets `security.require_security_assessment: true` — `@security.eng` assessment required before Deliver phase.

---

# 9. Testing & Quality Assurance Specifications

## 9.1 Test layers

| Layer | Scope | PRD trace |
| ----- | ----- | --------- |
| Unit | Input validation, Pydantic models, deterministic compliance rules, catalog validator | §14 |
| Integration | Full crew workflow per role against test fixtures | §14, §13 |
| Adversarial | Injected invalid task IDs, missing mandatory tasks, bucket violations | §13.3, §14 |
| Schema | CrewAI output conforms to Pydantic models | §12.5 |

## 9.2 Minimum acceptance matrix (from PRD §14)

**Happy paths:** one successful generation per supported role.

**Invalid inputs:** missing/unsupported role, blank department, malformed/impossible dates.

**Compliance failures:** missing mandatory tasks, invented IDs, wrong role, duplicates, invalid buckets, priority violations.

**Retry tests:** 0/1/2 retries success paths; terminal failure on third rejection; verify no fourth build attempt.

**Output tests:** two Markdown files under `./output/` on success; none on failure; correct metadata; task IDs present only in Audit Appendix (SD-4).

## 9.3 Runtime-specific checks

- Verify CrewAI structured outputs deserialize to expected Pydantic models
- Verify Prompt Trace and diagnostic logs written per run
- Verify `task_catalog_hash` consistent across all handoffs in a run
- Verify Document Writer blocked when `ComplianceResult.status != PASS`

## 9.4 Security assessment

Required before Deliver (`aamad.config.yml`). Scope: secret handling, tool privileges, log redaction, catalog integrity.

---

# 10. MVP Launch & Feedback Strategy

## 10.1 Pilot criteria

MVP is ready for pilot when:

1. Stakeholder-approved task catalog replaces placeholders
2. All PRD §20 acceptance criteria pass in automated tests
3. One successful plan generated for each of the five roles using production catalog
4. Security assessment complete or gap explicitly accepted

## 10.2 Success metrics (PRD-aligned)

| Metric | Target | Measurement method |
| ------ | ------ | ------------------ |
| Mandatory compliance/provisioning coverage | 100% | Automated test — PRD §13.2 |
| Zero invented tasks | 0 | Automated test — PRD §13.3 |
| Ramp-time reduction | ≥ 30% vs 3-week baseline | Pilot comparison — PRD §13.1 (requires baseline data) |

## 10.3 Iteration priorities post-pilot

1. Populate and govern authoritative task catalog with named owners
2. Replace assumed ramp baseline with measured data
3. Evaluate HRIS adapter if hire events should trigger generation automatically
4. Consider JSON output and configurable templates (Could Have)
5. Reassess whether multi-agent complexity outperforms deterministic workflow (MRD §5.3)

---

# Implementation Guidance for AI Development Agents

Recommended build order (from PRD §16, refined for architecture):

1. Pydantic models and handoff schemas
2. Task catalog loader and startup validator (placeholder fixtures only)
3. CLI and input validation
4. `EmployeeContextProvider` protocol and CLI adapter
5. Deterministic compliance rules engine
6. Workflow orchestrator and retry state machine
7. CrewAI crew configuration (`agents.yaml`, `tasks.yaml`, `crew.py`)
8. Role Analyst, Plan Builder, Compliance Checker, Document Writer tasks
9. Markdown rendering templates
10. Acceptance and adversarial test suite
11. Diagnostics and Prompt Trace logging

**Module sequencing per AAMAD development workflow:**

| Module | Epic focus |
| ------ | ---------- |
| Module 1 | Agent/task YAML definitions + crew.kickoff() against fixtures |
| Module 2 | Catalog repository + validation + adapter interfaces |
| Module 3 | CLI + Markdown rendering (no backend wiring — CLI invokes orchestrator directly) |
| Module 4 | End-to-end validation against PRD §14 test matrix |

**Frontend epic (`@frontend.eng`):** Not applicable for current PRD scope.

---

# Architecture Validation Checklist

- [x] PRD requirements mapped to architectural components
- [x] Agents designed for domain and CrewAI runtime (4 agents, sequential + retry loop)
- [x] CLI contract defined; no FE/BE schema mismatch (no HTTP API)
- [x] Secrets via env vars only
- [x] MVP vs Future Work boundaries explicit
- [x] Resolved `AAMAD_TARGET_RUNTIME=crewai` recorded in Audit
- [x] Task catalog format decided (YAML, one file per task set — SD-2)
- [x] LLM provider/model selected (OpenAI `gpt-4o` — SD-1)
- [x] Output path convention confirmed (`./output/` — SD-3)
- [x] CLI executable name confirmed (`onboard` — SD-6)
- [x] Task ID presentation confirmed (audit appendix — SD-4)
- [x] Department applicability confirmed (metadata only — SD-7)
- [x] Developer/Engineer distinction confirmed (separate task sets — SD-5)
- [x] `source_reference` format confirmed (URL string — SD-8)
- [ ] Task catalog **content** approved by stakeholder
- [ ] Security assessment (`@security.eng`) — Build/Deliver phase

---

# Sources

| Source | Path | Use in SAD |
| ------ | ---- | ---------- |
| PRD | `project-context/1.define/prd.md` | Primary requirements: agents, schemas, CLI, validation, non-goals |
| MRD | `project-context/1.define/mrd.md` | Context: pain points, security/observability guidance, deferral rationale |
| SAD template | `.cursor/templates/sad-template.md` | Document structure |
| AAMAD config | `aamad.config.yml` | Python, CrewAI runtime, testing/security gates |
| CrewAI adapter rule | `.cursor/rules/adapter-crewai.mdc` | YAML config, sequential process, logging, guardrails |
| AAMAD core rule | `.cursor/rules/aamad-core.mdc` | Artifact contracts, determinism, audit sections |

| Stakeholder clarifications | Operator input 2026-08-19 | SD-1 through SD-8 decisions |

User stories: **not present** — traceability is to PRD section IDs and functional requirement IDs (FR-001–FR-014).

---

# Assumptions

| ID | Assumption | Impact if wrong |
| -- | ---------- | --------------- |
| SA-1 | Task catalog is YAML, one file per task set, under `config/task_catalog/` | **Resolved — SD-2** |
| SA-2 | Default output directory is `./output/` relative to invocation cwd | **Resolved — SD-3** |
| SA-3 | Python 3.11+ is acceptable for the target environment | Setup.md version pinning |
| SA-4 | OpenAI `gpt-4o` is configured for all four agents via `OPENAI_API_KEY` | **Resolved — SD-1** |
| SA-5 | Deterministic compliance checks are implemented in Python alongside the Checker agent | If LLM-only validation, reproducibility risk |
| SA-6 | Test fixtures may contain synthetic task IDs for development; production catalog is stakeholder-owned | Test/production separation |
| SA-7 | PRD Assumption A1 (3-week manual ramp baseline) carries forward for pilot metrics | Metric validity |
| SA-8 | Department is metadata only in MVP; `applicable_departments` in catalog is not used for filtering until a future PRD revision | **Resolved — SD-7**; future department-aware filtering requires PRD change |
| SA-9 | No `@frontend.eng` epic is needed until/unless PRD adds a UI | Build phase scope |
| SA-10 | Diagnostic logs persist under `project-context/2.build/logs/{workflow_id}/` during development | Path may move to application-relative logs in Deliver |
| SA-11 | Developer and Engineer use separate role-specific YAML task sets | **Resolved — SD-5** |
| SA-12 | `source_reference` values in catalog are URL strings | **Resolved — SD-8** |
| SA-13 | CLI entry point is named `onboard` | **Resolved — SD-6** |

**Inherited from PRD (not independently verified):** A1–A6 in PRD §17.

---

# Open Questions

### Resolved (stakeholder 2026-08-19)

| # | Question | Resolution |
| - | -------- | ---------- |
| ~~OQ-3~~ | Department-specific tasks within AI Engineering? | **No** — department is metadata only for MVP (SD-7) |
| ~~OQ-5~~ | LLM provider/model? | **OpenAI `gpt-4o`** (SD-1) |
| ~~OQ-6~~ | Output path convention? | **`./output/`** default (SD-3) |
| ~~OQ-7~~ | Task IDs inline vs appendix? | **Audit appendix only** (SD-4) |
| ~~OQ-8~~ | Catalog format? | **YAML, one file per task set** (SD-2) |
| ~~OQ-9~~ | Developer vs Engineer distinction? | **Distinct roles**, separate task-set files (SD-5) |
| ~~OQ-10~~ | `source_reference` format? | **URL string** (SD-8) |
| ~~OQ-11~~ | CLI executable name? | **`onboard`** (SD-6) |

### Remaining — stakeholder input still required

| # | Question | Architectural impact | PRD/MRD ref |
| - | -------- | -------------------- | ----------- |
| OQ-1 | What are the actual tasks in each placeholder task set? | Blocks production-valid output | PRD §4.1, §18 Q1 |
| OQ-2 | Who owns approval and maintenance of each task set? | Governance and change-control process | PRD §18 Q2 |
| OQ-4 | What defines "ramp complete" for each of the five roles? | Pilot success measurement | PRD §18 Q4 |
| OQ-12 | Is a catalog validation-only CLI mode (`--validate-catalog`) in scope for MVP or deferred? | CLI surface area | PRD Could Have |
| OQ-13 | Where should diagnostic artifacts be stored in production vs development? | Logging architecture | SA-10 |
| OQ-14 | Are there geographic or regulatory compliance jurisdictions that affect compliance task content? | Security/compliance scope | MRD §Open Q10 |

---

# Audit

| Field | Value |
| ----- | ----- |
| **Timestamp** | 2026-08-19 (updated 2026-08-19 — stakeholder decisions) |
| **Persona ID** | `system-arch` |
| **Action** | `create-sad` (updated with stakeholder clarifications) |
| **Artifact** | `project-context/1.define/sad.md` |
| **Resolved `AAMAD_TARGET_RUNTIME`** | `crewai` |
| **LLM** | OpenAI `gpt-4o` via `OPENAI_API_KEY` (SD-1) |
| **Process model** | Sequential CrewAI crew with application-level retry state machine |
| **Agent count** | 4 (Role Analyst, Plan Builder, Compliance Checker, Document Writer) |
| **Primary interface** | CLI `onboard` (SD-6); default output `./output/` (SD-3) |
| **Language** | Python (`aamad.config.yml`) |
| **Task catalog** | YAML one-file-per-set; content still placeholder |
| **Department** | Metadata only; no applicability filtering (SD-7) |
| **Task IDs in Markdown** | Audit appendix only (SD-4) |
| **User stories** | None present |
| **MRD referenced** | Yes |
| **Prompt Trace** | Not captured inline; SAD is architecture specification, not runtime execution |
