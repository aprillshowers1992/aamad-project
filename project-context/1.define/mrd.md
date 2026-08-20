# Market Research Document — Automated Employee Onboarding Workflow

**Persona:** `product-mgr`
**Action:** `create-mrd`
**Phase:** Define
**Intended path:** `project-context/1.define/mrd.md`
**Research date:** 2026-08-09

## Research Query Structure

**Primary Focus:** Automated Employee Onboarding Workflow for an AI Engineering organization, using a multi-agent system to coordinate role-specific onboarding for UI Designers, UX Researchers, Product Managers, Developers, and Engineers.

**Internal market:** Hiring managers and new hires across the five specified AI Engineering roles.

**Selected Runtime:** Not specified. Runtime selection is intentionally deferred to architecture/build; the product opportunity does not depend on a particular agent framework.

---

# Executive Summary

## Market Opportunity

Employee onboarding is a persistent experience and operational problem even in organizations with established HR processes. Gallup reports that only **12% of employees strongly agree their organization does a great job of onboarding**. BambooHR research found that **70% of new hires decide whether a job is the right fit within their first month**, while **44% report regrets or second thoughts within their first week**. The same research identified lack of clarity about who can answer questions (65%), inadequate product/service training (62%), and technology problems (51%) among major onboarding frustrations.

For this project, the addressable "market" is deliberately internal: hiring managers and new hires in five AI Engineering roles—UI Designer, UX Researcher, Product Manager, Developer, and Engineer. No organization-specific hiring volume, headcount, onboarding labor, attrition, or salary data was supplied. Therefore, an absolute dollar TAM/SAM/SOM would be fabricated and is not used. Opportunity is instead sized as **100% of onboarding events within these five roles**, with financial value to be calculated after internal baseline measurements are collected. **Assumption A1:** the organization performs enough recurring hiring across these roles for reusable role-specific workflows to create meaningful operational leverage.

## Technical Feasibility

The workflow is technically feasible using existing HR, identity, collaboration, project-management, knowledge, and automation APIs. Current products already demonstrate automated task creation, role-based provisioning, document routing, onboarding plans, reminders, identity lifecycle management, and cross-system workflow execution. Examples include Workday Onboarding Plans, ServiceNow Employee Journey Management, Rippling workflows, BambooHR Onboarding, Deel onboarding, Microsoft Entra Lifecycle Workflows, Okta Lifecycle Management, and Zapier onboarding automation.

A multi-agent architecture is differentiated not because conventional onboarding cannot be automated, but because this use case contains several distinct responsibilities: interpreting role context, preparing access and resources, coordinating manager obligations, answering new-hire questions, tracking progress, and escalating exceptions. Multi-agent systems can divide complex work among specialized agents, support routing and handoffs, and introduce human approval at sensitive execution points. They also create additional coordination, security, observability, and cost risks that must be controlled.

## Recommended Approach

Proceed with an MVP focused on **orchestrating—not replacing—the organization's systems of record**. The system should ingest an approved hire/start event, identify the employee's role, instantiate the appropriate onboarding plan, coordinate pre-start and post-start tasks, surface role-relevant knowledge, monitor completion, and escalate exceptions to the hiring manager or responsible human.

The strongest initial differentiation is **role-aware adaptive orchestration across the five AI Engineering roles**, with auditable handoffs and human approval for consequential actions. The MVP should not attempt autonomous employment decisions, unrestricted permission assignment, performance evaluation, or unsupervised changes to authoritative HR/identity records.

---

# 1. Market Analysis & Opportunity Assessment

## Key Insights

### 1.1 Validated pain points

Evidence supports five recurring onboarding problems relevant to the proposed workflow:

1. **Onboarding quality is broadly weak.** Gallup reports only 12% of employees strongly agree their organization does a great job onboarding.
2. **Early experience affects retention decisions quickly.** BambooHR found 70% of new hires decide whether a role is the right fit within one month and estimates organizations have roughly 44 days to influence long-term retention.
3. **Ownership is fragmented.** SHRM notes that onboarding spans HR/training, supervisors, coworkers, executives, and buddies and warns that generalized responsibility without actionable accountability undermines programs.
4. **Role-specific context matters.** SHRM recommends modifying onboarding for different employee groups rather than treating all employees identically.
5. **Manual and disconnected processes create administrative friction.** BambooHR's 2024 HR research reported 29% of HR teams saying manual/unorganized onboarding created tedious work that frustrated new hires, while 35% struggled to create onboarding that quickly engaged and acclimated employees.

These findings validate the general problem. They do **not** prove that each percentage applies to this AI Engineering organization; internal validation remains required.

### 1.2 Target user segments

**Primary segment — New hires**

| Role            | Likely onboarding context                                                                    | Role-specific need                                                              |
| --------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| UI Designer     | Design system, product surfaces, prototyping environment, design-to-engineering handoff      | Rapid access to design tools, components, standards, current product context    |
| UX Researcher   | Research repositories, participant/research processes, privacy requirements, product context | Research governance, repositories, tools, prior studies, stakeholder map        |
| Product Manager | Roadmaps, customer/product context, metrics, decision processes, cross-functional network    | Fast synthesis of strategy, priorities, metrics, dependencies, stakeholders     |
| Developer       | Repositories, local/dev environments, CI/CD, coding conventions, tickets                     | Reliable technical setup and first contribution path                            |
| Engineer        | Architecture, infrastructure/services, operational practices, security/access                | System context, environment access, technical ownership and operating standards |

**Evidence boundary:** the five roles are stakeholder-provided. The detailed needs above are **Assumption A2**, inferred from typical role responsibilities and requiring validation with actual hiring managers/new hires.

**Primary segment — Hiring managers**

Hiring managers need visibility into readiness, outstanding tasks, dependencies, first-week expectations, and exceptions without manually chasing every participant. SHRM's responsibility model supports explicit accountability rather than diffuse ownership.

**Secondary segment — enabling functions**

HR/People Operations, IT/identity administrators, security, learning/training owners, and onboarding buddies may participate in workflows. Their inclusion is **Assumption A3** pending confirmation of the organization's operating model.

### 1.3 Current workflow challenges

A likely current-state workflow is:

**Hire approved → employee data entered → manager/HR launches checklist → IT/access requests → equipment/tool setup → documents/training → introductions → role-specific learning → first tasks → manager follow-up.**

**Assumption A4:** this sequence represents the organization's current process conceptually. No internal system description or process map was supplied.

External evidence shows why this flow is difficult: Workday supports sequential and parallel onboarding tasks; ServiceNow explicitly treats employee journeys as cross-enterprise processes; Zapier identifies missing tasks, manual data entry, slow submissions, and lack of unified progress visibility as onboarding automation problems.

### 1.4 Opportunity sizing

Because this is an internal market, the most defensible opportunity model is event-based rather than industry-revenue-based.

**Addressable onboarding volume**

`Annual onboarding events = annual UI Designer hires + UX Researcher hires + PM hires + Developer hires + Engineer hires`

**Administrative value**

`Annual coordination value = onboarding events × baseline manager/admin hours per event × loaded hourly cost × automatable share`

**Ramp value**

`Annual ramp value = onboarding events × reduction in days-to-productivity × estimated value of one productive day`

**Avoided-error value**

`Annual exception value = onboarding events × baseline costly-error rate × average remediation cost`

Every input above is currently **unsourced and therefore an assumption**. No numeric ROI should be presented until baseline data is collected.

### 1.5 Business case

The business case should be evaluated against:

* time-to-productivity;
* percentage of Day-1 access/equipment requirements completed on time;
* hiring-manager administrative hours per hire;
* overdue onboarding tasks;
* onboarding completion;
* new-hire satisfaction/clarity;
* 30/60/90-day retention where sample sizes permit.

SHRM explicitly identifies time-to-productivity, retention, new-hire surveys, satisfaction/engagement, performance measures, and feedback as useful onboarding measures.

---

# 2. Technical Feasibility & Requirements Analysis

## Key Insights

### 2.1 Feasible integration pattern

Existing products demonstrate the required primitives:

* Workday supports configurable onboarding plans, staged content, tasks, notifications, audiences, and reporting.
* Rippling triggers onboarding actions based on attributes such as start date, location, and role and can provision applications and devices.
* Microsoft Entra Lifecycle Workflows automates joiner/mover/leaver identity tasks using conditions and workflow tasks.
* Okta Lifecycle Management automates identity creation, provisioning, and deprovisioning.
* Zapier connects onboarding events across HRIS, messaging, forms, project-management, and other applications.

The technical opportunity is therefore orchestration and intelligence above existing systems, not invention of basic onboarding automation.

### 2.2 Candidate multi-agent pattern

**Recommended conceptual pattern: bounded orchestrator + specialists.**

Candidate responsibilities:

* **Onboarding Orchestrator:** owns workflow state and routes work.
* **Role Context Agent:** selects role-specific onboarding content/tasks.
* **Access & Setup Agent:** prepares tool/access/equipment requests but requires approval for consequential changes.
* **Knowledge Agent:** answers questions from approved organizational sources.
* **Manager Coordination Agent:** prompts manager actions, meetings, introductions, and first assignments.
* **Progress & Exception Agent:** detects missing/late tasks and escalates.

This is a research recommendation, not an approved architecture.

Microsoft describes multi-agent orchestration as decomposition into specialized capabilities with routing, checkpoints, traceability, and human-in-the-loop controls. IBM similarly identifies specialization and flexibility as benefits while warning about coordination complexity and unpredictable behavior.

### 2.3 Integration requirements

**Expected integrations — Assumption A5 until system inventory is supplied:**

* HRIS/ATS or authoritative hire event;
* identity provider;
* email/calendar;
* team messaging;
* project/work management;
* documentation/knowledge repository;
* learning platform;
* source-control/developer systems for technical roles;
* design/research systems for design/research roles;
* equipment/device management where applicable.

### 2.4 Scalability

For the internal MVP, scale is unlikely to be dominated by raw transaction throughput. More important constraints are:

* number of integrations;
* number of role/department policy variants;
* concurrent onboarding workflows;
* reliability of external APIs;
* agent/tool-call cost;
* audit-log volume;
* permission boundaries.

**Assumption A6:** onboarding volume is moderate enough that correctness and observability should take priority over high-throughput optimization.

### 2.5 Technical risks

Multi-agent systems introduce coordination and shared-failure risks. Anthropic's production experience notes challenges in agent coordination, evaluation, and reliability; IBM identifies coordination complexity and unpredictable behavior; OWASP identifies additional attack surfaces involving reasoning, memory, tools, identity, human oversight, and multi-agent interactions.

Implication: deterministic workflow logic should govern critical state transitions, while agents handle interpretation, personalization, knowledge retrieval, and bounded delegation.

---

# 3. User Experience & Workflow Analysis

## Key Insights

### 3.1 Target journey

**Pre-start**

Approved hire triggers onboarding → role identified → role plan instantiated → required systems/tasks identified → manager validates plan → welcome/preboarding materials delivered → access/equipment requests initiated.

**Day 1**

System verifies readiness → new hire receives one prioritized onboarding view → missing prerequisites are escalated → role-specific orientation begins → manager receives readiness summary.

**Week 1**

Agent system guides learning, introductions, environment setup, role context, and first meaningful task while answering questions from approved sources.

**Weeks 2–4**

System tracks milestones, adapts reminders/resources, surfaces blockers, collects structured feedback, and provides manager summaries.

**30/60/90 days**

Human manager evaluates outcomes; system measures completion and onboarding experience but does not autonomously make employment/performance decisions.

### 3.2 Personalization requirement

Personalization should be based on explicit attributes such as role, team, location, employment type, and start date—not opaque inference. Existing products already support audience/attribute-based personalization: Workday supports audiences and condition rules; Rippling uses employee attributes; Deel can assign workflows based on department or location.

The proposed differentiation is to combine this deterministic segmentation with context-aware agent assistance.

### 3.3 Full vs partial automation

**Suitable for fuller automation:**

* checklist generation from approved templates;
* reminders;
* progress aggregation;
* approved-content retrieval;
* meeting/task preparation;
* routing;
* status summaries;
* detection of missing prerequisites.

**Require human approval or ownership:**

* privileged access grants;
* exceptions to access policy;
* employment/compliance decisions;
* changes to authoritative personnel records;
* evaluation of employee performance;
* sensitive HR communications;
* deviations from approved onboarding policy.

### 3.4 Human-in-the-loop

Human approval should be explicit at consequential boundaries. Modern agent frameworks support pausing workflows for approval before tool execution, and NIST recommends structured risk management for generative-AI systems.

### 3.5 Adoption factors

Likely adoption enablers:

* one clear source of onboarding status;
* visible ownership;
* fewer repetitive questions;
* role-relevant information instead of generic content;
* explainable recommendations;
* ability for managers to override or edit plans;
* no requirement to replace systems of record.

Likely barriers:

* inaccurate or stale knowledge;
* excessive notifications;
* distrust of autonomous access actions;
* unclear accountability between agents and humans;
* tool proliferation;
* privacy concerns.

---

# 4. Production & Operations Requirements

## Key Insights

### 4.1 Deployment approach

The MVP should operate as an orchestration layer over existing enterprise systems. It should maintain only the workflow state, audit information, role configuration, approved knowledge references, and minimum data necessary for execution.

The authoritative employee record should remain in the organization's existing HR/identity systems.

### 4.2 Monitoring and observability

Required telemetry should include:

* workflow ID and hire ID/pseudonymous reference;
* agent/tool actions;
* handoffs;
* approval events;
* external API results;
* failures/retries;
* task completion timestamps;
* exception/escalation events;
* model/runtime version;
* prompt/configuration version where relevant;
* cost/token telemetry.

Traceability is especially important for multi-agent systems; current agent platforms emphasize workflow tracing and observability as production capabilities.

### 4.3 Security

Minimum requirements:

* least-privilege tool access;
* role-based access control;
* separation of read and write capabilities;
* human approval for privileged actions;
* secret isolation;
* audit logging;
* approved knowledge sources;
* prompt-injection/tool-abuse defenses;
* data minimization;
* retention controls;
* explicit boundaries on agent memory.

OWASP's agentic-security guidance identifies tools, identity, memory, reasoning, human oversight, and multi-agent interactions as attack surfaces. NIST's Generative AI Profile provides a broader framework for trustworthy AI risk management.

### 4.4 Maintenance

Role onboarding plans must be versioned. A change to a role's approved tools, policies, repositories, training, or responsibilities should not silently modify already-running onboarding workflows unless explicitly approved.

### 4.5 Cost structure

No credible dollar estimate can be produced from supplied inputs.

**Assumption A7:** major cost categories are implementation/integration labor, model inference, observability, hosting/state storage, security review, and ongoing workflow/content maintenance.

A later PRD/SAD should establish measurable cost ceilings after the runtime and integration inventory are known.

---

# 5. Innovation & Differentiation Analysis

## Key Insights

### 5.1 Competitive landscape

The market already contains strong onboarding automation. The proposed system should therefore avoid positioning itself merely as "automated onboarding."

| Solution                               | Demonstrated strength                                                                             | Limitation relative to proposed internal use case                                                                                                                                                                |
| -------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BambooHR Onboarding                    | Packets, e-signatures, checklists, progress, customizable role/work-mode templates                | Primarily HRIS-centered structured onboarding; differentiation would require deeper cross-tool, role-context reasoning and specialized agent coordination.                                                       |
| Workday Onboarding Plans/Journeys      | Personalized staged plans, audiences, tasks, content, reporting, broader employee journeys        | Powerful platform configuration; some capabilities require additional SKUs. Proposed system could sit across heterogeneous tools rather than requiring Workday to be the experience/orchestration center.        |
| ServiceNow Employee Journey Management | Cross-enterprise lifecycle events and personalized journeys                                       | Enterprise platform approach; proposed differentiation is lightweight AI Engineering role specialization and conversational/adaptive orchestration.                                                              |
| Rippling                               | HR + IT automation, app provisioning, devices, role/attribute-based workflows                     | Particularly strong on operational provisioning. Proposed system should differentiate through knowledge/context, adaptive guidance, and manager/new-hire coordination rather than compete on basic provisioning. |
| Deel                                   | Department/location workflows, Slack onboarding, HRIS and global IT/device support                | Strong global workforce/IT orientation; proposed system focuses on deeper role-specific AI Engineering workflows.                                                                                                |
| Microsoft Entra Lifecycle Workflows    | Joiner/mover/leaver identity automation, conditions, audit/history                                | Identity-governance scope rather than complete role learning/manager/new-hire experience.                                                                                                                        |
| Okta Lifecycle Management              | Automated identity provisioning/deprovisioning across applications                                | Identity lifecycle is only one component of full onboarding.                                                                                                                                                     |
| Zapier                                 | Broad integration ecosystem, triggered tasks, notifications, documents, chatbot/onboarding portal | Flexible automation still requires workflow construction and governance; proposed system can differentiate with bounded specialist agents and role-aware adaptive decisions.                                     |

### 5.2 Multi-agent differentiators

The defensible differentiation is the combination of:

**Specialization.** Separate agents can own knowledge, setup, manager coordination, role context, and exception monitoring instead of concentrating every instruction and tool in one monolithic agent.

**Adaptive routing.** A Developer blocked on repository access can be routed differently from a UX Researcher missing research-governance materials.

**Parallel preparation.** Independent setup, knowledge preparation, scheduling, and resource discovery can proceed concurrently where dependencies permit.

**Persistent workflow context.** The system can maintain a coherent onboarding state across pre-start, Day 1, Week 1, and later milestones.

**Bounded autonomy.** Routine coordination can execute automatically while privileged or ambiguous actions stop for human review.

**Auditable handoffs.** Agent ownership and workflow transitions can be logged rather than buried in informal email/Slack exchanges.

These are technically plausible differentiators supported by current multi-agent orchestration patterns, but their actual business advantage over a well-designed deterministic workflow is **not yet validated**. That comparison must be tested during MVP evaluation.

### 5.3 Why not a single agent?

A single agent may be sufficient if the final scope is mainly question answering plus checklist reminders. Multi-agent architecture becomes justified when the system needs materially different permissions, tools, contexts, approval boundaries, or concurrent responsibilities.

Therefore:

**Go multi-agent only if specialization produces measurable improvements in control, maintainability, accuracy, or workflow completion.**

This prevents "multi-agent" from becoming an architectural requirement unsupported by product value.

### 5.4 Patent/IP landscape

No patent clearance or freedom-to-operate analysis was conducted. **Assumption A8:** standard workflow orchestration, retrieval, role-based automation, and agent handoffs are implementation patterns rather than a claimed proprietary moat. Formal IP review is required before making patentability or freedom-to-operate claims.

### 5.5 Monetization

N/A as a primary objective because the stated market is the internal AI Engineering organization.

Operational value—not external subscription revenue—should drive prioritization.

---

# Critical Decision Points

## Go / No-Go Factors

**Go if:**

* there is recurring onboarding volume across the five roles;
* current onboarding requires meaningful manual coordination;
* authoritative systems expose usable APIs/integration mechanisms;
* role-specific onboarding content can be defined;
* hiring managers agree to explicit ownership/approval boundaries;
* the organization can establish a measurable baseline.

**No-Go / redesign if:**

* onboarding volume is too low to justify automation;
* the organization cannot identify an authoritative hire event;
* critical systems cannot be integrated safely;
* no owners exist for role-specific onboarding content;
* the solution would require agents to make autonomous employment decisions;
* a simple deterministic workflow satisfies the measurable need at materially lower complexity.

## Technical Architecture Choices

1. Use deterministic workflow state for critical milestones.
2. Use specialized agents only where reasoning or contextual adaptation adds value.
3. Require explicit approval for privileged actions.
4. Keep systems of record authoritative.
5. Implement traceable handoffs and workflow checkpoints.
6. Select `AAMAD_TARGET_RUNTIME` during architecture/build evaluation; no runtime has been approved in this MRD.

## Market Positioning

**Internal positioning:** "A role-aware onboarding orchestration layer that coordinates people, knowledge, access, and tools so every AI Engineering hire reaches productive work through an auditable, personalized workflow."

## Resource Requirements

Exact staffing, timeline, and budget are **Assumption A9 / TBD** because integration inventory and runtime are unknown.

Likely capabilities required include product ownership, agent/backend engineering, enterprise integration expertise, security/identity review, UX design, and representatives from each of the five roles.

---

# Risk Assessment Matrix

| Risk                                                               | Level      | Impact                                      | Mitigation                                                      |
| ------------------------------------------------------------------ | ---------- | ------------------------------------------- | --------------------------------------------------------------- |
| Agent grants inappropriate access or performs consequential action | High       | Security/privacy exposure                   | Least privilege, deterministic policies, mandatory approvals    |
| Incorrect/stale onboarding knowledge                               | High       | New hire receives misleading guidance       | Approved retrieval corpus, ownership/versioning, source display |
| Agent/tool prompt injection                                        | High       | Unauthorized tool behavior or data exposure | Tool isolation, input/output validation, OWASP-aligned controls |
| Cross-agent coordination failure                                   | High       | Tasks skipped, duplicated, or contradictory | Explicit state machine, typed handoffs, idempotency, tracing    |
| Sensitive employee-data exposure                                   | High       | Privacy/compliance harm                     | Data minimization, RBAC, retention policy, secret isolation     |
| Integration/API failure                                            | Medium     | Delayed onboarding                          | Retry/idempotency, graceful degradation, human escalation       |
| Notification overload                                              | Medium     | Adoption decline                            | Priority rules, digests, role-based notifications               |
| Manager distrust/low adoption                                      | Medium     | Workflow bypass                             | Editable plans, explainability, clear ownership                 |
| Excess agent cost/latency                                          | Medium     | Poor economics/UX                           | Small models where suitable, deterministic operations, caching  |
| Role templates become outdated                                     | Medium     | Declining onboarding quality                | Named content owners, review cadence, versioning                |
| Multi-agent architecture adds no incremental value                 | Medium     | Unnecessary complexity                      | Benchmark against deterministic/single-agent baseline           |
| Low internal hiring volume                                         | Low/Medium | Weak ROI                                    | Validate annual onboarding event volume before scaling          |

---

# Success Metrics

The MRD recommends establishing baseline and target values for:

* **Day-1 readiness rate:** percentage of required approved access/equipment/tasks complete before start.
* **Time-to-productivity:** role-specific time to a defined first meaningful contribution.
* **Manager administrative effort:** hours spent coordinating onboarding per hire.
* **On-time task completion:** percentage of onboarding tasks completed by required milestone.
* **Exception rate:** percentage of workflow tasks requiring manual recovery.
* **New-hire clarity:** survey score covering role expectations, resources, ownership, and where to get help.
* **New-hire satisfaction:** onboarding CSAT or equivalent.
* **30/60/90-day retention:** directional metric, interpreted carefully given small internal samples.
* **Agent accuracy:** percentage of actions/recommendations judged correct against approved policies.
* **Unsafe-action prevention:** 100% of designated privileged actions should require/enforce correct authorization.

No numeric target is assigned because the organization supplied no baseline. Any target before baseline collection would be an assumption.

---

# Actionable Recommendations

## Immediate — next 48 hours

1. Map the actual onboarding workflow from signed offer through Day 30.
2. Identify authoritative systems and integration owners.
3. Collect the last 5–10 onboarding examples per role where available.
4. Interview at least one hiring manager and one recent hire from each role where feasible.
5. Define what "productive" means separately for UI Designer, UX Researcher, Product Manager, Developer, and Engineer.
6. Inventory every access request and identify which actions may be automated versus approval-gated.

## Short-Term — next 30 days

* Establish baseline metrics.
* Build five role onboarding blueprints.
* Identify common versus role-specific tasks.
* Define human/agent responsibility boundaries.
* Create an approved onboarding knowledge corpus.
* Prototype one role end-to-end.
* Compare deterministic workflow, single-agent assistance, and bounded multi-agent orchestration on the same onboarding scenario.
* Conduct security/threat modeling before granting write-capable tools.

## Long-Term — 6–12 months

If the MVP demonstrates value:

* expand from one pilot role to all five roles;
* optimize role-specific knowledge and first-contribution paths;
* introduce controlled adaptive workflows;
* add onboarding analytics and bottleneck detection;
* extend patterns to internal transfers or offboarding only after onboarding reliability is demonstrated;
* continuously evaluate whether additional agents improve outcomes enough to justify their operational complexity.

---

# Sources

1. Gallup, **Employee Experience: Strategies for Improvement** — reports 12% strong agreement that organizations do onboarding well. [Gallup employee experience research](https://www.gallup.com/workplace/323573/employee-experience-and-workplace-culture.aspx)
2. Gallup, **Essential Ingredients for an Effective Onboarding Program**, 2019. [Gallup onboarding research](https://www.gallup.com/workplace/246242/essential-ingredients-effective-onboarding-program.aspx)
3. Gallup, **Why the Onboarding Experience Is Key for Retention**, 2018. [Gallup retention and onboarding analysis](https://www.gallup.com/workplace/235121/why-onboarding-experience-key-retention.aspx)
4. Gallup, **5 Questions Every Onboarding Program Must Answer**, 2019. [Gallup onboarding questions research](https://www.gallup.com/workplace/247598/questions-every-onboarding-program-answer.aspx)
5. SHRM, **Employee Onboarding Guide: Roles & Responsibilities**, updated 2024. [SHRM onboarding responsibilities](https://www.shrm.org/topics-tools/topics/onboarding/roles-responsibilities)
6. SHRM, **Role-Tailored Onboarding**, updated 2024. [SHRM role-tailored onboarding](https://www.shrm.org/topics-tools/topics/onboarding/role-tailored)
7. SHRM, **How to Measure Onboarding Success**, updated 2024. [SHRM onboarding measurement guidance](https://www.shrm.org/topics-tools/topics/onboarding/measuring-success)
8. BambooHR, **44% of New Hires Regret their Decision Within a Week**, 2023. [BambooHR onboarding study](https://www.bamboohr.com/about-bamboohr/press-release/44-of-new-hires-regret-their-decision-within-a-week-bamboohr-study-finds)
9. BambooHR, **State of HR 2024**. [BambooHR State of HR research](https://www.bamboohr.com/resources/guides/state-of-hr-2024)
10. [BambooHR](https://www.bamboohr.com/), **Onboarding product documentation**.
11. [Workday](https://www.workday.com/), **Onboarding Plans / onboarding experience documentation**.
12. [ServiceNow](https://www.servicenow.com/), **Employee Journey Management**, updated 2026.
13. [Rippling](https://www.rippling.com/), **HR Workflow Automation**, onboarding and provisioning capabilities.
14. [Deel](https://www.deel.com/), **Employee onboarding workflows**.
15. [Microsoft](https://www.microsoft.com/), **Microsoft Entra Lifecycle Workflows**, updated 2026.
16. [Okta](https://www.okta.com/), **Lifecycle Management onboarding/offboarding**.
17. [Zapier](https://zapier.com/), **Employee Onboarding Automation**, 2026.
18. Anthropic, **How we built our multi-agent research system**, 2025. [Anthropic multi-agent engineering analysis](https://www.anthropic.com/engineering/multi-agent-research-system)
19. IBM, **What is a Multi-Agent System?** [IBM multi-agent systems overview](https://www.ibm.com/think/topics/multiagent-system)
20. Microsoft Agent Framework, **Multi-Agent Orchestration**, 2025. [Microsoft multi-agent orchestration analysis](https://devblogs.microsoft.com/agent-framework/unlocking-enterprise-ai-complexity-multi-agent-orchestration-with-the-microsoft-agent-framework/)
21. NIST, **Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile**, 2024; updated 2026. [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
22. OWASP GenAI Security Project, **Agentic AI Threats and Mitigations**, 2025. [OWASP agentic AI security guidance](https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/)

---

# Assumptions

**A1.** Hiring occurs frequently enough across the five roles for reusable onboarding automation to create meaningful value.

**A2.** The role-specific needs described for UI Designer, UX Researcher, Product Manager, Developer, and Engineer are representative; they have not yet been validated against this organization's actual job expectations.

**A3.** HR/People Operations, IT/identity, security, learning owners, and onboarding buddies participate in onboarding to some degree.

**A4.** The current workflow follows the typical hire → setup → access → training → role integration sequence. No internal process map was supplied.

**A5.** The organization uses enterprise systems capable of API or automation integration.

**A6.** Internal onboarding volume makes correctness, security, and workflow reliability more important than extreme transaction throughput.

**A7.** Primary operating costs will consist of engineering/integration labor, inference, observability, hosting/state, security, and content maintenance.

**A8.** No claim of patentability or freedom to operate is made.

**A9.** Team size, implementation duration, and budget cannot be estimated responsibly until integration scope and runtime are selected.

**A10.** All financial opportunity/ROI figures are intentionally left formula-based because no internal hiring volume, compensation, administrative-hours baseline, turnover rate, or time-to-productivity baseline was supplied.

**A11.** External onboarding statistics validate the general problem but are not treated as measured outcomes for the AI Engineering organization.

---

# Open Questions

1. How many hires per year occur in each of the five roles?
2. What systems currently constitute the onboarding workflow?
3. What event is the authoritative trigger that a hire is approved for onboarding?
4. What are the existing onboarding completion, Day-1 readiness, and time-to-productivity baselines?
5. How many manager/HR/IT hours are spent per onboarding event?
6. What distinguishes "Developer" from "Engineer" in this organization?
7. Which role-specific tools, repositories, knowledge sources, and training are mandatory?
8. Which actions can agents execute directly, and which require human approval?
9. What employee data may the system retain, and for how long?
10. Which geographic/compliance jurisdictions apply?
11. What identity provider, HRIS, collaboration platform, knowledge repository, source-control platform, design tools, and research tools are in use?
12. What is the target `AAMAD_TARGET_RUNTIME`?
13. What minimum hiring volume or measurable labor reduction would justify production deployment?
14. Should onboarding cover only pre-start through Day 30 for MVP, or extend to 60/90 days?
15. Who owns and approves each role's onboarding blueprint?

---

# Audit

**Timestamp:** 2026-08-09
**Persona ID:** `product-mgr`
**Action:** `create-mrd`
**Artifact:** `project-context/1.define/mrd.md`
**MRD status:** Required by stakeholder/course; not skipped.
**Selected runtime:** Unresolved / not supplied.
**Context boundary:** Internal AI Engineering organization; hiring managers and new hires across UI Designer, UX Researcher, Product Manager, Developer, and Engineer roles.
**Evidence policy:** External figures are cited; organization-specific quantitative values not supplied by the stakeholder are recorded as assumptions or left TBD.
**Architecture handoff status:** Conditional. Resolve the high-impact Open Questions—especially systems inventory, workflow baseline, role definitions, approval boundaries, and target runtime—before final architecture/build decisions.
