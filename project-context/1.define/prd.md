# Product Requirements Document — Automated Employee Onboarding Workflow

**Persona:** `product-mgr`
**Action:** `create-prd`
**Phase:** Define
**Intended path:** `project-context/1.define/prd.md`
**Product:** Automated Employee Onboarding Workflow
**Target organization:** AI Engineering (internal)
**Supported roles:** UI Designer, UX Researcher, Product Manager, Developer, Engineer
**MVP interface:** Command-line interface (`onboard`)
**Status:** Template-aligned PRD; development handoff candidate, subject to task-catalog population

## Context & Instructions

This PRD defines MVP product requirements for a multi-agent onboarding-plan generator. Product scope is plan generation and validation from an authoritative task catalog—not live HR execution, provisioning, or progress tracking.

## Input Requirements

**Deep Research Report / MRD:** `project-context/1.define/mrd.md` (completed; not skipped)
**System Description:** N/A — `project-context/1.define/system-description.md` is not present
**System Concept:** Crew-orchestrated, catalog-authoritative generation of role-aware 30/60/90-day onboarding plans and manager checklists for five AI Engineering roles
**Selected Runtime:** `crewai` (resolved from `aamad.config.yml` `runtime.target`; `AAMAD_TARGET_RUNTIME` unset)
**Prior PRD (preserved for comparison):** `project-context/1.define/prd-2026-08-09.md` — this template-aligned document keeps that MVP scope and incorporates 2026-08-19 stakeholder decisions recorded in `project-context/1.define/sad.md`

---

# 1. Executive Summary

## Problem Statement

The AI Engineering organization lacks a repeatable way to generate consistent employee onboarding plans for five roles: UI Designer, UX Researcher, Product Manager, Developer, and Engineer.

External research in the MRD supports the general problem: Gallup reports that only **12%** of employees strongly agree their organization does a great job of onboarding; BambooHR found **70%** of new hires decide fit within the first month and **44%** report regrets within the first week. SHRM notes fragmented ownership and recommends role-tailored onboarding rather than one generic checklist. These figures validate the problem class; they are **not** measured outcomes for this organization (MRD A11).

Internal impact is operational, not market-revenue: required compliance or provisioning tasks can be omitted, role-specific work can be sequenced incorrectly, and an AI system can invent onboarding requirements that do not exist in an approved source. That last risk is the primary product risk.

Target population is internal: hiring managers / onboarding coordinators as operators, and new hires in the five named roles as plan consumers. Industry TAM/SAM/SOM is N/A.

## Solution Overview

The product is a multi-agent application that accepts three CLI inputs—`role`, `department`, and `start_date`—and generates two Markdown artifacts:

1. a role-aware 30/60/90-day onboarding plan; and
2. a manager checklist supporting execution of that plan.

Four specialized agents operate with a validation gate:

**Role Analyst → Plan Builder → Compliance Checker → Document Writer**

The Compliance Checker is independent of the Plan Builder. A rejected plan returns to the Builder. A maximum of **two Builder retries** is allowed after the initial candidate. After two unsuccessful rebuilds, the workflow terminates without approved outputs.

Unique value versus generic LLM drafting or a single checklist template:

* the **task catalog**, not the language model, is the authoritative source of tasks;
* every generated item must reference a stable `task_id`;
* construction and validation are separated;
* outputs remain auditable (catalog version/hash, workflow ID, validation findings).

Expected operational outcomes: consistent role-aware plans, 100% mandatory compliance/provisioning coverage in approved plans, zero invented tasks, and a later pilot target of **30% ramp-time reduction** against an assumed three-week baseline (Assumption A1).

## Strategic Rationale

A multi-agent design is justified because the workflow has separable responsibilities with different validation boundaries: applicability, sequencing, independent compliance checking, and document rendering. The Builder must not also be the sole authority that declares a plan valid.

Business case is internal operational value (consistency, auditability, reduced manager reconstruction of checklists), not external subscription revenue. Competitive positioning versus Workday, Rippling, BambooHR, and similar platforms is N/A for MVP: this product does not replace an HRIS; it generates catalog-grounded plans locally.

Market timing figures are N/A for an internal tool. ROI formulas exist in the MRD but remain unpopulated until hiring volume and baselines are measured.

Phase 2 implementation SHALL follow the CrewAI adapter (`AAMAD_TARGET_RUNTIME` / config target `crewai`). The product is the onboarding workflow and catalog contract, not a CrewAI-specific capability lock-in.

---

# 2. Market Context & User Analysis

## Target Market / Users

**Primary user — Hiring manager / onboarding coordinator**

Operates the CLI. Needs to supply minimal employee context (`role`, `department`, `start_date`) and receive a consistent plan without manually deciding which shared and role-specific requirements apply.

**Secondary user — New hire**

Principal consumer of the 30/60/90 plan. Does not interact with the CLI in MVP.

**Supported role segments (canonical identifiers only):**

`UI Designer | UX Researcher | Product Manager | Developer | Engineer`

Role matching SHALL use these canonical identifiers. No alias support is required for MVP. Developer and Engineer are distinct supported roles with separate role-specific task sets (stakeholder decision SD-5).

**Market segment size and growth:** N/A as industry TAM. Addressable volume is 100% of onboarding events across the five roles. No organization-specific hiring counts were supplied (MRD A1, A10).

**Geographic focus:** N/A / unspecified. Jurisdictional compliance requirements are an Open Question; MVP does not infer legal requirements.

## User Needs Analysis

**Critical pain points (MRD + product scope):**

* Onboarding quality is broadly weak in published research; internal quality is unmeasured.
* Ownership is fragmented across HR, managers, IT, and peers (SHRM).
* Role-specific context is required; a generic checklist is insufficient.
* Manual reconstruction of plans risks omitted compliance/provisioning work.
* Unconstrained generative AI can invent tasks that are not approved.

**User journey (MVP):**

1. Operator validates a new hire’s role, department, and start date.
2. Operator runs `onboard` with those three inputs.
3. System validates input and catalog structure before any agent run.
4. Agents select, sequence, and validate catalog tasks.
5. On PASS, operator receives `onboarding-plan.md` and `manager-checklist.md` under `./output/` (or override).
6. Manager uses the checklist; new hire uses the plan. Execution, reminders, and tracking are out of scope.

**Adoption barriers:** missing or placeholder catalog content; distrust if plans contain invented tasks; CLI-only surface; no live HRIS so data is typed by the operator.

**Success factors:** catalog authority, fail-closed validation, explainable REJECT findings, stable CLI contract, traceability appendix.

## Competitive Landscape

Direct commercial competitors are **not** the MVP alternative. The relevant alternatives are:

| Alternative | Strength | Gap relative to this product |
| ----------- | -------- | ---------------------------- |
| Manual manager checklist | Full human control | Inconsistent coverage; high reconstruction cost |
| Generic LLM prompt | Fast drafting | Invents tasks; no catalog traceability |
| HRIS onboarding modules (Workday, BambooHR, Rippling, Deel) | Proven task/provisioning automation | Live integration and platform lock-in; out of MVP scope |
| Identity lifecycle tools (Entra, Okta) | Provisioning automation | Identity only; not role-learning plans |
| Zapier-style automation | Broad connectors | Governance and role-aware validation still must be designed |

MVP differentiation is **catalog-grounded, validation-gated plan generation** for five AI Engineering roles. Pricing benchmarks are N/A (internal tool).

---

# 3. Technical Requirements & Architecture

## Runtime & Agent Specifications

**Resolved runtime:** `crewai`
**Process model:** sequential forward path; retry loop owned by application orchestrator
**Language:** Python (`aamad.config.yml` `language.primary`)
**Delegation:** `allow_delegation=false` unless a future SAD revision justifies a manager pattern
**Memory:** `memory=false` for MVP reproducibility
**LLM (stakeholder decision SD-1):** OpenAI `gpt-4o`; secret via `OPENAI_API_KEY` only

Collaboration pattern:

```text
CLI Input
   |
   v
Role Analyst
   |
   v
Plan Builder
   |
   v
Compliance Checker
   |
   +---- PASS ----> Document Writer ----> Markdown Outputs
   |
   +---- REJECT --> Plan Builder (max 2 retries after initial candidate)
```

At most three candidate plans may be evaluated. The workflow SHALL NOT bypass the Compliance Checker. Document Writer SHALL execute only after `ComplianceResult.status == PASS`.

Structured outputs SHALL use Pydantic models or equivalent JSON schemas at every agent boundary. Malformed output is a failed stage, not something to silently parse.

### Core Agent Definitions

**agent:** `role_analyst`

* role: "Role Analyst"
* goal: "Select exactly the authoritative task IDs that apply to the requested role"
* backstory: "Applicability specialist who never invents or sequences tasks"
* tools: read-only task-catalog access; no write, network, or shell tools
* memory: false
* delegation: false
* runtime notes: CrewAI `max_iter <= 12`; output schema `RoleAnalysis`; department is metadata only in MVP (SD-7) and SHALL NOT filter task selection

The Role Analyst SHALL:

1. select active shared tasks applicable to the role;
2. select active compliance/legal tasks applicable to the role;
3. select active IT provisioning tasks applicable to the role;
4. select the matching role-specific task set;
5. select applicable team-integration tasks;
6. return task identifiers only, with task-set origin for each ID.

The Role Analyst SHALL NOT create tasks, alter descriptions, sequence, assign buckets, omit mandatory applicable tasks, or perform compliance approval.

**agent:** `plan_builder`

* role: "Plan Builder"
* goal: "Turn the applicability set into an ordered 30/60/90 candidate plan using catalog IDs only"
* backstory: "Onboarding planner constrained by priority and bucket rules"
* tools: read-only task-catalog access
* memory: false
* delegation: false
* runtime notes: CrewAI `max_iter <= 12`; output schema `CandidatePlan`; on retry, modify only invalid aspects identified by the Checker

Priority (highest to lowest):

```text
1. COMPLIANCE_LEGAL
2. IT_PROVISIONING
3. ROLE_ENABLEMENT
4. TEAM_INTEGRATION
```

Every selected task SHALL be assigned to exactly one of `30_DAY`, `60_DAY`, `90_DAY`, respecting `allowed_buckets`. Exact calendar deadlines SHALL NOT be inferred.

**agent:** `compliance_checker`

* role: "Compliance Checker"
* goal: "Independently validate a candidate plan and return PASS or REJECT with machine-readable findings"
* backstory: "Independent auditor who never edits plans"
* tools: read-only catalog access plus deterministic validation helpers in application code
* memory: false
* delegation: false
* runtime notes: CrewAI `max_iter <= 12`; output schema `ComplianceResult`; PASS eligibility is an application invariant, not an LLM self-assessment

Required checks: mandatory compliance coverage; mandatory provisioning coverage; traceability; applicability; uniqueness; bucket validity; priority integrity; role integrity.

**agent:** `document_writer`

* role: "Document Writer"
* goal: "Render an already-approved plan into Markdown using catalog-resolved titles and descriptions"
* backstory: "Technical writer; presentation only"
* tools: read-only catalog access; filesystem write to the configured output directory only
* memory: false
* delegation: false
* runtime notes: CrewAI `max_iter <= 12`; precondition `PASS`; task IDs appear in an audit appendix only (SD-4)

## Authoritative Task-Set Model

The onboarding task catalog is **not fully approved**. **Developer** content is stakeholder-supplied (SAD SD-9). Other role sets remain placeholders. Development agents MUST NOT populate placeholders with model-generated onboarding tasks.

Required placeholder task sets (YAML, one file per set — SD-2):

* `shared_tasks`
* `compliance_legal_tasks`
* `it_provisioning_tasks`
* `ui_designer_tasks`
* `ux_researcher_tasks`
* `product_manager_tasks`
* `developer_tasks`
* `engineer_tasks`
* `team_integration_tasks`

Conceptual `TaskDefinition` schema:

```text
TaskDefinition
- task_id: string, required, globally unique, immutable
- title: string, required
- description: string, required
- task_set: enum, required
- category: enum, required
- applicable_roles: list[SupportedRole], required
- applicable_departments: list[string] | ["*"], required
- mandatory: boolean, required
- allowed_buckets: list[30 | 60 | 90], required
- source_reference: string (URL), required
- active: boolean, required
- version: string, required
```

Allowed `category` values: `COMPLIANCE_LEGAL`, `IT_PROVISIONING`, `ROLE_ENABLEMENT`, `TEAM_INTEGRATION`.

`source_reference` SHALL be a URL string (SD-8). A catalog missing unique `task_id`, applicability, category, source reference, or bucket eligibility SHALL fail startup validation.

**Zero-invention enforcement:** agents SHALL select and manipulate `task_id` references only. Titles and descriptions SHALL be resolved from the catalog at render time. An intermediate output containing an unknown `task_id` SHALL be rejected.

## Integration Requirements

**MVP:** no live external integration. Input from CLI arguments. Task definitions from version-controlled local configuration. Outputs as local Markdown files. No application database.

Employee-data acquisition SHALL be isolated behind:

```text
EmployeeContextProvider
    get_employee_context(input_reference) -> EmployeeContext
```

MVP adapter: `CliEmployeeContextProvider`. Future HRIS and identity-provider adapters SHALL implement the same contract and SHALL NOT require changes to agent business logic.

Future HRIS fields may include employee identity, manager, employment type, location, and legal entity; only `role`, `department`, and `start_date` are required for the current workflow. No HRIS or IdP vendor is selected.

**Authentication (MVP):** none. The CLI is assumed to be operated by an authorized person on a trusted workstation (Assumption A5). LLM provider secrets SHALL NOT be embedded in catalogs, code, or generated Markdown.

**Performance:** no throughput SLA. One workflow per CLI invocation. Correctness over completeness.

## Infrastructure Specifications

* **Hosting (MVP):** local / developer workstation or a single-process runtime. Cloud hosting is Future Work for Deliver.
* **Compute / memory:** sufficient for one Python CrewAI process and OpenAI API calls; no cluster requirement.
* **Network:** outbound LLM provider access only; no HRIS/IdP network dependency.
* **Monitoring / logging:** each run SHOULD record `workflow_id`, inputs, catalog version/hash, selected task IDs, candidate plans, validation findings, retry count, final status, and output paths. Secrets redacted. Persist diagnostics under a project-scoped logs path during Build.

Conceptual layers:

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

Agents SHALL NOT parse CLI arguments directly or write arbitrary files outside defined responsibility.

## Shared Context and Handoffs

All stages SHALL have access to:

```text
WorkflowContext
- workflow_id
- role
- department
- start_date
- task_catalog_version
- task_catalog_hash
- supported_roles
- priority_rules
- retry_count
- max_builder_retries = 2
```

**Handoff A — CLI to Role Analyst:** `OnboardingRequest` (`workflow_id`, `role`, `department`, `start_date`, `task_catalog_version`). Preconditions: valid role, department, start date, catalog loaded.

**Handoff B — Role Analyst to Plan Builder:** `RoleAnalysis` with `applicable_tasks` as `{task_id, source_task_set, category, mandatory}` only. Every `task_id` MUST exist in the catalog.

**Handoff C — Plan Builder to Checker:** `CandidatePlan` with `build_attempt` (1=initial, 2=first retry, 3=final retry) and per-bucket `{task_id, sequence}`. No free-form task definitions.

**Handoff D — Checker:** `ComplianceResult` with `status: PASS | REJECT`, boolean checks, and findings (`rule_id`, `severity: ERROR`, `task_ids`, `message`). PASS requires every boolean check `true` and no error-level findings.

**Handoff E — Rejection to Builder:** `PlanRevisionRequest` with previous candidate, compliance result, and next build attempt. Role Analyst SHALL NOT rerun solely because sequencing failed.

**Handoff F — Approved plan to Writer:** `ApprovedPlan` only when status is PASS.

## Retry and Failure State Machine

```text
BUILD attempt 1 → CHECK
    PASS → WRITE → SUCCESS
    REJECT → BUILD attempt 2 → CHECK
        PASS → WRITE → SUCCESS
        REJECT → BUILD attempt 3 → CHECK
            PASS → WRITE → SUCCESS
            REJECT → TERMINAL FAILURE
```

Retry counter SHALL NOT reset during one workflow. No fourth build attempt. On terminal failure: do not invoke Document Writer; do not emit approved plan or checklist; emit structured diagnostics; return non-success CLI status.

---

# 4. Functional Requirements

## Core Features (Priority P0)

**FR-001 — Accept supported input**

As a hiring manager, I want to pass role, department, and start date to `onboard` so that a plan can be generated without a web UI.

Acceptance: CLI accepts the three required arguments; executable name is `onboard` (SD-6).

**FR-002 — Validate input before agent execution**

As an operator, I want invalid inputs to fail immediately so that the crew is never invoked on bad data.

Acceptance: unsupported role, blank department, missing/malformed/impossible start date fail with a non-zero exit, a clear error, and no generated files. Supported roles are listed on role errors. Start date MUST be `YYYY-MM-DD`. The application SHALL NOT infer a missing date from system time. Department MUST be non-whitespace after trim; no department enumeration is required.

**FR-003 — Resolve applicable tasks**

As a manager, I want the system to select the correct catalog tasks for the hire’s role so that I do not assemble the plan by hand.

Acceptance: Role Analyst returns only catalog `task_id`s applicable to the role; department is recorded but does not filter selection in MVP (SD-7).

**FR-004 — Support five roles**

As the organization, I want exactly the five named roles supported so that scope stays bounded.

Acceptance: canonical role set only; Developer and Engineer have separate task sets (SD-5).

**FR-005 — Apply priority ordering**

As a compliance-conscious operator, I want legal/compliance work before provisioning, role enablement, and team integration so that critical tasks are not buried.

Acceptance: Plan Builder sequences by `COMPLIANCE_LEGAL > IT_PROVISIONING > ROLE_ENABLEMENT > TEAM_INTEGRATION` within a planning window unless a task definition forbids that order.

**FR-006 — Generate 30/60/90 structure**

As a new hire, I want tasks grouped into 30-, 60-, and 90-day buckets so that I know the planning window.

Acceptance: every applicable task is in exactly one allowed bucket; no invented calendar due dates.

**FR-007 — Validate mandatory coverage**

As the organization, I want every applicable mandatory compliance and IT provisioning task present in approved plans.

Acceptance: Checker verifies 100% presence of those mandatory IDs; omission yields REJECT.

**FR-008 — Enforce task traceability**

As an auditor, I want every plan item to map to a catalog `task_id` so that no invented work reaches a hire.

Acceptance: unknown IDs cause REJECT; Writer resolves titles/descriptions from the catalog only.

**FR-009 — Implement validation loop**

As an operator, I want invalid plans corrected up to two Builder retries so that recoverable sequencing errors do not immediately fail the run.

Acceptance: max two returns to Plan Builder after the initial candidate; retry count is application state.

**FR-010 — Fail closed**

As the organization, I want no approved documents if validation never passes.

Acceptance: after three rejected evaluations, no `onboarding-plan.md` or `manager-checklist.md` is written as approved output.

**FR-011 — Generate onboarding Markdown**

As a new hire, I want a 30/60/90 Markdown plan with role, department, start date, catalog version, resolved titles/descriptions, category, and provenance.

Acceptance: plan body does not show raw `task_id`s; IDs appear in an audit appendix (SD-4).

**FR-012 — Generate manager checklist**

As a hiring manager, I want a Markdown checklist of the same approved tasks, grouped by 30/60/90, with checkboxes, employee context, and provenance, and with no extra tasks.

Acceptance: checklist task IDs match the approved plan; IDs in appendix only.

**FR-013 — Preserve traceability**

As an auditor, I want workflow and catalog identity recorded so that a plan can be reproduced against the same catalog snapshot.

Acceptance: documents include catalog version; hash SHOULD be recorded; workflow_id identifies the run.

**FR-014 — Adapter boundary**

As a future integrator, I want employee context behind an interface so that HRIS/IdP can be added without rewriting agents.

Acceptance: CLI is one `EmployeeContextProvider`; agent logic has no vendor-specific HRIS/IdP calls.

**FR-015 — Load authoritative catalog**

As a developer, I want YAML task-set files validated at startup so that placeholder or invalid catalogs cannot silently produce production-valid plans.

Acceptance: required task-set files exist structurally; unresolved placeholders are development-only and SHALL NOT be treated as production-valid.

**FR-016 — Configurable output location**

As an operator, I want files written to `./output/` by default, overridable via `--output-dir` or `ONBOARDING_OUTPUT_DIR` (SD-3).

Acceptance: successful runs write both Markdown files to the resolved directory.

## Enhanced Features (Priority P1)

Deferred unless needed to meet P0 acceptance. Should-have items that MAY be implemented if they do not expand MVP scope:

* structured run diagnostics on failure (labeled as diagnostics, not approved plans)
* human-readable compliance findings in CLI errors
* deterministic filenames
* duplicate-task detection (also implied by Checker uniqueness)
* unit-test fixtures for all five roles (`aamad.config.yml` requires unit tests)
* integration tests mapped to acceptance criteria (`aamad.config.yml`)
* deterministic application-level schema validation around runtime outputs

## Future Features (Priority P2)

Explicit Future Work — not MVP:

* live HRIS integration
* live identity-provider integration
* account provisioning or permission assignment
* executing onboarding tasks
* completion tracking, notifications, reminders
* exact deadline inference beyond 30/60/90 buckets
* additional roles or role aliases
* dynamic/catalog task invention by agents
* legal/compliance inference beyond the catalog
* performance evaluation or employment decisions
* rich chat UI, extra screens, pause/cancel (`aamad.config.yml` UI theme/visual_style still unused). **SD-10 (2026-08-27)** added a minimal form + results UI wrapping the CLI/API core; that wrap is in scope. Rich chat remains Future Work.
* JSON result alongside Markdown
* dry-run mode, catalog lint CLI, plan-diff across catalog versions
* alternative Markdown templates / `--verbose`
* enterprise AuthN/AuthZ, SSO, IAM
* onboarding analytics dashboard

Any development agent proposing a P2 item SHALL classify it as Future Work rather than adding it to MVP.

---

# 5. Non-Functional Requirements

## Performance Requirements

* **Correctness over completeness:** fail rather than emit a plan that violates mandatory coverage or traceability.
* **Response time:** no hard SLA; monitor during pilot. Happy-path duration depends on LLM latency.
* **Throughput:** one concurrent workflow per CLI invocation.
* **Availability:** N/A as a hosted SLA; the tool is available when the operator can run the CLI and reach the LLM provider.

The following SHALL be deterministic even when LLM reasoning is used inside constraints: input validation; role enumeration; task-ID existence; retry counting; max retries; output-schema validation; PASS eligibility; terminal failure; document-write eligibility.

## Security & Compliance

* No HRIS/IdP credentials in MVP.
* `OPENAI_API_KEY` (or equivalent provider key) from environment only; never committed (`security.forbid_committed_secrets: true`).
* Least-privilege tools per agent (catalog read; Writer write only to output dir).
* Data minimization: persist workflow inputs and catalog references needed for audit, not extra employee PII.
* `security.require_security_assessment: true` — `@security.eng` SHALL produce `project-context/2.build/security.md` before Deliver.
* `security.dependency_audit: true` — dependency audit in Build/Deliver.
* MVP SHALL NOT infer legal requirements; only catalogued `COMPLIANCE_LEGAL` tasks apply.
* Prompt Trace / diagnostics SHALL redact secrets.

## Scalability & Reliability

* Scaling triggers: N/A for MVP; MRD A6 treats volume as moderate and correctness-first.
* Fault tolerance: invalid input fails before crew; malformed agent output fails the stage; LLM/API failure is a non-success CLI result; SIGINT/cancel SHALL not leave approved partial outputs.
* Recovery: operator re-runs the CLI; no workflow resume/memory in MVP.
* Type checking is required (`coding_standards.type_checking: true`). Prefer files at or below `max_file_lines: 400` unless a module cannot be split without harming clarity.

---

# 6. User Experience Design

## Interface Requirements

MVP interface is the command line. No web or mobile client.

Conceptual invocation:

```text
onboard --role "Developer" --department "AI Engineering" --start-date "YYYY-MM-DD" [--output-dir PATH]
```

Accessibility/usability for GUI does not apply. CLI usability requirements: clear success/failure copy; list supported roles on role errors; non-zero exit on failure; do not claim success when validation failed.

`aamad.config.yml` UI keys (`theme`, `visual_style`, `prefer_modals`) are **not applicable** to this CLI MVP and SHALL NOT be used to justify adding a graphical UI.

## Agent Interaction Design

Human–agent communication is batch, not conversational:

* Operator supplies three validated fields.
* Agents do not ask clarifying questions in MVP.
* Success copy includes role, department, start date, Validation PASS, retries used (0–2), and output paths.
* Input failure: error before agents; example unsupported role message lists the five canonical roles.
* Validation failure after retries: show attempt counts, final REJECT, structured human-readable findings; no approved files.
* Transparency: audit appendix with task IDs, catalog version/hash; CLI reports retry count; optional diagnostic artifact on failure MUST be labeled as a failed-run diagnostic.

---

# 7. Success Metrics & KPIs

## Business / Operational Metrics

| Metric | Target | Notes |
| ------ | ------ | ----- |
| Ramp-time reduction | **30%** vs assumed 3-week baseline | A1; ~2.1 weeks arithmetic only; not measured |
| Mandatory compliance + provisioning coverage | **100%** in every approved plan | Automated |
| Invented tasks | **Zero** | Automated |

Ramp-time cannot be proven by unit tests. Validation requires a pilot with a per-role “ramp complete” definition, measured baseline, and agreed aggregation (median or specified method). Until A1 is replaced, the 30% target is a hypothesis.

## Technical Metrics

* Invalid inputs never invoke the crew (100% of invalid-input tests).
* Checker cannot be bypassed; Writer never runs without PASS.
* No fourth Builder attempt.
* Failed runs generate neither approved document.
* Inter-agent handoffs conform to schemas.
* Agent effectiveness: `mandatory_coverage == 1.0`; `invalid_task_count == 0`.
* Cost: no dollar ceiling supplied; log token/cost telemetry when available. Do not invent a budget.

## User Experience Metrics

* Task completion for the operator: successful generation of both files for each of the five roles using approved fixtures.
* Time-to-value: one CLI invocation after catalog load; no multi-step wizard.
* Satisfaction: not instrumented in MVP; collect qualitatively in the pilot.
* New-hire CSAT / clarity scores from the MRD remain Future Work.

## Validation Test Matrix (minimum)

**Happy paths:** one successful generation per supported role.

**Invalid inputs:** missing role; unsupported role; blank department; missing start date; malformed start date; impossible calendar date.

**Compliance failures:** missing mandatory compliance task; missing mandatory provisioning task; invented task ID; wrong-role task; duplicate task; invalid bucket; priority violation.

**Retry:** pass on attempt 1; fail then pass on retry 1; fail twice then pass on attempt 3; all three fail (terminal); verify no fourth build.

**Outputs:** success writes exactly two approved Markdown files with 30/60/90 sections and matching checklist IDs; failure writes no approved plan/checklist, shows reason, non-zero exit.

---

# 8. Implementation Strategy

## Development Phases

**Phase 1 — Define**

* MRD complete
* This PRD complete (template-aligned)
* SAD exists; remaining before production-valid plans: populate and approve the task catalog; name task-set owners; confirm role-task applicability in catalog content

**Phase 2 — Build** (recommended order)

1. Task schemas and catalog validation
2. CLI / input validation
3. Structured handoff models
4. Role Analyst
5. Plan Builder
6. Compliance Checker
7. Deterministic retry controller
8. Document Writer
9. Markdown templates (IDs in appendix)
10. Unit and integration tests mapped to acceptance criteria
11. Adapter interfaces for future HRIS/IdP
12. Security assessment (`security.md`) before Deliver

Follow the modular AAMAD build sequence: core configuration → API/runtime → frontend/CLI UX → validation. CLI `onboard` remains the underlying interface. SD-10 adds a single-screen UI at `src/onboarding-ui/` that calls the same core; a chat UI epic remains out of scope.

**Phase 3 — Deliver**

Deploy configs, runbook, and user guide (`documentation.require_user_guide: true`) are owned by `@devops.eng` after QA (and security assessment).

## Resource Requirements

Exact staffing, calendar, and budget are TBD (MRD A9). MVP needs: product owner for catalog approval, backend/runtime engineer, test coverage, and security review. SD-10 adds a small frontend wrap (`src/onboarding-ui/`); it does not replace the CLI.

## Risk Mitigation

| Risk | Mitigation |
| ---- | ---------- |
| Invented onboarding tasks | Catalog authority; ID-only handoffs; Checker; fail closed |
| Placeholder catalog treated as production | Explicit development-only rule; startup validation |
| Builder self-certifies | Separate Checker; deterministic PASS |
| Runtime retry defaults change product behavior | `max_builder_retries = 2` in application code |
| Secret leakage | Env-only keys; redacted logs |
| Scope creep into live HRIS | Adapter boundary; P2 list |
| Multi-agent complexity without value | Keep four bounded agents; benchmark later vs deterministic builder if needed |
| SAD/PRD drift | This PRD absorbs SD-1–SD-8; architecture remains in SAD |

## Development Guardrails (invariants)

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

Conflicts with these invariants SHALL be escalated, not silently changed.

## PRD Acceptance Criteria (MVP implemented when)

* all five roles generate plans from defined task fixtures;
* invalid inputs fail before agent execution;
* every inter-agent handoff conforms to a structured schema;
* priority rules are enforced;
* mandatory compliance coverage is 100%;
* mandatory provisioning coverage is 100%;
* no unknown task ID can reach approved output;
* the Checker cannot be bypassed;
* no more than two Builder retries occur;
* retry exhaustion produces terminal failure;
* the Writer executes only after PASS;
* successful runs generate both Markdown documents;
* failed runs generate neither approved document;
* future HRIS/IdP interfaces remain decoupled from agent logic;
* automated tests prove traceability and mandatory coverage;
* task IDs are not shown inline in plan/checklist body.

---

# 9. Launch & Go-to-Market Strategy

N/A — internal operational tool for AI Engineering. No external launch, pricing, or sales motion.

Internal “launch” is: catalog approved → QA pass → security assessment → operator-authorized deploy/runbook and user guide. Promotion remains a Deliver-phase operational decision.

---

# Quality Assurance Checklist

- [x] Requirements traceable to MRD, prior PRD MVP scope, SAD stakeholder decisions SD-1–SD-8, or recorded Assumptions
- [x] Technical specifications feasible with the selected runtime adapter (`crewai`)
- [x] Success metrics aligned with stated objectives (coverage, zero invention, hypothesized ramp reduction)
- [x] MVP vs Future Work boundaries explicit
- [x] Market TAM/GTM marked N/A because this is an internal tool (MRD was not skipped)

---

# Sources

1. `project-context/1.define/mrd.md` — market problem evidence, internal-tool framing, competitive alternatives, recommended bounded orchestration (MVP narrowed below MRD’s full journey).
2. Prior `project-context/1.define/prd.md` (2026-08-09 `create-prd`) — MVP scope: CLI plan generation, four-agent validation gate, zero-invention catalog, retry rule, functional requirements.
3. `project-context/1.define/sad.md` Stakeholder Decisions (2026-08-19) SD-1 through SD-8 — LLM, YAML catalog, output path, task-ID visibility, Developer vs Engineer, CLI name, department metadata-only, `source_reference` URL.
4. `aamad.config.yml` — `runtime.target: crewai`, Python, type checking, security assessment, user guide, unit and integration tests.
5. `.cursor/templates/prd-template.md` — required PRD structure.
6. CrewAI adapter rule `.cursor/rules/adapter-crewai.mdc` — YAML agents/tasks, sequential process, `max_iter`, memory default, structured outputs (implementation convention, not a market source).
7. MRD-cited external research: Gallup onboarding studies; SHRM onboarding roles/measurement; BambooHR 2023–2024 onboarding/HR research; vendor capability pages for Workday, ServiceNow, Rippling, Deel, Microsoft Entra, Okta, Zapier (see MRD Sources for URLs).

No competitor revenue or market-size figures are used as product requirements.

---

# Assumptions

**A1 — Ramp baseline.** Manual onboarding ramp time is assumed to be **three weeks**. This is not measured organizational data. The 30% reduction target is stakeholder-defined, not an external benchmark.

**A2 — Task catalogs.** Production acceptance still requires approved catalogs for all five roles. **Developer** content is supplied (SAD SD-9). Other task sets remain placeholders. Development agents MUST NOT invent catalog tasks.

**A3 — Department behavior.** Department is a required input and is recorded on outputs. For MVP it does not filter task applicability (SD-7). Future department-specific tasks remain unspecified.

**A4 — Local output.** Markdown files may be written to a local/configured filesystem because no document-management integration was requested. Default path `./output/` (SD-3).

**A5 — CLI operator.** The CLI is operated by an authorized manager, onboarding coordinator, developer, or evaluator. Authentication is not in MVP because there are no live enterprise integrations.

**A6 — First-party task authority.** Once stakeholder-approved, the task catalog is the only acceptable source of onboarding requirements. Model world knowledge is not an acceptable source.

**A7 — MRD skip.** MRD was **not** skipped. Broader MRD journey items (live orchestration, reminders, progress tracking) are Future Work, not silent MVP expansion.

**A8 — Runtime resolution.** `AAMAD_TARGET_RUNTIME` was unset; `aamad.config.yml` `runtime.target: crewai` is the resolved adapter. Product definition remains the workflow/catalog contract.

**A9 — UI config.** Visual UI settings in `aamad.config.yml` are unused. SD-10 is a minimal form + results wrap, not a themed chat product.

**A10 — No additional quantitative market, cost, performance, throughput, or staffing figures** are assumed beyond A1.

---

# Open Questions

These do not block PRD structure. They MUST be resolved before production-valid plans. Development agents SHALL NOT resolve them by invention.

1. What are the actual tasks in each placeholder task set?
2. Who owns approval and maintenance of each task set?
3. After MVP, should any tasks become department-specific within AI Engineering?
4. What defines “ramp complete” for each of the five roles?
5. How will the assumed three-week baseline be replaced with measured data?
6. Which specific policies or documents should `source_reference` URLs point to (the field format is URL; the corpus is unset)?
7. How many hires per year occur in each of the five roles (needed for ROI, not for CLI acceptance)?
8. What employee data may be retained in run diagnostics, and for how long?
9. Which geographic/compliance jurisdictions apply to catalog content?

Resolved since the 2026-08-09 PRD and therefore **not** repeated as open: LLM provider/model (SD-1); output path convention (SD-3); task-ID visibility (SD-4); Developer vs Engineer as distinct roles (SD-5); CLI name (SD-6); department filtering (SD-7); `source_reference` type (SD-8).

---

# Audit

**Timestamp:** 2026-08-20
**Persona ID:** `product-mgr`
**Action:** `create-prd`
**Artifact:** `project-context/1.define/prd.md`
**MRD:** Required and completed; not skipped
**System description:** Absent
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`)
**LLM (product constraint from SD-1):** OpenAI `gpt-4o`; temperature and token caps remain Build/setup Audit items
**Process:** Sequential with validation gate; max 2 Builder retries after initial candidate
**Supported roles:** UI Designer, UX Researcher, Product Manager, Developer, Engineer
**Task catalog:** Placeholder interfaces only; task content unresolved
**Quantitative assumption:** Three-week manual ramp baseline; 30% reduction target
**Prompt Trace:** Omitted — this artifact is a Define-phase requirements document, not a production model run; no prompts were executed against a live LLM API to populate catalog content
**Context boundary:** Approved for architecture/build handoff with the explicit constraint that development agents must not invent task-catalog contents
**Template compliance:** Headings aligned to `.cursor/templates/prd-template.md` (Executive Summary through Launch, plus Quality Assurance Checklist, Sources, Assumptions, Open Questions, Audit)

---

## Audit (sync-docs 2026-08-28)

**Timestamp:** 2026-08-28
**Persona ID:** `project-mgr` (operator requested documentation sync)
**Action:** `sync-docs`
**What changed:** P2 web/chat bullet, §8 build sequence, Resource Requirements, and A9 updated for SD-10 (`src/onboarding-ui/` wrap). CLI remains the underlying interface. A2 / catalog note: Developer content supplied; other roles still placeholders. Catalog-invention constraint unchanged.
