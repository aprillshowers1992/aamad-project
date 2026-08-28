# Backend Functional Spec — Onboarding Plan HTTP API

**Persona:** `backend-eng`
**Action:** `develop-be` (thin HTTP wrapper around the existing onboarding package)
**Phase:** Build
**Intended path:** `project-context/1.define/onboarding-backend-spec.md`
**Product surface:** Automated Employee Onboarding Workflow
**Implementation:** `src/onboarding/api.py` wrapping `run_onboarding` (not a second crew)
**Status:** Implemented — update the Spec Sync checklist after every commit that changes endpoints, run-store behavior, or this spec

---

## Purpose and Scope

- **Feature ID:** ONB-BE-001
- **Purpose:** Let a browser frontend start the existing four-agent onboarding workflow over HTTP, without blocking on crew completion, and poll until Markdown is ready or compliance fails.
- **In Scope:** `POST /runs`; `GET /runs/{runId}`; request validation matching CLI `onboard`; background call to existing `run_onboarding`; in-memory run store; returning `onboarding-plan.md` and `manager-checklist.md` text on success.
- **Out of Scope:** Duplicating Role Analyst / Plan Builder / Compliance Checker / Document Writer logic; a database; authentication; pause / cancel / retry-diff routes; the Critical Research Workflow API (`backend-functional-spec.md`); rewriting the Vite research prototype (`src/frontend/`).

This document is the HTTP contract for the onboarding API. A frontend MUST be built against these shapes, not against the research-run types in `src/frontend/src/types.ts`.

---

## Traceability

- **Operator request (2026-08-27):** FastAPI module `src/onboarding/api.py`; wrap existing Steps 1–7 logic; stub Role Analyst / Plan Builder unless `OPENAI_API_KEY` is set (OQ-13); in-memory store; spec in the same pattern as `backend-functional-spec.md`.
- **CLI / core:** `src/onboarding/cli.py`, `src/onboarding/workflow.py`, `src/onboarding/models.py` (`OnboardingInput`), `src/onboarding/rendering.py`.
- **PRD / SAD:** `project-context/1.define/prd.md`, `project-context/1.define/sad.md` — MVP remains CLI `onboard` (SD-6); this API is a thin wrap for a future UI (SD-10) and MUST NOT replace the CLI.
- **Research prototype (do not confuse):** `project-context/1.define/backend-functional-spec.md` and `src/frontend/` are a separate Critical Research Workflow spike (`question` / `domain` / `scope`). This onboarding API does not implement that contract.
- **Config:** `aamad.config.yml` — `runtime.target: crewai`, `language.primary: python`, `security.forbid_committed_secrets: true`.

---

## Security boundary (invariant)

```text
Browser
  MUST NOT import CrewAI
  MUST NOT read OPENAI_API_KEY
  MAY call POST /runs and GET /runs/{runId} over HTTP

Server (src/onboarding/api.py)
  MAY call run_onboarding
  MAY read OPENAI_API_KEY from the process environment
  MUST use catalog stubs when OPENAI_API_KEY is unset (OQ-13)
  MUST redact secret values from error messages
```

- Secret **names** only in `.env.example`. Never commit values.
- Missing `OPENAI_API_KEY` is **not** a 503. The server runs the existing stub Role Analyst / Plan Builder (`onboarding.stubs`) so local demo and CI work without a key.
- When `OPENAI_API_KEY` is set, `run_onboarding` uses the live CrewAI Role Analyst and Plan Builder. Compliance Checker and Document Writer stay deterministic Python.

---

## Inputs

The backend accepts onboarding data **only** on `POST /runs`. `GET /runs/{runId}` has no body.

### `POST /runs` body — `OnboardingInput`

Must match `OnboardingInput` in `src/onboarding/models.py` and CLI flags `--role`, `--department`, `--start-date`:

```text
OnboardingInput
- role: string
- department: string
- start_date: string   // YYYY-MM-DD
```

| Input name | Type / format | Required | Source | Validation (same as CLI) |
| ---------- | ------------- | -------- | ------ | ------------------------ |
| `role` | Canonical role string | Yes | JSON body | One of: `UI Designer`, `UX Researcher`, `Product Manager`, `Developer`, `Engineer`. Unknown values rejected. Only `Developer` is executable in MVP; other canonical roles return “not yet supported”. |
| `department` | string | Yes | JSON body | Trim; non-empty (metadata only). |
| `start_date` | calendar date | Yes | JSON body | Valid `YYYY-MM-DD` (impossible dates rejected). |

Unknown JSON keys are rejected (`extra="forbid"`), matching `OnboardingInput`. Missing `Content-Type: application/json` or a non-object body is `400`.

Store the validated `OnboardingInput`. Do not invent tasks or catalogs in the API layer.

### `GET /runs/{runId}` path

| Input name | Type / format | Required | Validation |
| ---------- | ------------- | -------- | ---------- |
| `runId` | string | Yes | Non-empty path segment; unknown id → `404` |

---

## Endpoints

Base URL is local (`http://127.0.0.1:8000` until setup.md records otherwise). Paths are **not** prefixed with `/api`. CORS MUST allow the onboarding UI origin `http://localhost:5174` (and `http://127.0.0.1:5174`). `http://localhost:5173` remains allowed so the unrelated Critical Research Workflow app is not blocked if both UIs are running.

| Method | Path | Success HTTP | Success body (minimum) |
| ------ | ---- | ------------ | ---------------------- |
| `POST` | `/runs` | `202 Accepted` | `{ runId, status: "running", submittedAt }` |
| `GET` | `/runs/{runId}` | `200 OK` | Discriminated union on `status` (below) |

`POST` MUST return before `run_onboarding` completes. Blocking the response until Markdown is written violates this spec.

Run the API with:

```text
uvicorn onboarding.api:app --host 127.0.0.1 --port 8000
```

### `POST /runs` — start

1. Validate body the same way the CLI validates `--role`, `--department`, `--start-date`. On failure, **do not** allocate a `runId` and **do not** start the workflow.
2. Reject non-Developer canonical roles with the CLI “not yet supported” message. Do not start the workflow.
3. Allocate a unique `runId` (`run-` plus a UUID; never `run-mock-`).
4. Write the run to the in-memory store as `status: "running"` with `submittedAt` (ISO-8601).
5. Start `run_onboarding` on a background thread. The request thread MUST NOT await it.
6. Return `202` immediately.

**Success payload:**

```text
{
  runId: string,
  status: "running",          // literal
  submittedAt: string         // ISO-8601
}
```

The operator short form `{ runId, status: "running" }` is the semantic contract. `submittedAt` is included so a UI can stamp the request.

**Background call (existing logic only):**

```text
run_onboarding(
  payload,
  output_dir=Path("output") / runId,
  role_analyst=...,   // stubs unless OPENAI_API_KEY is set
  plan_builder=...,
)
```

Document Writer still writes `onboarding-plan.md` and `manager-checklist.md` (filenames unchanged). Per-run subdirectory `./output/{runId}/` avoids concurrent POSTs overwriting each other. The API then **reads those files** and stores their text on the run record.

### `GET /runs/{runId}` — poll

Pure read of the in-memory store. MUST NOT start or cancel a workflow.

**Success payloads** (HTTP 200 when the `runId` exists):

```text
# still working
{
  runId: string,
  status: "running"
}

# compliance PASS — file bodies from ./output/{runId}/
{
  runId: string,
  status: "done",
  result: {
    role: string,
    department: string,
    startDate: string,             // YYYY-MM-DD; echo of POST
    onboardingPlan: string,        // full Markdown of onboarding-plan.md
    managerChecklist: string,      // full Markdown of manager-checklist.md
    completedAt: string            // ISO-8601
  }
}

# compliance FAIL after accept, or writer/runtime exception
{
  runId: string,
  status: "error",
  violations: string[],            // check_compliance messages; may be []
  message: string                  // same family as CLI "No approved output..."
}
```

`status` is the discriminator. Clients MUST NOT assume `result` exists unless `status === "done"`. Clients MUST NOT assume `violations` unless `status === "error"`.

Unknown `runId`: HTTP `404` with `{ "status": "error", "message": "Run not found." }`.

A UI MUST poll `GET /runs/{runId}` while `status === "running"`, then show the two Markdown documents or the failure reason.

---

## Processing behavior

### Run state machine (server)

```text
(none) -- POST valid --> running -- compliance PASS + files --> done
                           |
                           +-- compliance FAIL or exception --> error
```

There is no server `idle`. Retry is a **new** `POST /runs` (new `runId`). The backend does not reuse an errored run.

### Background workflow

After POST returns, the worker:

1. Loads the stored `OnboardingInput`.
2. Calls existing `run_onboarding` (Role Analyst → Plan Builder → `check_compliance` retry loop → Document Writer on PASS).
3. On PASS: read `output/{runId}/onboarding-plan.md` and `output/{runId}/manager-checklist.md`; set `status: "done"`; set `completedAt`.
4. On FAIL: set `status: "error"` with `violations` and `message` from `WorkflowResult`. No approved Markdown.
5. On exception: set `status: "error"` with a short `message` (no stack traces, no API keys).

Concurrent POSTs each get their own `runId` and output subdirectory. The store MUST be safe for the request thread and the worker thread.

### Polling

`GET` may be called many times. While `running`, every GET returns the running envelope. After `done` or `error`, later GETs return the same terminal payload. Process restart clears the store; subsequent GET is 404.

---

## Agents (not reimplemented here)

The API does not declare a new crew. It invokes the existing package:

| Agent | Implementation | When |
| ----- | -------------- | ---- |
| Role Analyst | `onboarding.stubs.StubRoleAnalyst` selecting real Developer catalog IDs | Default (no `OPENAI_API_KEY`) |
| Plan Builder | `onboarding.stubs.StubPlanBuilder` with a passing 30/60/90 split | Default (no `OPENAI_API_KEY`) |
| Role Analyst / Plan Builder | `onboarding.crew_runtime.build_llm_agents` | Only if `OPENAI_API_KEY` is set |
| Compliance Checker | Existing `check_compliance` (deterministic) | Always |
| Document Writer | Existing `MarkdownDocumentWriter` | Only on PASS |

---

## In-memory run store

No database.

```text
RunRecord
- runId: string
- status: "running" | "done" | "error"
- input: OnboardingInput
- submittedAt: string
- onboardingPlan: string | null     // set iff status === "done"
- managerChecklist: string | null   // set iff status === "done"
- violations: string[]              // set iff status === "error"
- message: string | null            // set iff status === "error"
- completedAt: string | null
```

| Rule | Detail |
| ---- | ------ |
| Lifetime | Process memory only; lost on restart |
| Workers | Single-process server; do not assume a shared store across multiple OS processes |
| Lookup | Exact `runId` |
| History | Not implemented on the server; a UI may keep session history |

---

## Validations and constraints

- Re-validate `OnboardingInput` on the server even if a UI already validated.
- Do not block `POST` on workflow completion.
- Do not persist secrets in `RunRecord`.
- Do not invent catalog tasks in the API layer.
- Task IDs in Markdown remain appendix-only (existing Document Writer / SD-4). The API returns file text as-is.
- Background `run_onboarding` is bounded by a 5-minute timeout (`asyncio.wait_for`). Timeout and unexpected exceptions become GET `status: "error"` with a generic `message` (no stack traces).

---

## Error handling

| Condition | HTTP | Body |
| --------- | ---- | ---- |
| Invalid JSON / failed `OnboardingInput` / unknown role / unsupported catalog role | `400` | `{ "status": "error", "message": "<validation or CLI-style text>" }` |
| Unknown `runId` | `404` | `{ "status": "error", "message": "Run not found." }` |
| Run accepted, workflow still working | `200` | `{ "runId", "status": "running" }` |
| Run accepted, compliance PASS | `200` | `{ "runId", "status": "done", "result": { ... } }` |
| Run accepted, compliance FAIL or worker exception | `200` | `{ "runId", "status": "error", "violations", "message" }` |

Crew/compliance failures after accept are **business** errors on GET (`200` + `status: "error"`), not `500`.

---

## Acceptance criteria

1. `POST /runs` with valid Developer JSON returns `202` and `{ runId, status: "running", submittedAt }` without waiting for Markdown.
2. Immediate `GET /runs/{runId}` MAY return `status: "running"`.
3. After a successful stub (or live) workflow, `GET` returns `status: "done"` and `result.onboardingPlan` / `result.managerChecklist` equal to the CLI files for the same input.
4. `result.role`, `result.department`, and `result.startDate` echo the POST body.
5. If compliance fails, GET returns `status: "error"` and `violations`.
6. Invalid POST bodies never create store entries and never start the workflow.
7. Unset `OPENAI_API_KEY` still completes a Developer happy path via stubs.
8. Restarting the server forgets runs (in-memory). GET of an old id is 404.

---

## Spec Sync checklist

Update this table after **each commit** that changes endpoint paths, request/response JSON, the run store, stub/LLM selection, or this spec.

| Item | Status | Note |
| ---- | ------ | ---- |
| Spec sections Inputs, Endpoints, Store | Done | Contract in this file; implemented in `src/onboarding/api.py`. |
| `POST /runs` async accept | Done | `202` + `{ runId, status: "running", submittedAt }`; background thread. |
| `GET /runs/{runId}` union | Done | `running` \| `done` + Markdown texts \| `error` + `violations`; 404 if unknown. |
| CLI validation parity | Done | Role enum, department, `YYYY-MM-DD`; non-Developer canonical roles unsupported. |
| In-memory run store | Done | Process-local dict + lock; no DB; lost on restart. |
| Wrap existing `run_onboarding` | Done | No second crew; Document Writer still owns Markdown. |
| Stubs unless `OPENAI_API_KEY` | Done | `onboarding.stubs`; OQ-13. |
| CORS for Vite `:5174` | Done | Onboarding UI origin; `:5173` still allowed for the research prototype. |
| TestClient POST → poll → CLI match | Done | `tests/test_api.py`. |

### Per-commit ritual

- [ ] Re-read **Inputs** and **Endpoints** against the running API
- [ ] Confirm `POST /runs` still returns `running` without waiting for `run_onboarding`
- [ ] Confirm `GET /runs/{runId}` still returns only the three `status` shapes (plus 404)
- [ ] Confirm `done` still returns both Markdown bodies and does not invent tasks
- [ ] Confirm the store is still in-memory
- [ ] Confirm stubs still run when `OPENAI_API_KEY` is unset
- [ ] Set the matching row above to `Done` / `Partial` / `Open`

---

## Sources

1. Operator request, 2026-08-27 — FastAPI wrap of existing onboarding package; `POST /runs` / `GET /runs/{runId}`; stubs unless `OPENAI_API_KEY`; TestClient vs CLI; this spec filename.
2. `src/onboarding/cli.py`, `workflow.py`, `models.py`, `rendering.py`, `stubs.py`.
3. `project-context/1.define/backend-functional-spec.md` — endpoint/store/spec-sync pattern (research spike; different product).
4. `project-context/1.define/prd.md` and `sad.md` — CLI MVP, SD-3 output dir, SD-4 appendix IDs, SD-6 `onboard`, SD-10 UI wraps CLI later.
5. `tests/test_e2e.py` / OQ-13 — stub Role Analyst and Plan Builder without a live LLM.

---

## Assumptions

- **A-ONB-BE-1:** This API is a wrap of the CLI core for a future onboarding UI (SD-10). It does not replace `onboard`.
- **A-ONB-BE-2:** FastAPI is the HTTP framework. Paths and JSON in this spec are authoritative.
- **A-ONB-BE-3:** Local listen address is `http://127.0.0.1:8000`. Onboarding UI origin is `http://localhost:5174`. `http://localhost:5173` is the unrelated research prototype.
- **A-ONB-BE-4:** `POST` uses `202 Accepted` because the workflow is asynchronous.
- **A-ONB-BE-5:** GET uses HTTP 200 for known runs in `running`, `done`, and `error` so pollers branch on `status`.
- **A-ONB-BE-6:** Per-run output lives at `./output/{runId}/` so concurrent runs do not clobber files. The JSON still carries the file text.
- **A-ONB-BE-7:** Single-process in-memory dict is enough for local demo; multiple uvicorn workers would not share state.

---

## Open Questions

1. **Resolved (2026-08-28):** The onboarding UI lives at `src/onboarding-ui/` and consumes this API only. The Critical Research Workflow prototype remains at `src/frontend/` and is not replaced.
2. Should `POST /runs` stay at `202`, or use `200` to match naive `fetch` helpers?
3. What poll interval and max wait should the onboarding UI use?
4. Should a later revision add `--output-dir` / `ONBOARDING_OUTPUT_DIR` to the API the same way SAD SD-3 describes for the CLI?

---

## Audit

**Timestamp:** 2026-08-27
**Persona ID:** `backend-eng`
**Action:** `develop-be` (HTTP wrap; no duplicated crew logic)
**Artifact:** `project-context/1.define/onboarding-backend-spec.md`
**Implementation:** `src/onboarding/api.py`
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`)
**Prompt Trace:** Omitted — no live crew kickoff required; stubs used unless `OPENAI_API_KEY` is set (OQ-13)

---

## Audit (sync-docs 2026-08-28)

**Timestamp:** 2026-08-28
**Persona ID:** `project-mgr` (operator requested documentation sync)
**Action:** `sync-docs`
**What changed:** Research-prototype paths `frontend/` → `src/frontend/`. Open Question 1 resolved: onboarding UI is `src/onboarding-ui/`, not a replacement of the CRW prototype.
