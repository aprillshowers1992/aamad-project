# Wall of Fame summary

**Title:** Catalog-Gated 30/60/90 Onboarding Crew

External / Wall of Fame copy only. Formal product description remains in `project-context/1.define/prd.md` and `sad.md`.

Catalog-Gated 30/60/90 Onboarding Crew is an internal AI Engineering MVP that generates consistent onboarding plans without letting a model invent the work. Hiring managers still reconstruct role-specific 30/60/90 plans by hand, which drops required compliance or provisioning tasks, sequences work badly, or—if a generic LLM is used—adds requirements that do not exist in an approved source. A sequential CrewAI crew (Role Analyst → Plan Builder → Compliance Checker → Document Writer) takes role, department, and start_date and may only select and bucket stable catalog task_ids; the Checker is independent of the Builder and may send a plan back at most twice. Construction and validation are separated: PASS/FAIL is a deterministic application check, not an LLM judgment call, and a terminal REJECT writes no approved files. On PASS, the CLI (onboard) and a thin web UI emit onboarding-plan.md and manager-checklist.md with an audit appendix listing task order, ID, title, and category for traceability. Runnable scope is Developer only; UI Designer, UX Researcher, Product Manager, and Engineer remain catalog placeholders and future work. Live HRIS execution, reminders, and task tracking are out of scope.

**Tech tags:** Python 3.11+ · CrewAI · OpenAI GPT-4o (Gemini fallback) · FastAPI · Pydantic v2 · Click · React 19 · TypeScript · Vite · YAML-based task catalog · Deterministic compliance gate
