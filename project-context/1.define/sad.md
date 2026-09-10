# System Architecture Document — Automated Employee Onboarding Workflow

**Persona:** `system-arch`
**Action:** `create-sad`
**Phase:** Define
**Intended path:** `project-context/1.define/sad.md`
**Product:** Automated Employee Onboarding Workflow
**Target organization:** AI Engineering
**Selected runtime:** CrewAI
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (environment unset; `aamad.config.yml` `runtime.target: crewai`)
**Primary interface:** CLI `onboard` (SD-6); minimal UI wrap at `src/onboarding-ui/` (SD-10)
**Status:** Architecture handoff candidate; aligned to 2026-08-20 template-aligned PRD; Developer catalog content supplied 2026-08-27; other roles remain placeholder; application code consolidated under `src/` (2026-08-28)

---

## Stakeholder Decisions (2026-08-19)

Recorded here as the architectural decision log. The 2026-08-20 PRD absorbs SD-1 through SD-8 as product constraints (PRD Sources item 3; PRD risk “SAD/PRD drift”).

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
| SD-10 | Frontend / UI Requirement | The onboarding-plan tool will include a frontend UI, in addition to the existing CLI. The UI wraps the existing CLI/agent core rather than replacing it — the underlying models, catalog loader, four-agent crew, and deterministic compliance checker remain unchanged and are called by the UI, not rebuilt for it. Date: August 27, 2026. Raised by: Professor Carmelo Iaria, in a follow-up meeting after the initial SAD review. Supersedes: prior CLI-only framing implied by SD-4 (CLI name `onboard`). SD-4 is not reversed — the CLI remains the underlying interface and stays available for testing/automation — this decision adds a UI layer on top of it. Scope: minimal UI — one screen with a form for the three inputs (role, department, start date), and a results view showing either the two generated files (on compliance PASS) or a clear failure reason (on compliance FAIL). No additional functionality beyond what the CLI already exposes. Sequencing: UI work begins only after the Developer happy path is fully proven via the CLI (Steps 1–7: models, catalog loader, CLI, deterministic compliance rules, four-agent crew, Markdown generation, automated tests). The UI is an interface change, not a product-logic change, and is not built concurrently with unproven compliance logic. Rationale: keeps the trust-boundary architecture (catalog-only tasks, fail-closed compliance, agent role separation) fully intact regardless of interface. Avoids rework of already-completed and tested build steps. Reduces risk by not introducing two unproven components (compliance logic + new UI) at the same time. |
| SD-9 | Developer task catalog | Compact source `project-context/2.build/developer-tasks.yaml`; normalized one-file-per-set copies under `project-context/2.build/task_catalog/` |

---

## Context & Instructions

This SAD specifies the MVP system architecture for a CrewAI-based multi-agent application that generates role-aware 30/60/90-day onboarding plans and manager checklists from an authoritative task catalog. It aligns with the PRD's sequential agent workflow, deterministic validation gate, zero-invention task policy, and functional requirements FR-001–FR-016.

**Input artifacts:**

| Artifact | Path | Status |
| -------- | ---- | ------ |
| PRD | `project-context/1.define/prd.md` | Complete (2026-08-20 template-aligned `create-prd`) |
| Prior PRD (comparison only) | `project-context/1.define/prd-2026-08-09.md` | Preserved; not authoritative |
| MRD | `project-context/1.define/mrd.md` | Complete (required; not skipped) |
| User stories | `project-context/1.define/user-stories/` | Not present |
| Project config | `aamad.config.yml` | Present (`runtime.target: crewai`, `language.primary: python`) |
| Developer catalog (source) | `project-context/2.build/developer-tasks.yaml` | Compact stakeholder YAML (15 tasks) |
| Task catalog (normalized) | `project-context/2.build/task_catalog/` | PRD `TaskDefinition` split; Developer content only |

---

# 1. MVP Architecture Philosophy & Principles

## 1.1 MVP Design Principles

| Principle | Architectural implication |
| --------- | ------------------------- |
| **Catalog authority over model inference** | Task definitions live in version-controlled configuration; agents manipulate `task_id` references only. Titles and descriptions are resolved at render time from the catalog. |
| **Separation of construction and validation** | Plan Builder constructs candidates; Compliance Checker independently validates. The Builder never self-certifies. |
| **Deterministic control boundaries** | Input validation, retry counting, schema validation, PASS eligibility, and document-write gating are implemented in application code—not delegated to LLM discretion (PRD §5). |
| **Fail closed** | Terminal compliance failure produces no approved onboarding artifacts (FR-010). |
| **Observable by default** | Each workflow run records `workflow_id`, handoff payloads, validation findings, retry count, and final status for auditability (PRD §3 Infrastructure). |
| **Adapter isolation** | Employee context acquisition and future HRIS/IdP integrations are isolated behind `EmployeeContextProvider`; agent logic remains vendor-agnostic (FR-014). |
| **Minimal viable surface** | MVP is a CLI batch tool with local Markdown output. SD-10 adds a single-screen UI that calls the same core; no live enterprise integrations, no task execution. |
| **Correctness over completeness** | Prefer fail-closed non-success over emitting a plan that violates mandatory coverage or traceability (PRD §5). |

## 1.2 Core vs Future Features

### MVP (P0 — in scope)

- CLI `onboard` accepting `role`, `department`, `start_date` (FR-001)
- Pre-flight input validation; crew never invoked on invalid input (FR-002)
- Authoritative task-catalog loader with startup structural/schema validation (FR-015)
- Authoritative task-set YAML (one file per set). **Developer** content is stakeholder-supplied (SD-9). UI Designer, UX Researcher, Product Manager, Engineer, and `shared_tasks` remain empty placeholders and SHALL NOT be treated as production-valid (FR-015, PRD A2)
- Four specialized CrewAI agents in sequential process (PRD §3)
- Structured Pydantic handoffs between all agent boundaries (PRD §3)
- Deterministic retry controller (`max_builder_retries = 2` after initial candidate; three evaluations maximum) (FR-009)
- Compliance Checker as mandatory validation gate (FR-007–FR-010)
- Markdown outputs: `onboarding-plan.md`, `manager-checklist.md` (FR-011, FR-012)
- Task IDs in Audit Appendix only (FR-011, FR-012, SD-4)
- Configurable output directory: default `./output/`, override `--output-dir` or `ONBOARDING_OUTPUT_DIR` (FR-016, SD-3)
- `CliEmployeeContextProvider` adapter (FR-014)
- Unit and integration tests mapped to acceptance criteria (`aamad.config.yml` `testing.*`; PRD §7 Validation Test Matrix)
- Type checking (`coding_standards.type_checking: true`)
- Minimal onboarding UI wrapping the CLI/API core (SD-10): `src/onboarding-ui/` plus FastAPI `src/onboarding/api.py`. Does not replace `onboard`.

### Should Have (P1 — implement if they do not expand P0 scope)

PRD §4 Enhanced Features. Several items are also required by config or by P0 invariants:

| Item | Architectural treatment |
| ---- | ----------------------- |
| Structured run diagnostics on failure (labeled as diagnostics, not approved plans) | Include in MVP architecture: PRD §3 says each run SHOULD record diagnostic fields; aligns with “observable by default” |
| Human-readable compliance findings in CLI errors | Include: required by PRD §6 failure copy |
| Deterministic filenames | Optional P1; default names `onboarding-plan.md` and `manager-checklist.md` are sufficient for P0 |
| Duplicate-task detection | Include: implied by Checker uniqueness check |
| Unit-test fixtures for all five roles | Include: config-required |
| Integration tests mapped to acceptance criteria | Include: config-required |
| Deterministic application-level schema validation around runtime outputs | Include: P0 invariant (PRD §5 deterministic controls) |

### Future Work (P2 — explicit deferrals)

From PRD §4 Future Features. Any proposal of these items SHALL be classified as Future Work, not MVP.

| Capability | Rationale for deferral |
| ---------- | ---------------------- |
| Rich chat UI, extra screens, pause/cancel | PRD §6; SD-10 covers only a single form + results page wrapping the existing core |
| Live HRIS integration | PRD §3 Integration; adapter boundary only |
| Live identity-provider integration | PRD §3 Integration |
| Account provisioning and permission assignment | PRD P2 / non-goals |
| Executing onboarding tasks | PRD P2 |
| Task completion tracking, notifications, reminders | PRD P2; MRD journey narrowed |
| Exact calendar deadline inference | PRD FR-006; bucket rules only |
| Additional roles or role aliases | PRD FR-004 |
| Dynamic / catalog task invention by agents | PRD §3 zero-invention |
| Legal/compliance inference beyond the catalog | PRD §5; MVP uses catalogued `COMPLIANCE_LEGAL` tasks only |
| Performance evaluation or employment decisions | PRD P2 |
| Enterprise AuthN/AuthZ, SSO, IAM | No live integrations in MVP (A5) |
| JSON machine-readable result alongside Markdown | PRD P2 |
| Dry-run mode, catalog lint CLI, plan-diff across catalog versions | PRD P2 |
| Alternative Markdown templates / `--verbose` | PRD P2 |
| Onboarding analytics dashboard | PRD P2 |
| Horizontal scaling and multi-region deployment | Internal moderate volume (MRD A6); correctness-first |
| Advanced APM and cost dashboards | Baseline logging sufficient for MVP |

## 1.3 Technical Architecture Decisions

| Decision | Choice | Rationale | Trace |
| -------- | ------ | --------- | ----- |
| Runtime | CrewAI | Sequential process and structured outputs fit the validation-gate workflow | PRD §3; `aamad.config.yml` `runtime.target` |
| Language | Python 3.11+ | `language.primary: python`; CrewAI ecosystem | Config; SA-3 |
| Process model | Sequential forward path; retry loop in application orchestrator | Ordered Role Analyst → Plan Builder → Compliance Checker → Document Writer | PRD §3 |
| Agent count | 4 | PRD-defined specialization with distinct validation boundaries | PRD §3 Core Agent Definitions |
| Delegation | `allow_delegation=false` | PRD §3; no manager pattern justified | PRD §3 |
| Interface | CLI `onboard` plus SD-10 UI wrap | CLI remains the underlying interface; UI calls the same core via HTTP | PRD §6, FR-001, SD-10 |
| Persistence | None (filesystem only) | Catalog and outputs are local files; no database | PRD §3 Integration |
| Inter-agent data format | Pydantic models / JSON schemas | Reduces parsing ambiguity; malformed output is a failed stage | PRD §3 |
| Streaming | Not required | Batch CLI; success/failure reported after completion | PRD §6 |
| Memory | Disabled (`memory=False`) | Reproducibility; each run is stateless aside from persisted diagnostics | PRD §3; CrewAI adapter |
| Compliance retry limit | Application invariant `max_builder_retries = 2` | Product rule; not delegated to CrewAI defaults | FR-009; PRD Retry state machine |
| LLM provider | OpenAI | Stakeholder decision SD-1 | SD-1; PRD §3 |
| LLM model | `gpt-4o` | Stakeholder decision SD-1 | SD-1 |
| Temperature / token caps | Record in `setup.md` Audit; SAD recommends ≤ 0.3 for reproducibility | PRD Audit defers numeric caps to Build/setup | PRD Audit; CrewAI adapter |
| Task catalog format | YAML, one file per task set | Stakeholder decision SD-2 | SD-2; PRD §3 Task-Set Model |
| Default output path | `./output/` | Stakeholder decision SD-3 | SD-3; FR-016 |
| CLI executable | `onboard` | Stakeholder decision SD-6 | SD-6; FR-001 |
| Department filtering | None in MVP | Department recorded in outputs; task selection by role only | SD-7; FR-003; PRD A3 |
| Task ID presentation | Audit appendix only | End-user sections show titles/descriptions; IDs in appendix | SD-4; FR-011, FR-012 |
| `source_reference` | URL string | Catalog field holds a URL to authoritative policy/doc | SD-8 |
| Type checking | Required | `coding_standards.type_checking: true` | Config; PRD §5 |
| Max file lines | Prefer ≤ 400 | Split modules unless clarity suffers | Config; PRD §5 |

### Frontend decision (SD-10)

The PRD originally scoped MVP to CLI only. **SD-10 (2026-08-27)** adds a minimal UI that wraps the existing CLI/agent core rather than replacing it. Scope: one screen with role / department / start date, and a results view for the two Markdown files (PASS) or a failure reason (FAIL). Implementation: `src/onboarding-ui/` (port 5174) calling `src/onboarding/api.py`.

`aamad.config.yml` UI keys SHALL NOT be used to justify extra screens, chat, or theming beyond that wrap. `src/frontend/` is a separate Critical Research Workflow prototype and is **not** the onboarding product.

---

# 2. Multi-Agent System Specification

## 2.1 Agent Architecture

Four specialized agents operate within a single CrewAI crew. Each agent has a narrow responsibility boundary aligned with PRD §3. Agents SHALL NOT parse CLI arguments directly or write arbitrary files outside defined responsibility.

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
| **Goal** | Select exactly the authoritative task IDs that apply to the requested role |
| **Inputs** | `OnboardingRequest`, authoritative task catalog, `WorkflowContext` |
| **Output** | `RoleAnalysis` (task IDs + metadata only) |
| **Allowed actions** | Select active tasks from shared, compliance/legal, IT provisioning, matching role-specific, and team-integration task sets filtered by **role only**; return identifiers with task-set origin for each ID; `department` is carried as metadata and does not affect applicability in MVP (SD-7, FR-003) |
| **Prohibited** | Create tasks, alter descriptions, sequence, assign buckets, omit mandatory applicable tasks, perform compliance approval |
| **Tools** | Read-only access to task catalog repository; no write, network, or shell tools |
| **Memory** | None (`memory=false`) |
| **Delegation** | `false` |

### Agent 2 — Plan Builder

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Transform applicable task set into ordered 30/60/90 onboarding plan using catalog IDs only |
| **Inputs** | `RoleAnalysis`, task catalog, priority rules, optional `PlanRevisionRequest` on retry |
| **Output** | `CandidatePlan` |
| **Allowed actions** | Assign each task to exactly one bucket (`30_DAY`, `60_DAY`, `90_DAY`) respecting `allowed_buckets`; sequence within priority hierarchy; on retry, modify only invalid aspects identified by the Checker |
| **Prohibited** | Invent tasks, infer calendar deadlines, remove correctly selected mandatory tasks to fix unrelated failures |
| **Priority order** | `COMPLIANCE_LEGAL` > `IT_PROVISIONING` > `ROLE_ENABLEMENT` > `TEAM_INTEGRATION` (FR-005) |
| **Tools** | Read-only task catalog access |
| **Memory** | None |
| **Delegation** | `false` |

### Agent 3 — Compliance Checker

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Independent validation gate; return `PASS` or `REJECT` with machine-readable findings |
| **Inputs** | `RoleAnalysis`, `CandidatePlan`, task catalog, priority rules, current retry count |
| **Output** | `ComplianceResult` |
| **Validation checks** | Mandatory compliance coverage, mandatory provisioning coverage, traceability, applicability, uniqueness, bucket validity, priority integrity, role integrity (FR-007, FR-008) |
| **Prohibited** | Modify plans, bypass checks, return `PASS` with error-level findings |
| **Tools** | Read-only task catalog access; deterministic validation helpers (implemented in code, not LLM-only) |
| **Memory** | None |
| **Delegation** | `false` |

**Architecture note:** Critical validation logic (task ID existence, mandatory coverage counts, bucket rule enforcement, duplicate detection) SHALL be implemented as **deterministic Python functions** invoked by or alongside the Checker agent. The LLM may assist with priority-integrity assessment, but PASS eligibility MUST be computed deterministically from boolean check results (PRD Handoff D; PRD §5). PASS requires every boolean check `true` and no error-level findings.

### Agent 4 — Document Writer

| Attribute | Specification |
| --------- | ------------- |
| **Goal** | Render an already-approved plan into Markdown using catalog-resolved titles and descriptions |
| **Precondition** | `ComplianceResult.status == PASS` |
| **Inputs** | `ApprovedPlan`, task catalog |
| **Outputs** | `onboarding-plan.md`, `manager-checklist.md` in the resolved output directory |
| **Allowed actions** | Resolve task titles/descriptions from catalog; format presentation; append **Audit Appendix** with task IDs, catalog version, and hash |
| **Prohibited** | Execute without PASS; introduce new tasks; alter authoritative task meaning; expose raw `task_id` inline in 30/60/90 sections or checklist items (SD-4, FR-011, FR-012) |
| **Tools** | Read-only catalog access; filesystem write to configured output directory only |
| **Memory** | None |
| **Delegation** | `false` |

## 2.2 Task / Turn Orchestration

### Execution flow

```text
1. CLI parses and validates inputs (FR-002)
2. Load and validate task catalog (structural + schema) (FR-015)
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

Product state machine (PRD Retry and Failure State Machine):

```text
BUILD attempt 1 → CHECK
    PASS → WRITE → SUCCESS
    REJECT → BUILD attempt 2 → CHECK
        PASS → WRITE → SUCCESS
        REJECT → BUILD attempt 3 → CHECK
            PASS → WRITE → SUCCESS
            REJECT → TERMINAL FAILURE
```

Retry counter SHALL NOT reset during one workflow. No fourth build attempt. On terminal failure: do not invoke Document Writer; do not emit approved plan or checklist; emit structured diagnostics labeled as a failed-run diagnostic; return non-success CLI status.

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

CrewAI task context chaining (`Task.context`) passes prior structured outputs forward within the crew execution path. The **Workflow Orchestrator** remains responsible for injecting retry state and re-invoking Plan Builder outside the linear crew sequence when compliance rejects. Role Analyst SHALL NOT rerun solely because sequencing failed.

### Handoff schemas (canonical)

Aligned to PRD §3 Shared Context and Handoffs. All schemas SHALL be implemented as Pydantic v2 models with strict validation. Unknown fields rejected. An intermediate output containing an unknown `task_id` SHALL be rejected.

| Handoff | Schema | Required fields / constraints | PRD reference |
| ------- | ------ | ----------------------------- | ------------- |
| A: CLI → Role Analyst | `OnboardingRequest` | `workflow_id`, `role`, `department`, `start_date`, `task_catalog_version`. Preconditions: valid role, department, start date, catalog loaded | Handoff A |
| B: Role Analyst → Plan Builder | `RoleAnalysis` | `applicable_tasks` as `{task_id, source_task_set, category, mandatory}` only. Every `task_id` MUST exist in the catalog | Handoff B |
| C: Plan Builder → Compliance Checker | `CandidatePlan` | `build_attempt` (1=initial, 2=first retry, 3=final retry); per-bucket `{task_id, sequence}`. No free-form task definitions | Handoff C |
| D: Checker decision | `ComplianceResult` | `status: PASS \| REJECT`; boolean checks; findings (`rule_id`, `severity: ERROR`, `task_ids`, `message`). PASS requires every boolean check `true` and no error-level findings | Handoff D |
| E: Rejection → Plan Builder | `PlanRevisionRequest` | Previous candidate, compliance result, next build attempt | Handoff E |
| F: Approved → Document Writer | `ApprovedPlan` | Only when status is PASS | Handoff F |

### Error handling, retries, and timeouts

| Control | Behavior |
| ------- | -------- |
| Invalid CLI input | Fail before crew invocation; exit non-zero; no files generated (FR-002) |
| Malformed agent output | Treat as stage failure; do not silently parse or guess |
| Compliance REJECT | Return structured findings to Plan Builder; increment `build_attempt` |
| Max retries exhausted | Terminal failure; no Document Writer; diagnostic artifact optional and MUST be labeled as failed-run diagnostic |
| Agent timeout | Configurable per-task `max_execution_time`; failure treated as stage error |
| CrewAI `max_iter` | ≤ 12 per agent task (adapter default; PRD §3 runtime notes) |
| CrewAI `max_retry_limit` | ≥ 2 at task level; product retry limit remains orchestrator-controlled |
| LLM/API failure | Non-success CLI result; no approved outputs |
| Cancellation | CLI SIGINT → abort run; SHALL not leave approved partial outputs (PRD §5) |
| Recovery | Operator re-runs the CLI; no workflow resume/memory in MVP |

### Performance budgets

| Budget | MVP target | Notes |
| ------ | ---------- | ----- |
| End-to-end CLI run (happy path) | No hard SLA; monitor during pilot | Depends on LLM latency (PRD §5) |
| Max build attempts | 3 | Product invariant |
| Max agent iterations | 12 per task | CrewAI adapter baseline |
| Concurrent workflows | 1 per CLI invocation | No multi-tenant server in MVP |
| Token budget | Configure per OpenAI `gpt-4o` usage; log per run when available | No dollar ceiling supplied; do not invent a budget (PRD §7) |

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
- Product-level PASS eligibility and retry limits remain in application code (PRD §5; FR-009)

### LLM configuration

| Setting | Value |
| ------- | ----- |
| Provider | OpenAI (SD-1) |
| Model | `gpt-4o` (SD-1) |
| API key env var | `OPENAI_API_KEY` |
| Temperature | Recommend ≤ 0.3 for reproducibility; exact value and token caps recorded in `setup.md` Audit (PRD Audit) |
| Agent scope | Same provider/model for all four agents unless setup.md documents a justified exception |

Secrets MUST NOT appear in task catalogs, Markdown outputs, or Prompt Trace.

---

# 3. Frontend Architecture Specification

## 3.1 Scope determination

**CLI remains primary (SD-6).** **SD-10** adds a minimal graphical wrap: `src/onboarding-ui/` (Vite + React + TypeScript, port 5174). No chat UI, no extra routes, no pause/cancel. The Critical Research Workflow app at `src/frontend/` (port 5173) is out of onboarding product scope.

## 3.2 CLI as the primary interface

The CLI layer fulfills the "frontend" responsibility for operator interaction. Human–agent communication is batch, not conversational: the operator supplies three validated fields; agents do not ask clarifying questions in MVP.

### Technology stack

| Component | Selection | Source |
| --------- | --------- | ------ |
| CLI framework | `click` (`onboard` console script in `pyproject.toml`) | Implemented; recorded in `setup.md` |
| Language | Python 3.11+ | `aamad.config.yml` |
| Output | stdout/stderr + local Markdown files | PRD §6 |

### Interface contract

**Invocation:**

```text
onboard --role "Developer" --department "AI Engineering" --start-date "YYYY-MM-DD" [--output-dir PATH]
```

- **Executable name:** `onboard` (SD-6); registered as console script entry point in `pyproject.toml`
- **Default output directory:** `./output/` (SD-3, FR-016); overridable via `--output-dir` or `ONBOARDING_OUTPUT_DIR`

**Required arguments:**

| Argument | Validation |
| -------- | ---------- |
| `--role` | Must match one of five canonical `SupportedRole` values. Role matching uses canonical identifiers only; no alias support in MVP |
| `--department` | Required; non-whitespace after trim; no department enumeration |
| `--start-date` | ISO `YYYY-MM-DD`; reject invalid calendar dates; SHALL NOT infer a missing date from system time |

**Optional arguments:**

| Argument | Purpose | Priority |
| -------- | ------- | -------- |
| `--output-dir` | Override default `./output/` (SD-3, FR-016) | P0 |
| `--verbose` | Not in MVP | P2 |
| Catalog lint / dry-run | Not in MVP | P2 |

### User experience states

| State | CLI behavior | Exit code |
| ----- | ------------ | --------- |
| Success | Display role, department, start date, Validation PASS, retries used (0–2), output paths | 0 |
| Input failure | Error message before agents; supported roles listed on role errors; "No files were generated" | non-zero |
| Terminal compliance failure | Attempt counts, final REJECT, structured human-readable findings; no approved outputs | non-zero |
| Configuration error | Catalog load/validation failure before agent execution | non-zero |
| Do not claim success | Never report success when validation failed | non-zero |

### Accessibility and responsive design

Not applicable to CLI MVP. Future web UI would require WCAG considerations.

---

# 4. Backend Architecture Specification

## 4.1 Application structure

The product core is a **Python package** (`src/onboarding/`) exposing CLI `onboard` and a thin FastAPI wrap for SD-10. Vite apps also live under `src/`. Prefer files at or below `max_file_lines: 400`. Type checking is required.

**Implemented layout (stakeholder 2026-08-28: all application code under `src/`):**

```text
aamad-project/
├── pyproject.toml                   # src-layout; packages.find include = ["onboarding*"]
├── .env.example
├── config/
│   ├── agents.yaml
│   └── tasks.yaml
├── src/
│   ├── onboarding/                  # Python package (CLI, API, catalog, crew, compliance)
│   │   ├── cli.py                   # onboard entrypoint (SD-6)
│   │   ├── api.py                   # FastAPI wrap of run_onboarding (SD-10)
│   │   ├── catalog.py
│   │   ├── models.py
│   │   ├── compliance.py
│   │   ├── workflow.py
│   │   ├── rendering.py
│   │   ├── crew_runtime.py
│   │   └── stubs.py
│   ├── onboarding-ui/               # Onboarding Vite + React UI (port 5174)
│   └── frontend/                    # Critical Research Workflow prototype (port 5173)
├── tests/                           # Python tests at repo root
└── project-context/2.build/
    ├── developer-tasks.yaml
    └── task_catalog/                # normalized one-file-per-set copies
```

An earlier nested scaffold (`src/cli/`, `src/catalog/`, `config/task_catalog/` as the loader root) was a recommendation only. The stakeholder specified consolidation under `src/`. Catalog YAML currently loads from `project-context/2.build/` (see SA-17).

Development agents MUST NOT populate placeholder YAML with model-generated onboarding tasks (PRD §3 Authoritative Task-Set Model).

## 4.2 API architecture

**CLI remains the product contract (PRD §3, FR-001).** SD-10 adds a **thin HTTP wrap** so the UI can call the same `run_onboarding` core. Paths and JSON live in `project-context/1.define/onboarding-backend-spec.md`. Implementation: `src/onboarding/api.py` (`POST /runs`, `GET /runs/{runId}`). This is not a second crew and not a research-run API.

Future adapter boundary (not implemented as a live integration):

```text
EmployeeContextProvider
  get_employee_context(input_reference) -> EmployeeContext

EmployeeContext (MVP subset)
  role: SupportedRole
  department: string
  start_date: date
```

Future HRIS adapter may extend `EmployeeContext` with additional fields (employee identity, manager, employment type, location, legal entity — PRD §3) without modifying agent business logic. No HRIS or IdP vendor is selected.

## 4.3 Data architecture

| Data | Storage | MVP persistence |
| ---- | ------- | ----------------- |
| Task catalog | Version-controlled YAML files (one file per task set) | Filesystem |
| Workflow diagnostics | JSON log per run | Filesystem under `project-context/2.build/logs/` or configurable path |
| Generated plans | Markdown files under `./output/` by default | Filesystem output directory |
| Workflow state | In-memory during run | None across runs (no resume) |

**No database** is required for MVP. Auditability is satisfied by structured diagnostic logs and catalog version/hash embedded in outputs (FR-013).

### Task catalog schema

Each task conforms to PRD §3 `TaskDefinition`:

```text
task_id, title, description, task_set, category, applicable_roles,
applicable_departments, mandatory, allowed_buckets, source_reference,
active, version
```

Allowed `category` values: `COMPLIANCE_LEGAL`, `IT_PROVISIONING`, `ROLE_ENABLEMENT`, `TEAM_INTEGRATION`.

**Format decisions (SD-2, SD-8):**

- One YAML file per task set. **Define/Build staging path:** `project-context/2.build/task_catalog/` (SD-9). Runtime default remains `./config/task_catalog/` once the application is scaffolded (SA-1)
- `source_reference` MUST be a URL string pointing to the authoritative policy or document (SD-8). Developer sources currently use `https://intranet.example.com/...` placeholders (PRD Open Question 6 still open for the real corpus)
- `applicable_departments` remains in schema for future use; MVP Role Analyst ignores department for filtering (SD-7)

**Role-specific task sets (SD-5):** `Developer` and `Engineer` are distinct `SupportedRole` values. Applicability uses `developer_tasks.yaml` vs `engineer_tasks.yaml` respectively—never a shared ambiguous role bucket.

**Developer catalog inventory (SD-9):** 15 stakeholder tasks, split as COMP-001–004 → `compliance_legal_tasks.yaml`; IT-001–004 → `it_provisioning_tasks.yaml`; ROLE-001–004 → `developer_tasks.yaml`; TEAM-001–003 → `team_integration_tasks.yaml`. All have `applicable_roles: [Developer]` only. Compact source field names (`id`, `category: compliance|it_setup|role_work|team_intro`, `source`) are not the runtime schema.

Startup validation SHALL fail if (FR-015):

- Required task-set YAML files are missing
- Any task lacks required fields
- Duplicate `task_id` values exist
- `task_id` format is invalid
- `source_reference` is not a valid URL string
- Unique `task_id`, applicability, category, source reference, or bucket eligibility is missing

Unresolved placeholders are development-only and SHALL NOT be treated as production-valid.

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

Logging hooks per CrewAI adapter and PRD §3 Infrastructure:

- Each run SHOULD record `workflow_id`, inputs, catalog version/hash, selected task IDs, candidate plans, validation findings, retry count, final status, and output paths
- Prompt Trace captured before agent execution (redact secrets)
- Lifecycle events (task start/stop, retries, guardrail outcomes) in Trace Log
- Persist under `project-context/2.build/logs/{workflow_id}/` during Build
- Data minimization: persist workflow inputs and catalog references needed for audit, not extra employee PII (PRD §5)

## 4.5 Authentication and secrets

| Secret / config | Env var | Notes |
| --------------- | ------- | ----- |
| OpenAI API key | `OPENAI_API_KEY` | Required for CrewAI LLM (SD-1); never committed |
| Output directory override | `ONBOARDING_OUTPUT_DIR` (optional) | Default: `./output/` (SD-3, FR-016) |
| Catalog path override | `ONBOARDING_CATALOG_PATH` (optional) | Default: `./config/task_catalog/` |

MVP requires **no HRIS, IdP, or operator authentication** (PRD A5). LLM provider secrets SHALL NOT be embedded in catalogs, code, or generated Markdown.

---

# 5. DevOps & Deployment Architecture

## 5.1 Deployment model

The MVP deploys as a **local Python application**: CLI `onboard` plus optional SD-10 UI (`src/onboarding-ui/` + `uvicorn onboarding.api:app`) on a developer or coordinator workstation, or CLI in CI for automated acceptance tests. Cloud hosting is Future Work for Deliver (PRD §3 Infrastructure).

| Aspect | MVP approach |
| ------ | ------------ |
| Hosting | Local execution; no server deployment required |
| Compute | Sufficient for one Python CrewAI process and outbound OpenAI API calls; no cluster |
| Network | Outbound LLM provider access only; no HRIS/IdP network dependency |
| Containerization | Optional Docker image for reproducibility (Future Work unless `@devops.eng` scopes it in Deliver) |
| Health check | CLI `--version` and catalog validation subcommand are P2 (catalog lint CLI); not required for P0 |
| Process model | Single-shot batch; one workflow per invocation |
| Availability | N/A as a hosted SLA; available when the operator can run the CLI and reach the LLM provider |

## 5.2 CI/CD (minimal MVP)

Per `aamad.config.yml` and delivery workflow, CI pipeline stages:

1. **Lint** — `ruff` or project-standard linter
2. **Type check** — `mypy` or `pyright` (`type_checking: true`)
3. **Unit tests** — schema validation, compliance rules, input validation (`testing.require_unit_tests: true`)
4. **Integration tests** — full crew workflow against test fixtures for all five roles (`testing.require_integration_tests: true`; `map_to_acceptance_criteria: true`)
5. **Build** — package installable artifact (`pip install .` or equivalent)
6. **Dependency audit** — `security.dependency_audit: true` in Build/Deliver

No live deploy stage without explicit operator authorization.

Deliver-phase `@devops.eng` owns deploy configs, runbook, and user guide (`documentation.require_user_guide: true`) after QA and security assessment.

## 5.3 Observability

| Signal | MVP | Future |
| ------ | --- | ------ |
| Structured run logs | Yes — workflow_id, handoffs, findings | |
| Prompt Trace | Yes — per agent, redacted | |
| Metrics/APM | No | Datadog/similar if product evolves to service |
| Cost/token telemetry | Log per run when provider supports; no invented budget | Dashboards (P2) |

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

Conceptual layers (PRD §3):

```text
CLI Layer
    → Input Validation
    → Employee Context Adapter
    → Task Catalog Repository
    → Workflow Orchestrator
    → Runtime agents (CrewAI)
    → Deterministic Validation / Retry Controller
    → Document Renderer
    → Filesystem Output
```

## 6.2 External integrations (MVP)

**None.** PRD §3 Integration Requirements. Network dependency is outbound LLM provider access only.

## 6.3 Future integration adapters

| Adapter | Interface | MVP status |
| ------- | --------- | ---------- |
| CLI | `CliEmployeeContextProvider` | Implemented |
| HRIS | `HrisEmployeeContextProvider` | Future Work — PRD §3 |
| Identity Provider | `IdpProvisioningContextProvider` | Future Work — PRD §3 |

Agent business logic MUST NOT depend on vendor-specific field names, authentication, or transport (FR-014).

## 6.4 Error propagation

| Layer | Error type | Operator-visible result |
| ----- | ---------- | ----------------------- |
| CLI validation | Invalid role/date/department | Immediate error message; no crew run |
| Catalog load | Missing/malformed task set | Configuration error; no crew run |
| Agent output | Schema violation | Stage failure; diagnostic log |
| Compliance | REJECT after 3 attempts | Terminal failure message with findings; no approved files |
| Document Writer | Precondition violation (not PASS) | Blocked by orchestrator; should not occur if state machine is correct |
| LLM/API | Provider failure | Non-success CLI result; no approved outputs |
| SIGINT | Operator cancel | Abort; no approved partial outputs |

---

# 7. Performance & Scalability Specifications

## 7.1 MVP targets

| Metric | Target | Status |
| ------ | ------ | ------ |
| Mandatory compliance + provisioning coverage | 100% in every approved plan | PRD §7 — test-enforced |
| Zero invented tasks | 0 invalid task IDs in approved output | PRD §7 — test-enforced |
| Ramp-time reduction | ≥ 30% vs 3-week manual baseline | Pilot-measured hypothesis (PRD A1); not automated in MVP |
| Response time | Not specified | Open Question / monitor during pilot |
| Concurrent users | N/A — CLI batch tool | One workflow per invocation |
| Invalid inputs invoke crew | 0% | PRD §7 Technical Metrics |

The following SHALL be deterministic even when LLM reasoning is used inside constraints (PRD §5): input validation; role enumeration; task-ID existence; retry counting; max retries; output-schema validation; PASS eligibility; terminal failure; document-write eligibility.

## 7.2 Scalability path

MRD Assumption A6: internal onboarding volume is moderate; **correctness takes priority over throughput**. Scaling triggers are N/A for MVP.

Future scaling considerations (deferred):

- Service-ify CLI into an API if multi-operator or HRIS-triggered runs are needed
- Cache catalog in memory (already expected for single run)
- Parallel plan generation for batch hires

## 7.3 Token and cost controls

- Set `max_rpm` at crew level for budget stability (CrewAI adapter)
- Low temperature for deterministic agent behavior
- Model: OpenAI `gpt-4o` (SD-1); log token usage per run for pilot cost tracking
- Exact cost ceiling: not specified; do not invent a budget (PRD §7)

## 7.4 Markdown output structure (Document Writer)

Both output files SHALL follow SD-4 presentation rules (FR-011, FR-012, FR-013).

### `onboarding-plan.md`

| Section | Content |
| ------- | ------- |
| Header | Role, department, start date, task-catalog version (hash SHOULD be recorded) |
| 30-day / 60-day / 90-day | Task **title**, description, category, source URL (`source_reference`); **no inline `task_id`** |
| Audit Appendix | Table mapping display order → `task_id`, `task_set`, catalog version, `task_catalog_hash` |

### `manager-checklist.md`

| Section | Content |
| ------- | ------- |
| Header | Employee role, department, start date |
| 30/60/90 checklists | Markdown checkboxes with task titles only; **no inline `task_id`**; no extra tasks beyond the approved plan |
| Audit Appendix | Same traceability table as onboarding plan for approved task IDs |

Diagnostic JSON logs MAY include raw `task_id` values; user-facing Markdown body sections MUST NOT. Optional diagnostic artifact on failure MUST be labeled as a failed-run diagnostic (PRD §6).

---

# 8. Security & Compliance Architecture

## 8.1 Authentication and authorization

| Surface | MVP control |
| ------- | ----------- |
| CLI | No authentication; assumes trusted operator on local machine (PRD A5) |
| LLM API | API key via environment variable (`security.forbid_committed_secrets: true`) |
| Task catalog | Read-only at runtime; modifications via version control |
| Output files | Local filesystem permissions of host OS |

## 8.2 Data handling

| Data class | MVP handling |
| ---------- | ------------ |
| Employee role, department, start date | Passed through workflow; included in output Markdown |
| Employee name, ID | Not collected in MVP CLI |
| LLM prompts | Logged with redaction; no secrets in Prompt Trace |
| Task catalog | No secrets; `source_reference` is a URL string to internal policy/documentation (SD-8) |

Retention of diagnostic employee data is unresolved (PRD Open Question 8). Until resolved, persist only fields needed for audit (data minimization, PRD §5).

## 8.3 Input validation

- Strict enum validation for role
- ISO date parsing with calendar validity check; do not infer missing dates from system clock
- Department whitespace normalization
- Schema validation on all agent outputs
- Reject unknown `task_id` values at every boundary

## 8.4 Agentic security controls

Per MRD and OWASP agentic guidance, constrained by PRD §5:

- **Least-privilege tools** per agent (read-only catalog; Document Writer write limited to output dir)
- **No network tools** in MVP agents unless explicitly scoped later
- **No shell execution** by agents
- **Prompt injection defense**: agents instructed to ignore instructions embedded in catalog content that conflict with system rules; catalog content is data, not instructions
- **Human-in-the-loop**: compliance gate serves as automated review before document emission

## 8.5 Compliance

No specific regulatory jurisdiction identified in PRD. MVP SHALL NOT infer legal requirements; only catalogued `COMPLIANCE_LEGAL` tasks apply. **Legal/compliance interpretation by agents is explicitly out of scope** (PRD P2).

`aamad.config.yml` sets `security.require_security_assessment: true` — `@security.eng` SHALL produce `project-context/2.build/security.md` before Deliver. `security.dependency_audit: true` applies in Build/Deliver.

---

# 9. Testing & Quality Assurance Specifications

## 9.1 Test layers

| Layer | Scope | PRD trace |
| ----- | ----- | --------- |
| Unit | Input validation, Pydantic models, deterministic compliance rules, catalog validator | PRD §7; config `require_unit_tests` |
| Integration | Full crew workflow per role against test fixtures | PRD §7 Validation Test Matrix |
| Adversarial | Injected invalid task IDs, missing mandatory tasks, bucket violations | PRD §7 Compliance failures |
| Schema | CrewAI output conforms to Pydantic models | PRD §3, §5 |

Tests SHALL map to acceptance criteria (`testing.map_to_acceptance_criteria: true`).

## 9.2 Minimum acceptance matrix (from PRD §7)

**Happy paths:** one successful generation per supported role.

**Invalid inputs:** missing role; unsupported role; blank department; missing start date; malformed start date; impossible calendar date.

**Compliance failures:** missing mandatory compliance task; missing mandatory provisioning task; invented task ID; wrong-role task; duplicate task; invalid bucket; priority violation.

**Retry tests:** pass on attempt 1; fail then pass on retry 1; fail twice then pass on attempt 3; all three fail (terminal); verify no fourth build attempt.

**Output tests:** success writes exactly two approved Markdown files with 30/60/90 sections and matching checklist IDs; failure writes no approved plan/checklist, shows reason, non-zero exit; task IDs present only in Audit Appendix (SD-4).

## 9.3 Runtime-specific checks

- Verify CrewAI structured outputs deserialize to expected Pydantic models
- Verify Prompt Trace and diagnostic logs written per run
- Verify `task_catalog_hash` consistent across all handoffs in a run
- Verify Document Writer blocked when `ComplianceResult.status != PASS`
- Verify Checker cannot be bypassed
- Verify placeholders are not treated as production-valid (FR-015)

## 9.4 Security assessment

Required before Deliver (`aamad.config.yml`). Scope: secret handling, tool privileges, log redaction, catalog integrity, dependency audit.

## 9.5 PRD acceptance criteria (architecture coverage)

MVP is implemented when all PRD §8 Acceptance Criteria are met. Architecture maps them as follows: five-role generation (FR-004); invalid input fail-closed (FR-002); structured handoffs (PRD §3); priority rules (FR-005); mandatory coverage (FR-007); unknown IDs blocked (FR-008); Checker not bypassable; max two Builder retries (FR-009); terminal failure (FR-010); Writer after PASS only; both Markdown documents on success (FR-011, FR-012, FR-016); neither approved document on failure; adapter decoupling (FR-014); automated traceability tests (FR-013); task IDs not inline.

---

# 10. MVP Launch & Feedback Strategy

## 10.1 Pilot criteria

MVP is ready for internal operational use when:

1. Stakeholder-approved task catalog replaces placeholders for **all five roles** (PRD A2). Developer content is supplied (SD-9); other roles remain open (OQ-1)
2. All PRD §8 acceptance criteria pass in automated tests
3. One successful plan generated for each of the five roles using the production catalog
4. Security assessment complete (`security.md`) or gap explicitly accepted
5. Deliver-phase runbook and user guide exist (`documentation.require_user_guide: true`) after QA

External GTM is N/A (PRD §9). Promotion remains a Deliver-phase operational decision.

## 10.2 Success metrics (PRD-aligned)

| Metric | Target | Measurement method |
| ------ | ------ | ------------------ |
| Mandatory compliance/provisioning coverage | 100% | Automated test — PRD §7 |
| Zero invented tasks | 0 | Automated test — PRD §7 |
| Ramp-time reduction | ≥ 30% vs 3-week baseline | Pilot comparison — PRD A1 (requires baseline data and per-role “ramp complete” definition) |

Ramp-time cannot be proven by unit tests. Until A1 is replaced, the 30% target is a hypothesis.

## 10.3 Iteration priorities post-pilot

1. Populate and govern authoritative task catalog with named owners (PRD Open Questions 1–2)
2. Replace assumed ramp baseline with measured data (PRD Open Question 5)
3. Decide whether any post-MVP tasks become department-specific (PRD Open Question 3)
4. Evaluate HRIS adapter if hire events should trigger generation automatically
5. Consider JSON output, dry-run, catalog lint, and configurable templates (P2)
6. Reassess whether multi-agent complexity outperforms a deterministic workflow (MRD; PRD risk table)

---

# Implementation Guidance for AI Development Agents

Recommended build order (PRD §8 Phase 2, refined for architecture):

1. Pydantic models and handoff schemas
2. Task catalog loader and startup validator (placeholder fixtures only — do not invent production tasks)
3. CLI and input validation
4. `EmployeeContextProvider` protocol and CLI adapter
5. Deterministic compliance rules engine
6. Workflow orchestrator and retry state machine
7. CrewAI crew configuration (`agents.yaml`, `tasks.yaml`, `crew.py`)
8. Role Analyst, Plan Builder, Compliance Checker, Document Writer tasks
9. Markdown rendering templates (IDs in appendix)
10. Acceptance and adversarial test suite mapped to PRD §7 matrix
11. Diagnostics and Prompt Trace logging
12. Security assessment (`security.md`) before Deliver

**Module sequencing per AAMAD development workflow:**

| Module | Epic focus |
| ------ | ---------- |
| Module 1 | Agent/task YAML definitions + crew.kickoff() against fixtures |
| Module 2 | Catalog repository + validation + adapter interfaces; optional FastAPI wrap for SD-10 |
| Module 3 | CLI + Markdown rendering; SD-10 UI at `src/onboarding-ui/` invokes the HTTP wrap |
| Module 4 | End-to-end validation against PRD §7 test matrix and §8 acceptance criteria |

**Frontend epic (`@frontend.eng`):** `src/onboarding-ui/` (SD-10). `src/frontend/` is the unrelated Critical Research Workflow prototype.

**Invariants (conflicts SHALL be escalated, not silently changed):**

```text
SUPPORTED_ROLES =
{UI Designer, UX Researcher, Product Manager, Developer, Engineer}

PRIORITY =
COMPLIANCE_LEGAL > IT_PROVISIONING > ROLE_ENABLEMENT > TEAM_INTEGRATION

MAX_BUILDER_RETRIES = 2

APPROVED_OUTPUT_REQUIRES = ComplianceResult.status == PASS

TASK_AUTHORITY = authoritative task catalog only

LIVE_INTEGRATIONS = none in MVP

TASK_IDS_IN_USER_BODY = false (appendix only)
```

---

# Architecture Validation Checklist

- [x] PRD requirements mapped to architectural components (FR-001–FR-016)
- [x] Agents designed for domain and CrewAI runtime (4 agents, sequential + retry loop)
- [x] CLI contract defined; SD-10 HTTP wrap documented (`onboarding-backend-spec.md`); CRW prototype kept separate
- [x] Secrets via env vars only
- [x] MVP vs Future Work boundaries explicit (P0 / P1 / P2)
- [x] Resolved `AAMAD_TARGET_RUNTIME=crewai` recorded in Audit (env unset; config `runtime.target`)
- [x] Task catalog format decided (YAML, one file per task set — SD-2)
- [x] LLM provider/model selected (OpenAI `gpt-4o` — SD-1)
- [x] Output path convention confirmed (`./output/` — SD-3, FR-016)
- [x] CLI executable name confirmed (`onboard` — SD-6)
- [x] Task ID presentation confirmed (audit appendix — SD-4)
- [x] Department applicability confirmed (metadata only — SD-7)
- [x] Developer/Engineer distinction confirmed (separate task sets — SD-5)
- [x] `source_reference` format confirmed (URL string — SD-8)
- [x] Handoff schemas aligned to 2026-08-20 PRD §3 field lists
- [x] Task catalog **content** for Developer supplied (SD-9; 15 tasks)
- [ ] Task catalog **content** for UI Designer, UX Researcher, Product Manager, Engineer (and any shared tasks) still placeholder
- [ ] Catalog version field: specified in PRD/SAD, not yet implemented in audit appendix
- [ ] Security assessment (`@security.eng`) — Build/Deliver phase
- [ ] User guide (`@devops.eng`) — Deliver phase

---

# Sources

| Source | Path | Use in SAD |
| ------ | ---- | ---------- |
| PRD | `project-context/1.define/prd.md` | Authoritative requirements (2026-08-20 template-aligned): agents, schemas, CLI, FR-001–FR-016, NFRs, test matrix, P2 list |
| Prior PRD | `project-context/1.define/prd-2026-08-09.md` | Comparison only; not authoritative after 2026-08-20 rewrite |
| MRD | `project-context/1.define/mrd.md` | Context: pain points, security/observability guidance, deferral rationale; MRD journey narrowed by PRD |
| SAD template | `.cursor/templates/sad-template.md` | Document structure |
| AAMAD config | `aamad.config.yml` | Python, CrewAI runtime, type checking, testing/security/user-guide gates |
| CrewAI adapter rule | `.cursor/rules/adapter-crewai.mdc` | YAML config, sequential process, logging, guardrails |
| AAMAD core rule | `.cursor/rules/aamad-core.mdc` | Artifact contracts, determinism, audit sections |
| Stakeholder clarifications | Operator input 2026-08-19 | SD-1 through SD-8 decisions |
| Developer catalog | `project-context/2.build/developer-tasks.yaml` | Operator-supplied Developer tasks (2026-08-27); SD-9 |

User stories: **not present** — traceability is to PRD section IDs and functional requirement IDs (FR-001–FR-016).

---

# Assumptions

| ID | Assumption | Impact if wrong |
| -- | ---------- | --------------- |
| SA-1 | Task catalog is YAML, one file per task set, under `config/task_catalog/` | **Resolved — SD-2** |
| SA-2 | Default output directory is `./output/` relative to invocation cwd | **Resolved — SD-3** |
| SA-3 | Python 3.11+ is acceptable for the target environment | Setup.md version pinning |
| SA-4 | OpenAI `gpt-4o` is configured for all four agents via `OPENAI_API_KEY` | **Resolved — SD-1** |
| SA-5 | Deterministic compliance checks are implemented in Python alongside the Checker agent | If LLM-only validation, reproducibility risk |
| SA-6 | Test fixtures may contain synthetic task IDs for development; production catalog is stakeholder-owned | Test/production separation (FR-015) |
| SA-7 | PRD Assumption A1 (3-week manual ramp baseline) carries forward for pilot metrics | Metric validity |
| SA-8 | Department is metadata only in MVP; `applicable_departments` in catalog is not used for filtering until a future PRD revision | **Resolved for MVP — SD-7**; post-MVP department-aware filtering is PRD Open Question 3 |
| SA-9 | `@frontend.eng` epic is the SD-10 wrap at `src/onboarding-ui/`; `src/frontend/` is not the onboarding product | **Updated — SD-10; src/ consolidation 2026-08-28** |
| SA-10 | Diagnostic logs persist under `project-context/2.build/logs/{workflow_id}/` during development | Path and retention may change; see PRD Open Question 8 |
| SA-11 | Developer and Engineer use separate role-specific YAML task sets | **Resolved — SD-5** |
| SA-12 | `source_reference` values in catalog are URL strings | **Resolved — SD-8**; URL corpus unset (PRD Open Question 6) |
| SA-13 | CLI entry point is named `onboard` | **Resolved — SD-6** |
| SA-14 | `AAMAD_TARGET_RUNTIME` remains unset; `aamad.config.yml` `runtime.target: crewai` is the resolved adapter | Matches PRD A8 |
| SA-15 | Temperature ≤ 0.3 is an architecture recommendation, not a PRD numeric requirement | setup.md Audit owns the recorded value |
| SA-16 | Compact Developer YAML maps as: `id`→`task_id`; `source`→`source_reference`; `compliance`→`COMPLIANCE_LEGAL`; `it_setup`→`IT_PROVISIONING`; `role_work`→`ROLE_ENABLEMENT`; `team_intro`→`TEAM_INTEGRATION`. Missing fields default to `applicable_roles: [Developer]`, `applicable_departments: ["*"]`, `mandatory: true`, `allowed_buckets: [30]`, `active: true`, `version: "1.0"`. COMP/IT/TEAM items stay out of `developer_tasks.yaml` (role-enablement only) | If COMP/IT/TEAM should apply to other roles, or some tasks are optional / 60- or 90-day, catalog and Role Analyst results change |
| SA-17 | Staging catalog path is `project-context/2.build/task_catalog/` until `@project.mgr` / `@backend.eng` copy it into the generated app `config/task_catalog/` | Loader default path in SAD §4.5 still `./config/task_catalog/` |

**Inherited from PRD (not independently verified):** A1–A10 in the PRD Assumptions section.

---

# Open Questions

### Resolved (stakeholder 2026-08-19; absorbed by 2026-08-20 PRD)

| # | Question | Resolution |
| - | -------- | ---------- |
| ~~OQ-3 (MVP)~~ | Department-specific tasks within AI Engineering for MVP? | **No** — department is metadata only for MVP (SD-7, PRD A3) |
| ~~OQ-5~~ | LLM provider/model? | **OpenAI `gpt-4o`** (SD-1) |
| ~~OQ-6~~ | Output path convention? | **`./output/`** default (SD-3, FR-016) |
| ~~OQ-7~~ | Task IDs inline vs appendix? | **Audit appendix only** (SD-4) |
| ~~OQ-8~~ | Catalog format? | **YAML, one file per task set** (SD-2) |
| ~~OQ-9~~ | Developer vs Engineer distinction? | **Distinct roles**, separate task-set files (SD-5) |
| ~~OQ-10~~ | `source_reference` format? | **URL string** (SD-8) |
| ~~OQ-11~~ | CLI executable name? | **`onboard`** (SD-6) |
| ~~OQ-12~~ | Catalog validation-only CLI mode in MVP? | **Deferred to P2** (PRD Future Features: catalog lint CLI) |

### Remaining — stakeholder input still required

These match PRD Open Questions 1–9. They do not block SAD structure. They MUST be resolved before production-valid plans. Development agents SHALL NOT resolve them by invention.

| # | Question | Architectural impact | PRD ref |
| - | -------- | -------------------- | ------- |
| OQ-1 | What are the actual tasks in each placeholder task set? | **Partial (2026-08-27):** Developer 15-task set supplied (SD-9). Still open: UI Designer, UX Researcher, Product Manager, Engineer, and `shared_tasks`. Production-valid plans for non-Developer roles remain blocked | PRD Open Question 1 |
| OQ-2 | Who owns approval and maintenance of each task set? | Governance and change-control process | PRD Open Question 2 |
| OQ-3 (post-MVP) | After MVP, should any tasks become department-specific within AI Engineering? | Future filtering rules; no MVP code change | PRD Open Question 3 |
| OQ-4 | What defines “ramp complete” for each of the five roles? | Pilot success measurement | PRD Open Question 4 |
| OQ-5 | How will the assumed three-week baseline be replaced with measured data? | KPI validity | PRD Open Question 5 |
| OQ-6 | Which specific policies or documents should `source_reference` URLs point to? | Catalog provenance corpus; field format is already URL | PRD Open Question 6 |
| OQ-7 | How many hires per year occur in each of the five roles? | ROI only; not CLI acceptance | PRD Open Question 7 |
| OQ-8 | What employee data may be retained in run diagnostics, and for how long? | Logging architecture and data minimization | PRD Open Question 8; SA-10 |
| OQ-9 | Which geographic/compliance jurisdictions apply to catalog content? | Security/compliance scope of catalogued tasks | PRD Open Question 9 |
| OQ-13 | Has the four-agent CrewAI crew been verified with a live LLM run? | **Open (2026-08-27):** The four-agent crew (Role Analyst, Plan Builder, Compliance Checker, Document Writer) is fully wired and the environment supports real CrewAI execution (Python 3.12 venv, CrewAI 1.15.17 installed, `crew.kickoff()` runs). No live LLM run has been completed yet — no `OPENAI_API_KEY` is configured, by choice, to avoid API costs during this phase of Build. All current tests (32 passing) use stubbed Role Analyst and Plan Builder outputs, not real LLM responses. The deterministic compliance logic (`check_compliance`) and retry loop are proven against stub outputs, not yet against real, unpredictable LLM output. Risk: stub tests confirm the code correctly rejects invented task IDs when given known/controlled input, but do not yet confirm this holds against a real LLM's actual behavior. Resolution: a live run will be completed once an API key is available (pending: shared course key, free-tier alternative, or a funded personal key), before this component is considered fully verified. | N/A — Build-phase live-run gate |

---

# Audit

| Field | Value |
| ----- | ----- |
| **Timestamp** | 2026-08-27 |
| **Persona ID** | `system-arch` |
| **Action** | `create-sad` (Developer catalog ingest; SD-9 / SA-16) |
| **Artifact** | `project-context/1.define/sad.md` |
| **Resolved `AAMAD_TARGET_RUNTIME`** | `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`) |
| **LLM** | OpenAI `gpt-4o` via `OPENAI_API_KEY` (SD-1); temperature/token caps deferred to setup.md Audit |
| **Process model** | Sequential CrewAI crew with application-level retry state machine |
| **Agent count** | 4 (Role Analyst, Plan Builder, Compliance Checker, Document Writer) |
| **Primary interface** | CLI `onboard` (SD-6); default output `./output/` (SD-3, FR-016); SD-10 UI at `src/onboarding-ui/` |
| **Language** | Python (`aamad.config.yml`) |
| **Functional requirements covered** | FR-001–FR-016 |
| **Task catalog** | YAML one-file-per-set; Developer content supplied (15 tasks); other roles placeholder |
| **Department** | Metadata only; no applicability filtering (SD-7) |
| **Task IDs in Markdown** | Audit appendix only (SD-4) |
| **User stories** | None present |
| **MRD referenced** | Yes (required; not skipped) |
| **PRD version aligned** | 2026-08-20 `create-prd` (prior 2026-08-09 PRD comparison only) |
| **Prompt Trace** | Not captured inline; SAD is architecture specification, not runtime execution |

---

## Audit (sync-docs 2026-08-28)

| Field | Value |
| ----- | ----- |
| **Timestamp** | 2026-08-28 |
| **Persona ID** | `project-mgr` (operator requested documentation sync after `src/` restructure) |
| **Action** | `sync-docs` |
| **What changed** | §4.1 implemented `src/` layout; §4.2 thin FastAPI wrap; §3 / Interface / SA-9 / Future Work aligned to SD-10; `src/onboarding-ui/` vs `src/frontend/` distinguished |
| **Resolved `AAMAD_TARGET_RUNTIME`** | `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`) |
