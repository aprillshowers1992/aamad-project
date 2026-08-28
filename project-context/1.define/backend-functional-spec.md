# Backend Functional Spec — Critical Research Workflow

**Persona:** `backend-eng`
**Action:** `develop-be` (operator-requested API prototype)
**Phase:** Build (prototype; not the CLI onboarding MVP)
**Intended path:** `project-context/1.define/backend-functional-spec.md`
**Product surface:** Critical Research Workflow
**Implementation target:** Python HTTP API + CrewAI (to be scaffolded under a backend package; not the onboarding CLI)
**Status:** Spec only — update the Spec Sync checklist after every commit that changes endpoints, crew config, run-store behavior, or this spec

---

## Purpose and Scope

- **Feature ID:** CRW-BE-001
- **Purpose:** Accept a researcher’s `ResearchInput`, start a CrewAI crew **without blocking the HTTP response**, and expose pollable run status until the crew finishes as `done` (with a `ResearchResult`) or `error` (with a message).
- **In Scope:** `POST /runs`; `GET /runs/:runId`; request validation matching the frontend Inputs rules; one hardcoded CrewAI crew (one agent, one task); in-memory run store; server-side LLM credentials; mapping crew output into `ResearchResult`.
- **Out of Scope:** Database or durable persistence; authentication; pause / cancel / retry-diff routes; multi-agent crews; the Automated Employee Onboarding Workflow CLI (`onboard`); frontend UI changes (owned by `frontend-funcional-spec.md` and `@integration.eng`); calling CrewAI or reading `OPENAI_API_KEY` from the browser.

This document is the HTTP and runtime contract for the Critical Research Workflow backend. It must stay aligned with `src/frontend/src/types.ts` and this Spec Sync checklist.

---

## Traceability

- **Operator request (2026-08-23):** Create this spec for two endpoints matching the existing frontend contract; CrewAI and API keys server-side only; start with one hardcoded crew and an in-memory store; include a Spec Sync checklist in the same format as the frontend spec.
- **Frontend contract:** `project-context/1.define/frontend-funcional-spec.md`; types in `src/frontend/src/types.ts`; stub sequence in `src/frontend/src/services/runService.ts` and `src/frontend/README.md` (“Where CrewAI connects next”).
- **PRD:** `project-context/1.define/prd.md` — current product MVP is CLI `onboard`; web UI and this research API are not FR-001–FR-016. This prototype does **not** implement the onboarding workflow.
- **SAD:** `project-context/1.define/sad.md` — onboarding MVP has no web API for research runs (SA-9). CrewAI adapter conventions (YAML agents/tasks, sequential process, `OPENAI_API_KEY`) still apply to **this** prototype’s crew.
- **Config:** `aamad.config.yml` — `runtime.target: crewai`, `language.primary: python`, `security.forbid_committed_secrets: true`.
- **User stories:** none present.

---

## Security boundary (invariant)

```text
Browser (src/frontend/)
  MUST NOT import CrewAI
  MUST NOT read OPENAI_API_KEY or any LLM secret
  MAY call POST /runs and GET /runs/:runId over HTTP

Server (this backend)
  MAY import CrewAI
  MAY read OPENAI_API_KEY from the process environment
  MUST redact secrets from logs, Prompt Trace, and error messages
```

- Secrets live in environment variables only (`.env` uncommitted; names listed in `.env.example`).
- A missing `OPENAI_API_KEY` is a **server** preflight failure. Do not start a run that cannot call the LLM.
- CrewAI `kickoff` runs only on the server, after `POST /runs` has allocated a `runId` and returned `status: "running"`.

---

## Inputs

The backend accepts research data **only** on `POST /runs`. `GET /runs/:runId` has no body. Reset remains a frontend FSM action (no backend call).

### `POST /runs` body — `ResearchInput`

Must match `ResearchInput` in `src/frontend/src/types.ts`:

```text
ResearchInput
- question: string
- domain: "general" | "product" | "technical" | "operations"
- scope: string
```

| Input name | Type / format | Required | Source | Validation (same as frontend Inputs) |
| ---------- | ------------- | -------- | ------ | ------------------------------------ |
| `question` | string | Yes | JSON body | Trim; non-empty; minimum 8 characters after trim |
| `domain` | enum: `general` \| `product` \| `technical` \| `operations` | Yes | JSON body | Must be one of the four values |
| `scope` | string | No | JSON body | Trim; empty string allowed; max 500 characters after trim |

Unknown JSON keys are ignored. Missing `Content-Type: application/json` or a non-object body is a 400.

Store the **trimmed** values. `scope` is passed into the crew task as context. It is **not** a field on `ResearchResult` (same omission as the frontend type).

### `GET /runs/:runId` path

| Input name | Type / format | Required | Validation |
| ---------- | ------------- | -------- | ---------- |
| `runId` | string | Yes | Non-empty path segment; must match a previously allocated id or the handler returns 404 |

---

## Endpoints

Base URL is local (assumed `http://127.0.0.1:8000` until setup.md records otherwise). Paths are **not** prefixed with `/api`. CORS MUST allow the Vite origin `http://localhost:5173` for local integration.

| Method | Path | Success HTTP | Success body (minimum) |
| ------ | ---- | ------------ | ---------------------- |
| `POST` | `/runs` | `202 Accepted` | `{ runId, status: "running", submittedAt }` |
| `GET` | `/runs/:runId` | `200 OK` | Discriminated union on `status` (below) |

`POST` MUST return before `crew.kickoff()` completes. Blocking the response until the crew finishes violates this spec.

### `POST /runs` — start (maps to frontend `startRun`)

**Client sequence this endpoint enables:**

1. Validate body. On failure, **do not** allocate a `runId` and **do not** start a crew.
2. Preflight: `OPENAI_API_KEY` is present in the server environment. On failure, **do not** allocate a `runId`.
3. Allocate a unique `runId` (prefix `run-` plus a UUID; never `run-mock-`, which is reserved for the frontend stub).
4. Write the run to the in-memory store as `status: "running"` with trimmed input and `submittedAt` (ISO-8601).
5. Schedule crew execution on a background worker (thread or equivalent). The request thread MUST NOT await kickoff.
6. Return `202` immediately.

**Success payload** — must satisfy frontend `StartRunResponse` in `src/frontend/src/types.ts`:

```text
StartRunResponse
- runId: string
- status: "running"          // literal
- submittedAt: string        // ISO-8601; required by the frontend type
```

The operator short form `{ runId, status: "running" }` is the semantic contract. `submittedAt` is required so the existing frontend type does not break when stubs are swapped for HTTP.

### `GET /runs/:runId` — poll (maps to frontend `getRunStatus`)

This handler is a **pure read** of the in-memory store. It MUST NOT start, resume, or cancel a crew.

**Success payloads** (HTTP 200 when the `runId` exists):

```text
# still working
{
  runId: string,
  status: "running"
}

# finished — result MUST match ResearchResult in src/frontend/src/types.ts exactly
{
  runId: string,
  status: "done",
  result: ResearchResult
}

# crew or mapping failed after the run was accepted
{
  runId: string,
  status: "error",
  message: string
}
```

`status` is the discriminator. Clients MUST NOT assume `result` exists unless `status === "done"`. Clients MUST NOT assume `message` exists unless `status === "error"`.

Unknown `runId`: HTTP `404` with `{ "status": "error", "message": "Run not found." }` (no `runId` required).

Today the Vite app calls `getRunStatus` **once** and the stub always returns `done`. A real crew takes longer than one round-trip. `@integration.eng` MUST add a poll loop that repeats `GET /runs/:runId` while `status === "running"`, then `COMPLETE` or `FAIL`. This backend spec does not change the frontend.

---

## `ResearchResult` (done payload)

**Source of truth:** `ResearchResult` in `src/frontend/src/types.ts`. `GET /runs/:runId` with `status: "done"` MUST return `result` with **exactly** these fields and types. Do not add `scope`. Do not rename keys.

```text
ResearchResult
- runId: string
- question: string
- domain: "general" | "product" | "technical" | "operations"
- summary: string
- findings: string[]
- sources: { title: string, url: string }[]
- completedAt: string          // ISO-8601
```

| Field | Produced by | Rule |
| ----- | ----------- | ---- |
| `runId` | Store | Same id as the path and the POST response |
| `question` | Store (echo of trimmed POST body) | Not invented by the LLM |
| `domain` | Store (echo of POST body) | Must remain one of the four enum values |
| `summary` | Crew output, mapped on the server | Non-empty string after trim |
| `findings` | Crew output, mapped on the server | Array of strings; empty array allowed only if mapping explicitly produces `[]` — prefer at least one finding |
| `sources` | Crew output, mapped on the server | Each item has `title` and `url` strings; `url` may be a non-http note string (frontend already renders `<a href={url}>`) |
| `completedAt` | Store clock when status becomes `done` | ISO-8601; set once; do not change on later GETs |

If crew output cannot be mapped into this shape, the run becomes `status: "error"` with a message. Never return `status: "done"` with a partial or extra-field `result`.

`src/frontend/src/types.ts` currently types `RunStatusResponse` as **done-only** (the stub). The backend union above is the live contract. Widening the client type is integration work, not a reason to omit `running` / `error` on GET.

---

## Processing behavior

### Run state machine (server)

```text
(none) -- POST valid --> running -- crew mapped --> done
                           |
                           +-- crew/map fail --> error
```

There is no server `idle`. `idle` / `Reset` / `Retry` are frontend FSM events (`frontend-funcional-spec.md`). Retry is a new `POST /runs` with the same body (new `runId`). The backend does not reuse an errored run.

Illegal: transitioning `done` → `running` for the same `runId`; exposing pause or cancel.

### Background crew step

After POST returns:

1. Load the stored `ResearchInput` for `runId`.
2. Render the single task with `question`, `domain`, and `scope`.
3. Call `crew.kickoff()` (or the CrewAI equivalent) on the server process.
4. On success: map output → `ResearchResult`; set store `status: "done"`; set `completedAt`; persist `result`.
5. On exception, timeout, or mapping/schema failure: set store `status: "error"` and a short `message` (no stack traces, no API keys).

Concurrent POSTs each get their own `runId`. The store MUST be safe for concurrent read/write from the request thread and the worker thread.

### Polling

`GET` may be called many times for the same `runId`. While `running`, every GET returns the running envelope. After `done` or `error`, later GETs return the same terminal payload (idempotent). Process restart clears the store; subsequent GET is 404.

---

## Hardcoded crew (v1)

Prove the **async run → poll → done** loop before adding agents.

| Piece | v1 value |
| ----- | -------- |
| Crew count | One crew |
| Agents | One |
| Tasks | One |
| Process | Sequential (`allow_delegation: false`) |
| Memory | `false` |
| `max_iter` | ≤ 12 |
| LLM | OpenAI via `OPENAI_API_KEY` (model recorded in implementation Audit; SAD onboarding default is `gpt-4o` — this prototype may use the same unless setup.md records otherwise) |
| Config files | `config/agents.yaml`, `config/tasks.yaml` plus a Python entry that builds the crew (CrewAI adapter) |

**Agent (logical id `critical_researcher`):** a single analyst whose job is to answer the submitted research question within `domain` and optional `scope`. No tools in v1 (no web search, no file writes) unless a later spec adds them.

**Task (logical id `answer_research_question`):** produce structured output that the server can map to `summary`, `findings`, and `sources`. `expected_output` MUST describe that JSON object (not a free-form essay only). `runId`, `question`, `domain`, and `completedAt` are filled by the server, not trusted from the LLM.

Do not implement the four-agent onboarding crew here. Do not add a manager/delegation topology in v1.

---

## In-memory run store

No database in this spec.

```text
RunRecord
- runId: string
- status: "running" | "done" | "error"
- input: ResearchInput          // trimmed
- submittedAt: string           // ISO-8601
- result: ResearchResult | null // set iff status === "done"
- message: string | null        // set iff status === "error"
```

| Rule | Detail |
| ---- | ------ |
| Lifetime | Process memory only; lost on restart |
| Workers | Single-process server; do not assume a shared store across multiple OS processes |
| Lookup | Exact `runId` |
| History | The backend does **not** implement History; the frontend keeps session history |

---

## Validations and constraints

- Re-validate `ResearchInput` on the server even if the UI already validated (never trust the client).
- `POST` payload size: reject bodies that are not a JSON object or that exceed a modest limit (implementation MAY use 64 KiB; record the chosen limit in backend.md).
- Do not block `POST` on crew completion. Do not call `kickoff` inside the request handler’s awaited path.
- Do not persist secrets in `RunRecord`.
- Timing: no SLA in v1. The UI must poll until `done` or `error`. A server-side kickoff timeout SHOULD eventually move the record to `error` (exact duration recorded at implementation; suggest 120 seconds unless setup.md overrides).

---

## Error handling

| Condition | HTTP | Body |
| --------- | ---- | ---- |
| Invalid JSON / failed `ResearchInput` validation | `400` | `{ "status": "error", "message": "<validation text>" }` |
| Missing `OPENAI_API_KEY` (preflight) | `503` | `{ "status": "error", "message": "Server is not configured for crew execution." }` |
| Unknown `runId` | `404` | `{ "status": "error", "message": "Run not found." }` |
| Run accepted, crew still working | `200` | `{ "runId", "status": "running" }` |
| Run accepted, mapping succeeded | `200` | `{ "runId", "status": "done", "result": ResearchResult }` |
| Run accepted, crew or mapping failed | `200` | `{ "runId", "status": "error", "message": "<safe text>" }` |
| Unexpected handler crash | `500` | `{ "status": "error", "message": "Internal error." }` |

Crew failures after accept are **business** errors on GET (`200` + `status: "error"`), not `500`, so a poll loop can `FAIL` the frontend FSM without treating the HTTP call as a transport failure.

Retry: the client POSTs again. The server does not restart an existing `runId`.

---

## Acceptance criteria

1. `POST /runs` with a valid `ResearchInput` returns `202` and `{ runId, status: "running", submittedAt }` in well under typical crew runtime (the response does not wait for kickoff to finish).
2. Immediate `GET /runs/:runId` may return `status: "running"`.
3. After the crew finishes successfully, `GET /runs/:runId` returns `status: "done"` and `result` matching `ResearchResult` in `src/frontend/src/types.ts` (`runId`, `question`, `domain`, `summary`, `findings`, `sources`, `completedAt`; no `scope`).
4. `result.question` and `result.domain` echo the trimmed POST body; `result.runId` equals the path id.
5. If kickoff or mapping fails, GET returns `status: "error"` and a `message` (HTTP 200 for a known run).
6. Invalid POST bodies never create store entries and never start a crew.
7. The frontend package does not import CrewAI and does not contain API keys.
8. Restarting the server forgets runs (in-memory). GET of an old id is 404.
9. v1 crew config declares one agent and one task.

QA mapping: unit tests for validation + store transitions; one integration test for POST → poll GET until `done` or `error` (may use a test double for the LLM if CI has no key; record that gap if the live crew is not exercised in CI).

---

## Spec Sync checklist

Update this table after **each commit** that changes endpoint paths, request/response JSON, crew YAML, the run store, secret handling, or this spec. Status is `Done` when the running backend matches the spec, `Partial` if only some of the item is true, or `Open` if not built.

| Item | Status | Note |
| ---- | ------ | ---- |
| Spec sections Inputs, Endpoints, Crew, Store | Done | Contract lives in this file; implementation not started. |
| `POST /runs` async accept | Open | Must return `{ runId, status: "running", submittedAt }` with `202` without awaiting kickoff. |
| `GET /runs/:runId` union | Open | `running` \| `done` + `ResearchResult` \| `error` + `message`; 404 if unknown. |
| `ResearchResult` exact shape | Open | Fields match `src/frontend/src/types.ts`; `scope` omitted; question/domain echoed from store. |
| In-memory run store | Open | Process-local `RunRecord`; no DB; lost on restart. |
| Hardcoded one-agent one-task crew | Open | YAML + sequential process; no onboarding four-agent crew. |
| Server-only CrewAI and secrets | Open | `OPENAI_API_KEY` env on server; frontend never imports CrewAI or holds keys. |
| Validation parity with Inputs | Open | Trimmed question min 8; domain enum; scope max 500. |
| No pause, cancel, or retry-diff routes | Open | Retry is a new POST; Reset is frontend-only. |
| CORS for Vite `:5173` | Open | Required before browser integration. |
| Frontend poll loop | Open | Owned by `@integration.eng`; backend GET is poll-safe. Current UI still one-shot stubs. |
| Local run docs (backend README / `.env.example`) | Open | Document `OPENAI_API_KEY` name only; no secret values. |

### Per-commit ritual

- [ ] Re-read **Inputs**, **Endpoints**, **ResearchResult**, and **Hardcoded crew** against the running API
- [ ] Confirm `POST /runs` still returns `running` without waiting for `crew.kickoff()`
- [ ] Confirm `GET /runs/:runId` still returns only the three `status` shapes (plus 404)
- [ ] Confirm `result` on `done` still matches `ResearchResult` in `src/frontend/src/types.ts` (no extra keys, no `scope`)
- [ ] Confirm the store is still in-memory and the crew is still one agent / one task until a later spec says otherwise
- [ ] Confirm CrewAI and `OPENAI_API_KEY` remain server-side only
- [ ] Confirm there are still no pause, cancel, or retry-diff routes
- [ ] Set the matching row above to `Done` / `Partial` / `Open` and refresh its one-line note
- [ ] Leave items `Open` if the commit did not finish them

---

## Sources

1. Operator request, 2026-08-23 — `backend-functional-spec.md`; `POST /runs` and `GET /runs/:runId`; async CrewAI kickoff; in-memory store; one-agent one-task crew; Spec Sync checklist format; server-only credentials.
2. `src/frontend/src/types.ts` — `ResearchInput`, `ResearchResult`, `StartRunResponse`; `ResearchResult` is the exact `done` result shape.
3. `project-context/1.define/frontend-funcional-spec.md` — Spec Sync Item / Status / Note table and ritual; Inputs validation; FSM `idle → running → done | error`.
4. `src/frontend/src/services/runService.ts` and `src/frontend/README.md` — current stub `startRun` / `getRunStatus` and the intended HTTP swap.
5. `project-context/1.define/prd.md` — MVP remains CLI; this API is not onboarding FR scope.
6. `project-context/1.define/sad.md` — CrewAI / `OPENAI_API_KEY` conventions; no research-run web API in onboarding MVP.
7. `aamad.config.yml` — `runtime.target: crewai`, Python, `forbid_committed_secrets`.
8. `.cursor/rules/adapter-crewai.mdc` — YAML agents/tasks, sequential process, `max_iter`, memory default, least-privilege tools.
9. `.cursor/templates/sfs-template.md` — heading taxonomy (adapted; filename requested as `backend-functional-spec.md`).

---

## Assumptions

- **A-CRW-BE-1:** “Critical Research Workflow” is an operator-requested prototype name, not a named PRD epic. This API does not change onboarding CLI scope in the PRD/SAD.
- **A-CRW-BE-2:** HTTP framework is Python (FastAPI assumed at implementation unless setup.md records otherwise). This spec locks paths and JSON, not a framework brand.
- **A-CRW-BE-3:** Local listen address is `http://127.0.0.1:8000` until recorded otherwise. Frontend origin for CORS is `http://localhost:5173`.
- **A-CRW-BE-4:** `POST` uses `202 Accepted` because the crew is asynchronous. Integration must treat 2xx + `status: "running"` as success (not only 200).
- **A-CRW-BE-5:** `submittedAt` is required on POST success because `StartRunResponse` in `src/frontend/src/types.ts` includes it.
- **A-CRW-BE-6:** GET uses HTTP 200 for known runs in `running`, `done`, and `error` so pollers can branch on `status` without using HTTP codes as the crew state machine.
- **A-CRW-BE-7:** Single-process in-memory dict is enough for local demo; multiple uvicorn workers would not share state and are out of v1.
- **A-CRW-BE-8:** v1 crew has no tools (no web fetch). `sources[].url` may be model-produced strings; they are not fetched by this backend.
- **A-CRW-BE-9:** Filename uses requested spelling `backend-functional-spec.md` (unlike `frontend-funcional-spec.md`).

---

## Open Questions

1. Should this prototype become a PRD/SAD-scoped product, or remain a disposable API spike? (Same unresolved question as the frontend spec.)
2. Should `POST /runs` stay at `202`, or use `200` to match naive `fetch` helpers?
3. When `@integration.eng` wires the UI, what poll interval and max wait should `getRunStatus` use?
4. Should CI call a real LLM, or is a kickoff test double acceptable for the POST → poll → done loop?
5. After the async loop is proven, what is the first extra agent/task (if any), and does `ResearchResult` stay unchanged?

---

## Audit

**Timestamp:** 2026-08-23
**Persona ID:** `backend-eng`
**Action:** `develop-be` (specification only; no backend package scaffolded in this commit)
**Artifact:** `project-context/1.define/backend-functional-spec.md`
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`)
**Prompt Trace:** Omitted — specification artifact; no live crew kickoff
**Conflict:** Original PRD/SAD forbade a research-run web API for the onboarding MVP. This artifact remains the Critical Research Workflow backend contract for `src/frontend/` only. The onboarding HTTP wrap is `onboarding-backend-spec.md` / `src/onboarding/api.py`.

---

## Audit (sync-docs 2026-08-28)

**Timestamp:** 2026-08-28
**Persona ID:** `project-mgr` (operator requested documentation sync)
**Action:** `sync-docs`
**What changed:** Paths `frontend/` → `src/frontend/`. Distinguished this CRW contract from the onboarding API at `src/onboarding/api.py`.
