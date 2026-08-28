# Frontend Functional Spec — Critical Research Workflow

**Persona:** `frontend-eng`
**Action:** `develop-fe` (operator-requested UI prototype)
**Phase:** Build (prototype; not the CLI onboarding MVP)
**Intended path:** `project-context/1.define/frontend-funcional-spec.md`
**Product surface:** Critical Research Workflow
**Implementation:** `src/frontend/` (Vite + React + TypeScript)
**Status:** Initial scaffold — update the Spec Sync checklist after every commit

---

## Purpose and Scope

- **Feature ID:** CRW-FE-001
- **Purpose:** Give a researcher a single-page surface to submit a critical-research question, start a mocked run, inspect results, and review session history.
- **In Scope:** Inputs form; run control and status banner; results display; in-session history; finite state machine `idle → running → done | error`; stub services `startRun` and `getRunStatus`; basic keyboard and heading accessibility.
- **Out of Scope:** Live backend or LLM calls; authentication; multi-route navigation; persistence beyond the current browser session; the Automated Employee Onboarding Workflow CLI; pause; cancel; retry-diff (Retry always resends the last submitted inputs).

This document is the contract for the Vite app under `src/frontend/`. Code and this spec must stay aligned via the Spec Sync checklist.

---

## Traceability

- **Operator request (2026-08-23):** Create this spec (Inputs, Run, Results, History, Spec Sync checklist) and a single-route React/TypeScript Vite app with stubbed run services.
- **PRD:** `project-context/1.define/prd.md` — current product MVP is CLI `onboard`; web UI is listed as Future Work (PRD §4 P2, §6). This prototype does **not** implement FR-001–FR-016.
- **SAD:** `project-context/1.define/sad.md` §3 — onboarding product UI is SD-10 (`src/onboarding-ui/`). This app is a separate Critical Research Workflow prototype.
- **Config:** `aamad.config.yml` — `ui.theme: system`, `ui.visual_style: minimal`, `ui.prefer_modals: false`, `coding_standards.type_checking: true`.
- **User stories:** none present.

---

## Inputs

The Inputs section is the only place a researcher enters data. It is enabled in `idle` and `done`. It is disabled in `running` and `error` (Retry uses stored inputs; edit after Reset only).

| Input name | Type / format | Required | Source | Validation |
| ---------- | ------------- | -------- | ------ | ---------- |
| `question` | string | Yes | Form textarea | Trimmed, non-empty, minimum 8 characters |
| `domain` | enum: `general` \| `product` \| `technical` \| `operations` | Yes | Form select | Must be one of the four values; default `general` |
| `scope` | string | No | Form textarea | Trimmed; empty string allowed; max 500 characters |

**Run** lives in the Run section (not on the Inputs form). It is available only when the machine is `idle` and Inputs validate. It does not use a modal (`prefer_modals: false`).

**Mapped payload** sent to `startRun`:

```text
ResearchInput
- question: string
- domain: "general" | "product" | "technical" | "operations"
- scope: string
```

Client-side validation failures stay on the Inputs section. The crew / stub run is never started.

---

## Run

The Run section owns the finite state machine and stub service calls. There is a **single route** (`/`). Form and results share that route; visibility follows `phase`.

### Finite state machine

```text
idle  -- START (Run) -->  running  -- COMPLETE -->  done
  ^                         |                         |
  |                         +-- FAIL --> error -------+
  |                                      |            |
  |                                      +-- RETRY --> running
  +---------------- RESET ----------------------------+
```

| State | User-visible meaning | Allowed actions |
| ----- | -------------------- | --------------- |
| `idle` | No active run | Edit Inputs; **Run**; **Reset** (clears form, stays idle) |
| `running` | Stub run in progress | None (form disabled; no pause/cancel) |
| `done` | Mock result available | **Reset** → `idle`; inspect Results and History |
| `error` | Stub run threw | Inline error; **Retry** (same inputs) → `running`; **Reset** → `idle` |

Illegal transitions are ignored (state unchanged). Stub calls normally resolve; a thrown stub error transitions `running → error`. **Pause**, **cancel**, and **retry-diff** are not implemented.

### Status labels (shared constant)

All crew-status wording comes from `CREW_STATUS_LABELS` in `src/frontend/src/statusLabels.ts`. Do not retype these strings in the banner, Run badge, History pill, or error messages.

| Key | Exact label |
| --- | ----------- |
| `idle` | `Crew: idle` |
| `running` | `Crew: running` |
| `done` | `Crew: done` |
| `error` | `Crew: error` |

### Status banner

Fixed at the top of the single page, bound to FSM `phase`:

- Colored pill: gray / blue / green / red for idle / running / done / error
- Label: `CREW_STATUS_LABELS[phase]`
- `Last updated: [ISO timestamp]` updates whenever `phase` changes (including the initial idle stamp on load)

### Stub services (no network)

Both functions wait a short in-process delay, then return **fixed mock data**. They MUST NOT call a real HTTP API.

| Function | Input | Delay | Success payload |
| -------- | ----- | ----- | --------------- |
| `startRun` | `ResearchInput` | ~400 ms | `{ runId, status: "running", submittedAt }` |
| `getRunStatus` | `runId: string` | ~600 ms | `{ runId, status: "done", result: ResearchResult }` |

**Client sequence (Run):**

1. Validate Inputs. On failure, show an Inputs validation message; stay `idle`.
2. Transition `idle → running`.
3. Store the submitted payload as `lastSubmitted`.
4. Call `startRun(input)`.
5. Call `getRunStatus(runId)` once (this prototype does not poll a live backend).
6. Transition `running → done` and store `result`.
7. Append a History entry.

**Client sequence (Retry):** same as steps 2–7 using `lastSubmitted` only (`error → running`). Do not re-read the form.

`runId` is unique per start (for History). **Result content is always the same mock fixture**, independent of Inputs, so the stub contract stays deterministic.

### Run section UI

- Phase badge: `CREW_STATUS_LABELS[phase]` (same wording as the banner)
- Current `runId` when not idle
- **Run** — enabled only in `idle`; calls `startRun` and transitions to `running`
- **Reset** — enabled when not `running`; returns to `idle` and clears the current run, form, and errors
- **Retry** — visible only in `error`; resends `lastSubmitted` (same inputs). Not retry-diff.
- While `running`, show a non-blocking status line that includes `Crew: running` — no modal
- While `error`, show an inline error that includes `Crew: error` plus **Retry**
- No Pause or Cancel controls

### Accessibility (basic pass)

- Heading outline: one page `h1` (Critical Research Workflow); section `h2` for Inputs, Run, Results, History; Results subsections use `h3` (Findings, Sources).
- Interactive controls are native `<textarea>`, `<select>`, and `<button type="button">` in document order: question → domain → scope → Run → Reset → Retry (Retry only when visible).
- Enter and Space activate buttons via the browser; no custom key handlers.
- Visible `:focus-visible` ring on interactive controls and the skip-link. Disabled controls are not in the tab order.
- Skip link (“Skip to main content”) is the first focusable control.
- No ARIA live regions in this pass (`role="status"`, `aria-live`, and `role="alert"` are not used).

---

## Results

The Results section renders only when `phase === "done"` and a `ResearchResult` is present. Empty placeholder in `idle`, `running`, and `error` (copy uses `Crew: done`).

| Field | Type | Display |
| ----- | ---- | ------- |
| `runId` | string | Run ID |
| `question` | string | Echo of submitted question |
| `domain` | enum | Caption |
| `summary` | string | Lead paragraph |
| `findings` | `string[]` | Ordered list |
| `sources` | `{ title: string; url: string }[]` | Link list (fixture URLs only) |
| `completedAt` | ISO-8601 string | Completed |

**Fixed mock result (contract):**

```text
summary: "Stub analysis complete. This fixture is deterministic and is not live research."
findings:
  - "The workflow accepted the submitted question and recorded a run identifier."
  - "No external sources were queried; findings are placeholder text."
  - "Replace stub services with a real backend when integration is in scope."
sources:
  - title: "AAMAD PRD (local)"
    url: "in-app note; not fetched — project-context/1.define/prd.md"
  - title: "AAMAD SAD (local)"
    url: "in-app note; not fetched — project-context/1.define/sad.md"
```

Results are read-only. There is no export, share, or edit in this prototype.

---

## History

History is **session-scoped** (React state). It is not written to disk or a backend.

| Field | Type | Notes |
| ----- | ---- | ----- |
| `runId` | string | Matches the stub `runId` |
| `question` | string | Submitted question (truncated in the list if long) |
| `domain` | enum | Submitted domain |
| `completedAt` | ISO-8601 string | From the mock result |
| `status` | `"done"` | Only completed runs are recorded |

**Behavior:**

- One seeded example row exists on first load so the section is never blank.
- Each successful `done` transition prepends a new row.
- Selecting a history row shows that row’s question in Results **only if** the current phase is `done` and the selected `runId` matches the latest result. In this prototype, all completed runs share the same fixture findings; the list is an audit of submissions, not a multi-result archive.
- History is visible in all phases.

No delete, filter, or pagination in this prototype.

---

## Spec Sync checklist

Update this table after **each commit** that changes UI copy, form fields, FSM transitions, stub payloads, or this spec. Status is `Done` when the running UI matches the spec, `Partial` if only some of the item is true, or `Open` if not built.

| Item | Status | Note |
| ---- | ------ | ---- |
| Form (Inputs) | Done | Question, domain, and optional scope; validation stays on idle; disabled while running or error. |
| FSM | Done | `idle → running → done \| error`; RESET to idle; RETRY is `error → running`. |
| Status banner | Done | Top of page bound to FSM; wording from `CREW_STATUS_LABELS`. |
| Status pill | Done | Gray / blue / green / red for idle / running / done / error. |
| Last-updated timestamp | Done | `Last updated: [ISO]` refreshes only when `phase` changes. |
| Run / Reset | Done | **Run** calls `startRun` from idle; **Reset** returns to idle and clears the current run. |
| Error + Retry | Done | Inline `Crew: error` copy; **Retry** resends `lastSubmitted` (not retry-diff). |
| Clickable sources | Done | Each `sources` item is `<a href={url} target="_blank" rel="noopener noreferrer">{title}</a>`. |
| Spec sections Inputs, Run, Results, History | Done | Contract lives in this file; UI sections match those four names. |
| Single-route Vite React/TypeScript app | Done | `src/frontend/` serves `/` only; form and results share one page. |
| Stub `startRun` / `getRunStatus` | Done | In-process delay + fixed mock; no HTTP; replace later per `src/frontend/README.md`. |
| Shared `CREW_STATUS_LABELS` | Done | Banner, Run badge, History pills, and error copy all read `Crew: idle\|running\|done\|error`. |
| No pause, cancel, or retry-diff | Done | Reset is disabled while running; Retry never re-reads the form. |
| Session History + Results fixture | Done | Seeded row on load; successful runs prepend; results show the stub fixture. |
| Basic accessibility pass | Done | h1/h2 outline (h3 under Results); native tab order; visible focus; no ARIA live regions. |
| Local run + CrewAI hook docs | Done | `src/frontend/README.md` covers install/dev, stubs, known limits, and the next CrewAI contract. |

### Per-commit ritual

- [ ] Re-read **Inputs**, **Run**, **Results**, and **History** against the running UI
- [ ] Confirm `startRun` / `getRunStatus` still match the Run table (delay + fixed mock, no HTTP) until a backend is wired
- [ ] Confirm the machine is `idle → running → done | error` (Reset to `idle`; Retry from `error` with same inputs)
- [ ] Confirm controls are only **Run**, **Reset**, and **Retry** (no pause/cancel/retry-diff)
- [ ] Confirm the status banner uses `CREW_STATUS_LABELS` and updates Last updated on phase change
- [ ] Confirm a single route (`/`) still hosts form + results
- [ ] Confirm heading outline (h1/h2), tab order, and visible focus; no ARIA live regions
- [ ] Set the matching row above to `Done` / `Partial` / `Open` and refresh its one-line note
- [ ] Leave items `Open` if the commit did not finish them

---

## Sources

1. Operator request, 2026-08-23 — spec sections, Vite React/TypeScript app, FSM, stub services, Spec Sync checklist.
2. Operator request, 2026-08-23 — Spec Sync item/status/note table; `src/frontend/README.md` local run + CrewAI connection notes.
3. `project-context/1.define/prd.md` — CLI remains the underlying interface; SD-10 added a minimal onboarding UI wrap (this CRW prototype is separate).
4. `project-context/1.define/sad.md` §3 Frontend Architecture — onboarding product UI is `src/onboarding-ui/` (SD-10).
5. `aamad.config.yml` — UI theme/minimal, no modals, type checking; `runtime.target: crewai`.
6. `.cursor/templates/sfs-template.md` — heading taxonomy (adapted; filename requested as `frontend-funcional-spec.md`).
7. `src/frontend/README.md` — local run instructions and CrewAI integration hook.

---

## Assumptions

- **A-CRW-1:** “Critical Research Workflow” is an operator-requested prototype name, not a named PRD epic. Inputs/results are a minimal research-run metaphor.
- **A-CRW-2:** Filename keeps the requested spelling `frontend-funcional-spec.md`.
- **A-CRW-3:** Single route means no React Router routes beyond the Vite SPA entry; sections are one page.
- **A-CRW-4:** Stub delays are approximately 400 ms / 600 ms; exact timing may vary slightly by environment.
- **A-CRW-5:** History is in-memory only; refresh clears user-started runs and restores the seeded row.
- **A-CRW-6:** This UI does not change onboarding CLI scope in the PRD/SAD.

---

## Open Questions

1. Should this prototype become a PRD/SAD-scoped product, or remain a disposable UI spike?
2. When a real backend exists, should Inputs (`question`, `domain`, `scope`) map to a documented API, or should the form change?
3. Should History persist (localStorage or server) after session refresh?
4. ~~Should an `error` / `failed` FSM state be added?~~ **Resolved 2026-08-23:** `error` is an FSM state (`running --FAIL--> error`). **Reset** returns to `idle`. **Retry** resends the same inputs (`error --RETRY--> running`). Pause, cancel, and retry-diff remain out of scope.

---

## Audit

**Timestamp:** 2026-08-23
**Persona ID:** `frontend-eng`
**Action:** `develop-fe` (handoff docs: README order + Known limitations; Spec Sync rows per built feature)
**Artifact:** `project-context/1.define/frontend-funcional-spec.md`
**Resolved `AAMAD_TARGET_RUNTIME`:** `crewai` (env unset; `aamad.config.yml` `runtime.target: crewai`) — **not used** by this stub UI
**Prompt Trace:** Omitted — specification and local stub UI; no live model/tool backend run
**Conflict:** Original PRD/SAD forbade a web UI for the onboarding MVP. SD-10 later added `src/onboarding-ui/` as a wrap of the CLI/API core. **This artifact and `src/frontend/` remain the Critical Research Workflow prototype only** — they are not the onboarding product UI.

---

## Audit (sync-docs 2026-08-28)

**Timestamp:** 2026-08-28
**Persona ID:** `project-mgr` (operator requested documentation sync)
**Action:** `sync-docs`
**What changed:** Implementation paths `frontend/` → `src/frontend/`. Clarified this spec is not the SD-10 onboarding UI (`src/onboarding-ui/`).
