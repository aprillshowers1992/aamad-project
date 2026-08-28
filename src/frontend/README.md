# Critical Research Workflow (frontend)

Single-route Vite + React + TypeScript prototype for a mocked research run (`idle → running → done | error`). **This is not the onboarding product.** The onboarding UI is [`../onboarding-ui/`](../onboarding-ui/).

Functional contract: [`../../project-context/1.define/frontend-funcional-spec.md`](../../project-context/1.define/frontend-funcional-spec.md).

## Run locally

**Need:** Node.js LTS (18+) and npm on your `PATH`.

```text
cd src/frontend
npm install
npm run dev
```

Open [http://localhost:5173/](http://localhost:5173/). The dev server is pinned to port **5173**.

| Script | What it does |
| ------ | ------------ |
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Typecheck (`tsc -b`) then production bundle |
| `npm run preview` | Serve the production bundle locally |

This app does not read `OPENAI_API_KEY` or any other secret. Do not add keys to the frontend.

## Stubbed services

`startRun` and `getRunStatus` in [`src/services/runService.ts`](src/services/runService.ts) are in-process stubs. They wait a short delay and return **fixed mock data**. There is no HTTP call and no real backend yet.

## Known limitations

- Pause, cancel, and retry-diff are not implemented. **Retry** resends the last submitted inputs only.
- Source links use local fixture `url` strings (PRD/SAD paths in an “in-app note; not fetched” prefix), not content retrieved from the network.
- Only one seeded happy-path input has been tested (the History seed plus a successful stub run).

## Where CrewAI connects next

Stubs live in [`src/services/runService.ts`](src/services/runService.ts). Keep those function names and return shapes. Swap the bodies to HTTP (or a thin client) when `@backend.eng` / `@integration.eng` expose a run API. Do not call CrewAI or `crew.kickoff()` from the browser.

Resolved runtime for this repo is **CrewAI** (`aamad.config.yml` `runtime.target: crewai`). LLM secrets stay on the server (`OPENAI_API_KEY`).

### `startRun(input)`

Today: waits ~400 ms and returns `{ runId, status: "running", submittedAt }`.

**Next:** `POST` a create-run endpoint on the Python backend. The handler should:

1. Validate `ResearchInput` (`question`, `domain`, `scope`) the same way the UI does.
2. Allocate a `runId` and persist `running`.
3. Start the CrewAI crew (`crew.kickoff()` / orchestrator) **asynchronously** so the HTTP response can return `running` without waiting for the full crew.
4. Return `{ runId, status: "running", submittedAt }` so the FSM can stay on `Crew: running`.

Do not have `startRun` wait for the crew to finish.

### `getRunStatus(runId)`

Today: waits ~600 ms and always returns `{ runId, status: "done", result }` with a fixed fixture.

**Next:** `GET` (or poll) a run-status endpoint. The handler should read orchestrator state for that `runId` and return one of:

| Backend outcome | Response the UI needs | FSM |
| --------------- | --------------------- | --- |
| Crew still working | `{ runId, status: "running" }` | stay `running`; poll again |
| Crew finished | `{ runId, status: "done", result: ResearchResult }` | `COMPLETE` → `done` |
| Crew / API failed | throw or `{ status: "error", message }` | `FAIL` → `error` |

`ResearchResult` must keep: `runId`, `question`, `domain`, `summary`, `findings[]`, `sources[{ title, url }]`, `completedAt`. Map CrewAI / Document Writer output into that shape on the server.

The UI currently calls `getRunStatus` **once** after `startRun`. A real crew needs a short poll loop (or one request that stays `running`) until `done` or `error`. Pause and cancel are still out of scope, so the backend does not need those routes yet.

### Boundary

```text
Browser (this app)
  Run / Retry
    → startRun(ResearchInput)     → POST /api/…/runs          → WorkflowOrchestrator + CrewAI
    → getRunStatus(runId)         → GET  /api/…/runs/{runId}  → run store / crew result
  Reset
    → local FSM only (no backend call)
```

Exact URL paths are not specified yet. When they exist, change only `runService.ts` (plus types if the envelope adds fields). Leave the FSM and `CREW_STATUS_LABELS` as the UI contract.
