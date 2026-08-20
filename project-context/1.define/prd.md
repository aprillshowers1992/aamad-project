# Product Requirements Document — Automated Employee Onboarding Workflow

**Persona:** `product-mgr`
**Action:** `create-prd`
**Phase:** Define
**Intended path:** `project-context/1.define/prd.md`
**Product:** Automated Employee Onboarding Workflow
**Target organization:** AI Engineering
**Supported roles:** UI Designer, UX Researcher, Product Manager, Developer, Engineer
**Selected runtime:** CrewAI
**MVP interface:** Command-line interface
**Status:** Development handoff candidate, subject to task-catalog population

---

# 1. Executive Summary

## 1.1 Problem Statement

The AI Engineering organization requires a repeatable way to generate structured employee onboarding plans for five roles:

* UI Designer
* UX Researcher
* Product Manager
* Developer
* Engineer

The workflow must combine organization-wide onboarding requirements with role-specific enablement requirements and sequence them consistently into a 30/60/90-day onboarding structure.

The primary product risk is inconsistency: required compliance or provisioning tasks could be omitted, role-specific tasks could be prioritized incorrectly, or an AI system could invent onboarding requirements that do not exist in an approved source.

The MVP therefore treats the onboarding task catalog—not the language model—as the authoritative source of tasks.

## 1.2 Solution Overview

The product is a CrewAI-based multi-agent application that accepts three CLI inputs:

`role + department + start_date`

It generates two Markdown artifacts:

1. a role-aware 30/60/90-day onboarding plan; and
2. a manager checklist supporting execution of that plan.

Four specialized agents operate sequentially:

**Role Analyst → Plan Builder → Compliance Checker → Document Writer**

The Compliance Checker functions as a validation gate. A rejected plan returns to the Plan Builder for correction. A maximum of **two Builder retries** is allowed. After two unsuccessful rebuilds, the workflow terminates without generating an approved onboarding plan.

The system must never create onboarding tasks independently. Every generated task must correspond to a stable identifier in an approved task set.

## 1.3 Strategic Rationale

The MRD identified role-specific onboarding, fragmented ownership, provisioning requirements, and auditability as suitable areas for structured automation.

A multi-agent architecture is appropriate here because the workflow contains separable responsibilities with different validation boundaries:

* determining applicability;
* sequencing;
* independent compliance validation; and
* document rendering.

The Compliance Checker is deliberately separated from the Plan Builder so that the component constructing a plan is not also solely responsible for declaring that plan valid.

The selected runtime is CrewAI. Current CrewAI documentation supports sequential task processing and structured Pydantic/JSON outputs between tasks, both of which fit this workflow.

---

# 2. Product Goals and Non-Goals

## 2.1 MVP Goals

The MVP SHALL:

* generate a valid onboarding plan for each of the five supported roles;
* combine applicable shared and role-specific task sets;
* sequence tasks using the defined priority hierarchy;
* organize tasks into 30/60/90-day buckets;
* verify mandatory compliance and provisioning coverage;
* prevent tasks outside the approved catalog from entering generated plans;
* generate a manager-oriented checklist;
* expose clear CLI success and failure states;
* preserve structured intermediate artifacts for auditability;
* provide a future adapter boundary for HRIS and identity-provider systems without implementing those integrations.

## 2.2 Non-Goals

The MVP SHALL NOT:

* connect to a live HRIS;
* connect to a live identity provider;
* provision accounts or permissions;
* execute onboarding tasks;
* monitor task completion;
* send notifications;
* infer exact deadlines beyond assignment to the 30/60/90 buckets;
* support roles other than the five explicitly named;
* create new onboarding tasks dynamically;
* infer legal or compliance requirements;
* evaluate employee performance;
* make employment decisions.

---

# 3. Target Users

## 3.1 Primary User: Hiring Manager / Onboarding Coordinator

The primary CLI operator is a hiring manager or authorized onboarding coordinator.

The operator needs to provide minimal employee context and receive a consistent plan without manually determining which role-specific and shared requirements apply.

## 3.2 Secondary User: New Hire

The new hire is the principal consumer of the generated 30/60/90 plan but does not interact directly with the CLI in the MVP.

## 3.3 Supported Role Segments

The product supports exactly:

`UI Designer | UX Researcher | Product Manager | Developer | Engineer`

Role matching SHALL use canonical identifiers rather than free-form semantic interpretation.

No alias support is required for MVP unless aliases are explicitly added to configuration.

---

# 4. Authoritative Task-Set Model

## 4.1 Task Catalog Status

The actual onboarding task catalog has not been supplied.

Therefore, the PRD defines **task-set interfaces and placeholders only**. Development agents MUST NOT populate these placeholders with model-generated onboarding tasks.

Required task-set placeholders are:

* `shared_tasks`
* `compliance_legal_tasks`
* `it_provisioning_tasks`
* `ui_designer_tasks`
* `ux_researcher_tasks`
* `product_manager_tasks`
* `developer_tasks`
* `engineer_tasks`
* `team_integration_tasks`

The stakeholder must populate or approve these task sets before generated plans can be considered production-valid.

## 4.2 Task Definition Schema

Every authoritative task SHALL conform conceptually to:

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
- source_reference: string, required
- active: boolean, required
- version: string, required
```

Allowed `category` values are:

```text
COMPLIANCE_LEGAL
IT_PROVISIONING
ROLE_ENABLEMENT
TEAM_INTEGRATION
```

A task catalog without a unique `task_id`, applicability information, category, source reference, and bucket eligibility SHALL fail startup validation.

## 4.3 Zero-Invention Enforcement

Agents SHALL NOT pass task titles or newly composed task descriptions as authoritative task definitions between stages.

Agents SHALL select and manipulate `task_id` references.

Final task titles and descriptions SHALL be resolved from the authoritative catalog during document rendering.

If an intermediate output contains a `task_id` not present in the loaded task catalog, the workflow SHALL be rejected.

This requirement is the primary technical control supporting the success criterion of zero invented tasks.

---

# 5. Agent Roles, Responsibilities, and Interaction Pattern

## 5.1 Overall Interaction Pattern

Required workflow:

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
   +---- REJECT --> Plan Builder
                       |
                       v
                  Compliance Checker
```

Maximum Builder retries after the initial plan: **2**.

Therefore, at most three candidate plans may be evaluated:

* initial build;
* retry 1;
* retry 2.

If the third evaluated candidate is rejected, processing terminates.

The workflow SHALL NOT bypass the Compliance Checker.

The Document Writer SHALL execute only after a Checker result of `PASS`.

CrewAI's sequential-process and structured-output capabilities are suitable for this ordered task pattern. Structured outputs SHOULD be implemented with Pydantic models or equivalent runtime-supported JSON schemas rather than parsing free-form prose.

---

## 5.2 Agent 1 — Role Analyst

### Role

Determine exactly which authoritative task definitions apply to the requested onboarding scenario.

### Inputs

* validated role;
* validated department;
* validated start date;
* authoritative task catalog;
* task catalog version.

### Responsibilities

The Role Analyst SHALL:

1. select all active shared tasks applicable to the department;
2. select all active compliance/legal tasks applicable to the role and department;
3. select all active IT provisioning tasks applicable to the role and department;
4. select the matching role-specific task set;
5. select applicable team-integration tasks;
6. return task identifiers only;
7. identify the task-set origin of every selected ID.

The Role Analyst SHALL NOT:

* create tasks;
* alter task descriptions;
* sequence tasks;
* assign 30/60/90 buckets;
* omit a mandatory applicable task;
* perform compliance approval.

### Output

`RoleAnalysis`

Defined in Section 8.

---

## 5.3 Agent 2 — Plan Builder

### Role

Transform the approved applicability set into an ordered 30/60/90 onboarding plan.

### Inputs

* `RoleAnalysis`;
* task catalog;
* priority rules;
* previous validation result when executing a retry.

### Mandatory Priority Rules

Task sequencing SHALL apply this category priority, highest to lowest:

```text
1. COMPLIANCE_LEGAL
2. IT_PROVISIONING
3. ROLE_ENABLEMENT
4. TEAM_INTEGRATION
```

A lower-priority category SHALL NOT be intentionally placed ahead of an applicable higher-priority task within the same logical planning window unless the authoritative task definition prevents that ordering.

### Bucket Rules

The Plan Builder SHALL assign every selected task to exactly one of:

* `30_DAY`
* `60_DAY`
* `90_DAY`

Assignment SHALL respect the task's `allowed_buckets` configuration.

The Plan Builder SHALL NOT infer exact calendar deadlines.

For example, it may classify a task as `30_DAY`, but it SHALL NOT invent a due date such as "complete by Tuesday, April 14" unless a future source integration explicitly provides that date.

### Retry Responsibilities

When the Compliance Checker rejects a candidate, the Builder SHALL receive the structured validation findings.

On a retry it SHALL modify only the aspects identified as invalid.

It SHALL NOT remove correctly selected mandatory tasks to resolve unrelated failures.

### Output

`CandidatePlan`

---

## 5.4 Agent 3 — Compliance Checker

### Role

Serve as the mandatory independent validation gate.

### Inputs

* `RoleAnalysis`;
* `CandidatePlan`;
* authoritative task catalog;
* priority rules;
* current retry count.

### Required Checks

The Compliance Checker SHALL verify:

**Coverage**

Every applicable mandatory `COMPLIANCE_LEGAL` task is present.

Every applicable mandatory `IT_PROVISIONING` task is present.

**Traceability**

Every plan item references an existing authoritative `task_id`.

**Applicability**

Every plan task was included in the Role Analyst output.

**Uniqueness**

No task is duplicated unless future task schema explicitly permits repetition.

**Bucket validity**

Every task is placed in one of its configured `allowed_buckets`.

**Priority integrity**

The candidate respects:

`compliance/legal → IT provisioning → role enablement → team integration`

**Role integrity**

No task applicable exclusively to a different supported role appears in the plan.

### Pass Condition

The Checker returns `PASS` only when all validation checks succeed.

### Reject Condition

Any violation SHALL produce `REJECT`.

A rejection SHALL contain machine-readable findings, including affected task IDs and validation-rule identifiers.

### Retry Limit

The Checker may cause a return to Plan Builder a maximum of **two times after the initial candidate**.

The retry counter SHALL be controlled by deterministic application state, not by an agent deciding whether another retry is available.

CrewAI exposes task guardrail and retry mechanisms, but the product-level two-retry limit specified here SHALL remain an explicit application invariant so runtime defaults cannot change product behavior.

---

## 5.5 Agent 4 — Document Writer

### Role

Render an already-approved plan into human-readable Markdown.

### Preconditions

The Document Writer SHALL require:

```text
ComplianceResult.status == PASS
```

If this precondition is false, the Writer SHALL not execute.

### Outputs

The Writer produces:

```text
onboarding-plan.md
manager-checklist.md
```

### Onboarding Plan Requirements

The onboarding plan SHALL contain:

* role;
* department;
* start date;
* task-catalog version;
* 30-day section;
* 60-day section;
* 90-day section;
* task IDs;
* task titles resolved from the catalog;
* task descriptions resolved from the catalog;
* category;
* source/task-set traceability.

### Manager Checklist Requirements

The manager checklist SHALL:

* reference the same approved task IDs;
* provide checkboxes suitable for Markdown;
* group manager-relevant tasks by 30/60/90 stage;
* include employee role, department, and start date;
* include task provenance;
* not introduce additional tasks.

The Document Writer MAY alter presentation wording surrounding tasks.

It SHALL NOT alter the authoritative meaning of a task or create a new task.

---

# 6. Integration Requirements

## 6.1 MVP

There SHALL be no live external integration in MVP.

Input originates from CLI arguments.

Task definitions originate from local/version-controlled configuration.

Outputs are local Markdown files.

## 6.2 Adapter Boundary

Development SHALL isolate external employee-data acquisition behind an interface conceptually equivalent to:

```text
EmployeeContextProvider

get_employee_context(input_reference)
    -> EmployeeContext
```

The CLI implementation SHALL be one adapter:

```text
CliEmployeeContextProvider
```

Future integrations SHALL implement the same contract rather than modifying downstream agents.

## 6.3 Future HRIS Adapter

A future HRIS adapter may supply:

```text
employee_id
employee_name
role
department
start_date
manager_id
manager_name
employment_type
work_location
legal_entity
```

Only `role`, `department`, and `start_date` are required by the current MVP workflow.

No HRIS vendor is selected.

Any vendor-specific API behavior is outside this PRD.

## 6.4 Future Identity-Provider Adapter

A future identity-provider adapter may supply or verify:

```text
employee_identity_id
account_status
group_memberships
application_assignments
provisioning_status
manager_relationship
```

Its future purpose would be to distinguish requested provisioning tasks from completed provisioning work.

The MVP SHALL NOT query or modify any identity system.

## 6.5 Adapter Design Constraint

Agent business logic SHALL NOT depend on:

* HRIS vendor;
* identity-provider vendor;
* API authentication method;
* network transport;
* vendor-specific field names.

Vendor-specific translation belongs exclusively inside adapters.

---

# 7. User Interface and Experience

## 7.1 Interface

MVP interface: command line.

Required inputs:

```text
role
department
start_date
```

Example conceptual invocation:

```text
onboard --role "Developer" --department "AI Engineering" --start-date "YYYY-MM-DD"
```

Exact executable/package naming is an implementation decision.

## 7.2 Input Validation

### Role

Role is required.

Accepted canonical values:

```text
UI Designer
UX Researcher
Product Manager
Developer
Engineer
```

An unsupported role SHALL fail before any CrewAI workflow begins.

The application SHALL display the supported values.

### Department

Department is required.

It SHALL:

* contain non-whitespace content;
* be normalized for leading/trailing whitespace;
* not be silently inferred.

No fixed department enumeration is required by this PRD.

### Start Date

Start date is required.

It SHALL conform to ISO date format:

```text
YYYY-MM-DD
```

Invalid calendar dates SHALL be rejected.

The application SHALL NOT infer a missing date from system time.

## 7.3 Task-Catalog Validation

Before agent execution, the application SHALL validate that required task sets exist structurally.

Because actual task content is currently unspecified, a catalog containing unresolved placeholders SHALL be considered **development configuration only** and SHALL not produce a production-valid plan.

## 7.4 Successful User Experience

On success, the CLI SHALL display:

```text
Onboarding plan generated successfully.

Role: <role>
Department: <department>
Start date: <date>
Validation: PASS
Compliance retries used: <0-2>

Outputs:
<path>/onboarding-plan.md
<path>/manager-checklist.md
```

Exit status SHALL indicate success.

## 7.5 Input Failure Experience

For invalid input, the workflow SHALL terminate before agent execution.

Example:

```text
ERROR: Unsupported role "Data Scientist".

Supported roles:
UI Designer
UX Researcher
Product Manager
Developer
Engineer

No files were generated.
```

## 7.6 Validation Failure Experience

If compliance validation remains unsuccessful after two Builder retries:

```text
ERROR: Unable to generate a compliant onboarding plan.

Validation attempts: 3
Builder retries: 2
Final status: REJECT

Reasons:
<structured, human-readable findings>

No approved onboarding plan or manager checklist was generated.
```

The CLI SHALL return a non-success exit status.

A machine-readable validation artifact MAY be retained for diagnostics but SHALL be clearly labeled as a failed-run diagnostic rather than an onboarding plan.

---

# 8. Technical Architecture and Multi-Agent Coordination

## 8.1 Runtime

Required runtime:

```text
CrewAI
```

Required process model:

```text
Sequential
```

CrewAI supports sequential task execution, and its task API supports structured Pydantic/JSON task outputs. The implementation SHOULD use structured outputs for every agent boundary.

## 8.2 Architectural Layers

The MVP SHOULD be divided conceptually into:

```text
CLI Layer
    |
Input Validation
    |
Employee Context Adapter
    |
Task Catalog Repository
    |
Workflow Orchestrator
    |
CrewAI Agents
    |
Deterministic Validation / Retry Controller
    |
Document Renderer
    |
Filesystem Output
```

CrewAI agents SHALL not directly parse CLI arguments or write arbitrary output files outside their defined responsibility.

---

## 8.3 Shared Context

All stages SHALL have access, directly or through structured task context, to:

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

`workflow_id` SHALL uniquely identify one generation attempt.

`task_catalog_hash` SHOULD allow later verification that all stages operated against the same catalog snapshot.

---

## 8.4 Handoff A — CLI to Role Analyst

Schema:

```text
OnboardingRequest
- workflow_id: string
- role: SupportedRole
- department: string
- start_date: date
- task_catalog_version: string
```

Preconditions:

* role valid;
* department valid;
* start date valid;
* task catalog loaded successfully.

---

## 8.5 Handoff B — Role Analyst to Plan Builder

Schema:

```text
RoleAnalysis
- workflow_id: string
- role: SupportedRole
- department: string
- start_date: date
- applicable_tasks:
    - task_id: string
      source_task_set: string
      category: TaskCategory
      mandatory: boolean
- task_catalog_version: string
```

Critical invariant:

```text
∀ task in applicable_tasks:
    task.task_id MUST exist in authoritative catalog
```

The Plan Builder SHALL reject malformed analysis rather than trying to repair unidentified task IDs.

---

## 8.6 Handoff C — Plan Builder to Compliance Checker

Schema:

```text
CandidatePlan
- workflow_id: string
- build_attempt: integer
- role: SupportedRole
- department: string
- start_date: date
- buckets:
    30_DAY:
        - task_id
        - sequence
    60_DAY:
        - task_id
        - sequence
    90_DAY:
        - task_id
        - sequence
- task_catalog_version: string
```

`build_attempt` values:

```text
1 = initial build
2 = first retry
3 = second/final retry
```

No free-form task definitions SHALL be accepted in `CandidatePlan`.

---

## 8.7 Handoff D — Compliance Checker Decision

Schema:

```text
ComplianceResult
- workflow_id: string
- evaluated_build_attempt: integer
- status: PASS | REJECT
- checks:
    mandatory_compliance_complete: boolean
    mandatory_provisioning_complete: boolean
    all_tasks_traceable: boolean
    all_tasks_applicable: boolean
    no_duplicates: boolean
    bucket_rules_valid: boolean
    priority_rules_valid: boolean
    role_integrity_valid: boolean
- findings:
    - rule_id: string
      severity: ERROR
      task_ids: list[string]
      message: string
- task_catalog_version: string
```

A `PASS` result requires every Boolean validation field to equal `true`.

Agents SHALL NOT be permitted to return `PASS` while including an error-level finding.

---

## 8.8 Handoff E — Rejection to Plan Builder

For attempts 1 or 2 that fail, the Builder receives:

```text
PlanRevisionRequest
- previous_candidate_plan
- compliance_result
- next_build_attempt
```

The Builder SHALL use the findings as correction constraints.

It SHALL continue using the original `RoleAnalysis`.

The Role Analyst SHALL not rerun solely because the Builder produced an invalid sequence.

If source applicability itself is shown to be structurally invalid, the workflow SHOULD terminate as a configuration/system error rather than allowing agents to reinterpret the catalog.

---

## 8.9 Handoff F — Approved Plan to Document Writer

Schema:

```text
ApprovedPlan
- candidate_plan
- compliance_result
- task_catalog_version
- task_catalog_hash
```

Precondition:

```text
compliance_result.status == PASS
```

The Document Writer resolves each `task_id` against the catalog and renders the two Markdown outputs.

---

# 9. Retry and Failure State Machine

Required deterministic behavior:

```text
BUILD attempt 1
    |
CHECK
    |
    +-- PASS --> WRITE --> SUCCESS
    |
    +-- REJECT --> BUILD attempt 2
                       |
                     CHECK
                       |
                       +-- PASS --> WRITE --> SUCCESS
                       |
                       +-- REJECT --> BUILD attempt 3
                                          |
                                        CHECK
                                          |
                                          +-- PASS --> WRITE --> SUCCESS
                                          |
                                          +-- REJECT --> TERMINAL FAILURE
```

The retry counter SHALL NOT reset during one workflow.

No fourth build attempt is permitted.

On terminal failure:

* do not invoke Document Writer;
* do not create approved plan output;
* do not create manager checklist output;
* emit structured diagnostic information;
* return non-success CLI status.

---

# 10. Functional Requirements

## P0 — Must Have

### FR-001 — Accept Supported Input

The CLI SHALL accept role, department, and start date.

### FR-002 — Validate Input Before Agent Execution

Invalid inputs SHALL fail without invoking the crew.

### FR-003 — Resolve Applicable Tasks

The Role Analyst SHALL select applicable task IDs from approved task sets.

### FR-004 — Support Five Roles

Exactly the five named roles SHALL be supported.

### FR-005 — Apply Priority Ordering

The Plan Builder SHALL prioritize:

`compliance/legal → IT provisioning → role enablement → team integration`

### FR-006 — Generate 30/60/90 Structure

Every applicable task SHALL be assigned to exactly one supported bucket.

### FR-007 — Validate Mandatory Coverage

The Compliance Checker SHALL verify 100% presence of applicable mandatory compliance and IT provisioning tasks.

### FR-008 — Enforce Task Traceability

Every generated task SHALL reference a valid authoritative `task_id`.

### FR-009 — Implement Validation Loop

Rejected plans SHALL return to Plan Builder, maximum two retries.

### FR-010 — Fail Closed

If compliance validation does not pass after the permitted retries, no approved user-facing documents SHALL be generated.

### FR-011 — Generate Onboarding Markdown

Successful workflows SHALL generate a 30/60/90 Markdown onboarding plan.

### FR-012 — Generate Manager Checklist

Successful workflows SHALL generate a Markdown manager checklist based on exactly the approved plan.

### FR-013 — Preserve Traceability

Generated documents SHALL expose task IDs or equivalent traceability metadata.

### FR-014 — Adapter Boundary

Employee-context acquisition SHALL be abstracted sufficiently to permit later CLI, HRIS, or identity-provider implementations.

---

# 11. Feature Prioritization

## Must Have

* CLI input and validation
* five-role enumeration
* authoritative task-catalog loader
* placeholder task-set interfaces
* Role Analyst
* Plan Builder
* Compliance Checker
* Document Writer
* sequential CrewAI orchestration
* structured handoff schemas
* two-retry compliance loop
* mandatory-task validation
* zero-invented-task validation
* priority rules
* 30/60/90 bucketing
* onboarding Markdown output
* manager checklist Markdown output
* failure-safe behavior
* task traceability
* integration adapter boundary

## Should Have

* structured run diagnostics
* catalog version/hash recorded in output
* human-readable compliance findings
* configurable output directory
* deterministic filenames
* duplicate-task detection
* unit-test fixtures for all five roles
* deterministic application-level schema validation around CrewAI outputs

## Could Have

* alternative Markdown templates
* CLI `--verbose` mode
* machine-readable JSON result alongside Markdown
* dry-run validation mode
* configurable role aliases
* catalog linting command
* plan-diff capability between task-catalog versions

None of the Could Have features is required for MVP acceptance.

---

# 12. Non-Functional Requirements

## 12.1 Correctness

Correctness takes precedence over generation completeness.

The product SHALL fail rather than knowingly generate an onboarding plan that violates mandatory-task coverage or traceability requirements.

## 12.2 Determinism at Control Boundaries

LLM reasoning may determine applicability and sequencing within defined constraints.

The following SHALL be deterministic:

* input validation;
* role enumeration;
* task-ID existence validation;
* retry counting;
* maximum retries;
* output-schema validation;
* PASS eligibility;
* terminal failure;
* document-write eligibility.

## 12.3 Auditability

Every run SHOULD record:

```text
workflow_id
input values
task catalog version/hash
selected task IDs
candidate plans
validation findings
retry count
final status
output file paths
```

## 12.4 Security

Because no live integrations exist, the MVP SHALL not require HRIS or identity-provider credentials.

Secrets for the selected LLM provider SHALL not be embedded in task catalogs or generated Markdown.

## 12.5 Reliability

Malformed agent output SHALL be treated as a failed stage rather than silently parsed or guessed.

Structured CrewAI outputs SHOULD use Pydantic or JSON schemas to reduce handoff parsing ambiguity. CrewAI specifically documents these structured output mechanisms and recommends structured outputs for production data exchange.

---

# 13. Success Metrics and Validation Criteria

## 13.1 Ramp-Time Reduction

### Target

**30% reduction in ramp time compared with an assumed three-week manual baseline.**

### Assumption

**ASSUMPTION A1:** Current manual ramp time is three weeks.

This baseline was supplied as an assumption and has not been measured against actual organizational onboarding data.

The 30% value is a stakeholder-defined product success target, not an externally sourced benchmark.

A 30% reduction against a three-week baseline implies a target equivalent of approximately:

```text
3 weeks × 70% = 2.1 weeks
```

This derived value is arithmetic, not measured organizational evidence.

### MVP Test Method

The MVP itself does not execute onboarding or track employees, so actual ramp-time reduction cannot be validated solely through automated system tests.

Validation SHALL occur through a pilot:

1. define a role-specific "ramp complete" criterion before the pilot;
2. establish actual historical/manual baseline data;
3. record start-to-ramp-complete duration for onboarding workflows using the generated plans;
4. compare median or agreed aggregation method against baseline;
5. calculate percentage reduction.

Formula:

```text
reduction =
(baseline_ramp_time - generated_plan_ramp_time)
/
baseline_ramp_time
× 100
```

Product success criterion:

```text
reduction >= 30%
```

Until measured baseline data replaces A1, this metric remains a validation hypothesis rather than a demonstrated outcome.

---

## 13.2 Mandatory Compliance and Provisioning Coverage

### Target

**100% of mandatory compliance and provisioning tasks present in every generated plan.**

### Automated Test Method

For each supported role and representative department fixture:

1. derive expected mandatory IDs directly from the authoritative catalog;
2. generate a plan;
3. extract all task IDs from the approved candidate;
4. calculate:

```text
mandatory_coverage =
count(expected_mandatory_ids ∩ generated_ids)
/
count(expected_mandatory_ids)
```

Required result:

```text
mandatory_coverage == 1.0
```

Test coverage SHALL include:

* every supported role;
* task sets containing multiple mandatory tasks;
* tasks applicable to all roles;
* tasks applicable to one role only;
* rejection cases where Builder output intentionally omits one required task.

A deliberately incomplete candidate MUST be rejected by the Compliance Checker.

---

## 13.3 Zero Invented Tasks

### Target

**Zero invented tasks.**

Every generated task must be traceable to a defined task set.

### Automated Test Method

For every task ID in every generated plan:

```text
assert generated_task.task_id in authoritative_catalog
```

Additionally:

```text
assert generated_task.task_id in role_analysis.applicable_task_ids
```

Required result:

```text
invalid_task_count == 0
```

Testing SHALL inject an unknown task ID into a candidate plan and verify that:

* Compliance Checker returns `REJECT`;
* `all_tasks_traceable == false`;
* Document Writer does not run;
* no approved documents are emitted.

Document-level validation SHALL also verify that rendered task titles/descriptions correspond to the catalog entry identified by each task ID.

---

# 14. Validation Test Matrix

Minimum acceptance coverage SHALL include:

### Valid Happy Paths

One successful generation for each of:

* UI Designer
* UX Researcher
* Product Manager
* Developer
* Engineer

### Invalid Inputs

* missing role;
* unsupported role;
* blank department;
* missing start date;
* malformed start date;
* impossible calendar date.

### Compliance Failures

* missing mandatory compliance task;
* missing mandatory provisioning task;
* invented task ID;
* task for wrong role;
* duplicate task;
* invalid bucket assignment;
* priority-rule violation.

### Retry Tests

* initial candidate passes: 0 retries;
* initial fails, retry 1 passes;
* attempts 1 and 2 fail, retry 2 passes;
* all three candidate evaluations fail: terminal failure;
* verify no fourth Builder attempt occurs.

### Output Tests

Successful run:

* exactly two required Markdown artifacts generated;
* plan contains 30/60/90 sections;
* checklist reflects approved task IDs;
* role/department/start date correct.

Failed run:

* no approved plan generated;
* no manager checklist generated;
* failure reason visible;
* non-success CLI status returned.

---

# 15. Scope Boundaries

## In Scope

* role-aware onboarding-plan generation;
* five supported roles;
* shared and role-specific task-set selection;
* defined sequencing priority;
* 30/60/90 organization;
* compliance validation;
* provisioning-task validation;
* manager checklist generation;
* CLI workflow;
* Markdown output;
* CrewAI multi-agent coordination;
* future integration adapter interfaces.

## Out of Scope

* live HR integration;
* live IT/identity integration;
* account provisioning;
* task execution;
* completion tracking;
* workflow notifications;
* employee reminders;
* exact deadline inference beyond 30/60/90 buckets;
* onboarding analytics dashboard;
* new roles;
* automatic generation of catalog tasks;
* autonomous legal/compliance interpretation;
* performance evaluation.

Any development agent proposing an out-of-scope item SHALL classify it as Future Work rather than adding it to MVP requirements.

---

# 16. Implementation Strategy

## Phase 1 — Define

Completed/current:

* MRD
* PRD

Remaining before architecture boundary approval:

* populate authoritative task catalog;
* resolve task-set ownership;
* define exact role-task applicability.

## Phase 2 — Build

Recommended implementation order:

1. task schemas and catalog validation;
2. CLI/input validation;
3. structured handoff models;
4. Role Analyst;
5. Plan Builder;
6. Compliance Checker;
7. deterministic retry controller;
8. Document Writer;
9. Markdown templates;
10. acceptance and adversarial tests;
11. future integration adapter interfaces.

## Phase 3 — Deliver

Deployment packaging, operational runbook, environment configuration, and release management belong to downstream architecture/build/delivery personas and are not specified here.

---

# 17. Assumptions

**A1 — Ramp baseline.** Manual onboarding ramp time is assumed to be **three weeks**. This is not measured organizational data.

**A2 — Task catalogs.** The approved task catalog will be supplied before production acceptance. Current task sets are placeholders only.

**A3 — Department behavior.** Department is required as input and may affect future task applicability, but no authoritative department enumeration has been supplied.

**A4 — Local output.** Markdown files may be written to a local/configured filesystem in MVP because no document-management integration was requested.

**A5 — CLI operator.** The CLI is operated by an authorized manager, onboarding coordinator, developer, or evaluator. Authentication is not included in MVP because the application has no live enterprise integrations.

**A6 — First-party task authority.** The future task catalog, once stakeholder-approved, is the authoritative source for onboarding requirements. Language-model world knowledge is not an acceptable source of onboarding tasks.

No additional quantitative market, cost, performance, throughput, or staffing figures are assumed.

---

# 18. Open Questions

The following do not block PRD structure but must be resolved before production-readiness:

1. What are the actual tasks in each placeholder task set?
2. Who owns approval and maintenance of each task set?
3. Are any tasks department-specific within AI Engineering?
4. What defines "ramp complete" for each of the five roles?
5. How will the assumed three-week baseline be replaced with measured data?
6. Should task source references point to policies, internal documentation, ticket templates, or another authority?
7. Should generated Markdown expose raw task IDs to end users or only in an audit appendix?
8. Which LLM provider/model will be configured beneath CrewAI?
9. What exact local/configured output path convention should downstream implementation adopt?

These questions SHALL NOT be resolved by development agents through invention.

---

# 19. Development Guardrails

Development agents SHALL treat the following as non-negotiable product invariants:

```text
SUPPORTED_ROLES =
{UI Designer, UX Researcher, Product Manager, Developer, Engineer}

PRIORITY =
COMPLIANCE_LEGAL
> IT_PROVISIONING
> ROLE_ENABLEMENT
> TEAM_INTEGRATION

MAX_BUILDER_RETRIES = 2

APPROVED_OUTPUT_REQUIRES =
ComplianceResult.status == PASS

TASK_AUTHORITY =
authoritative task catalog only

LIVE_INTEGRATIONS =
none in MVP
```

If implementation constraints conflict with these invariants, development SHALL escalate the conflict rather than silently changing product behavior.

---

# 20. PRD Acceptance Criteria

The PRD is considered implemented for MVP only when:

* all five supported roles generate plans from defined task fixtures;
* invalid inputs fail before agent execution;
* every inter-agent handoff conforms to a structured schema;
* priority rules are enforced;
* mandatory compliance coverage is 100%;
* mandatory provisioning coverage is 100%;
* no unknown task ID can reach approved output;
* the Checker cannot be bypassed;
* no more than two Builder retries occur;
* retry exhaustion produces terminal failure;
* the Writer executes only after `PASS`;
* successful runs generate both Markdown documents;
* failed runs generate neither approved document;
* future HRIS/IdP interfaces remain decoupled from agent logic;
* automated tests prove traceability and mandatory coverage requirements.

---

# 21. Sources

**Product requirements source:** Stakeholder instructions in the `*create-prd` request and subsequent clarification that task sets should remain placeholders and technical architecture should receive emphasis.

**Market/product context:** Automated Employee Onboarding Workflow MRD produced during the Define phase.

**CrewAI runtime:** CrewAI official documentation. CrewAI documents sequential process orchestration, task-level structured outputs including Pydantic/JSON, and task guardrail retry configuration.

No competitor figures or external market-size figures are required to establish the technical MVP requirements in this PRD.

---

# 22. Audit

**Timestamp:** 2026-08-09
**Persona ID:** `product-mgr`
**Action:** `create-prd`
**Artifact:** `project-context/1.define/prd.md`
**MRD:** Required and completed; not skipped
**Runtime:** `crewai`
**Process:** Sequential with validation gate
**Compliance retry rule:** Maximum 2 returns to Plan Builder after initial candidate
**Supported roles:** UI Designer, UX Researcher, Product Manager, Developer, Engineer
**Task catalog:** Placeholder interfaces only; task content unresolved
**Quantitative assumption:** Three-week manual ramp baseline
**Success target:** 30% ramp-time reduction against that assumed baseline
**Context boundary:** Approved for architecture handoff only with the explicit constraint that development agents must not invent task-catalog contents.
