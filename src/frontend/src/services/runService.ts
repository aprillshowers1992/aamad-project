import type {
  ResearchInput,
  ResearchResult,
  RunStatusResponse,
  StartRunResponse,
} from "../types";

const START_DELAY_MS = 400;
const STATUS_DELAY_MS = 600;
/** Stub stays `running` long enough for a few 2s polls, then `done`. */
const STUB_RUNNING_MS = 5000;

export const RUN_POLL_INTERVAL_MS = 2000;
export const RUN_POLL_TIMEOUT_MS = 60000;

const MOCK_SUMMARY =
  "Stub analysis complete. This fixture is deterministic and is not live research.";

const MOCK_FINDINGS = [
  "The workflow accepted the submitted question and recorded a run identifier.",
  "No external sources were queried; findings are placeholder text.",
  "Replace stub services with a real backend when integration is in scope.",
] as const;

const MOCK_SOURCES = [
  { title: "AAMAD PRD (local)", url: "in-app note; not fetched — project-context/1.define/prd.md" },
  { title: "AAMAD SAD (local)", url: "in-app note; not fetched — project-context/1.define/sad.md" },
] as const;

interface StubRunRecord {
  input: ResearchInput;
  startedAt: number;
  status: "running" | "done" | "error";
  result: ResearchResult | null;
  message: string | null;
}

const stubRuns = new Map<string, StubRunRecord>();

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function createRunId(): string {
  return `run-mock-${Date.now()}`;
}

function buildFixedResult(
  runId: string,
  input: ResearchInput,
  completedAt: string,
): ResearchResult {
  return {
    runId,
    question: input.question,
    domain: input.domain,
    summary: MOCK_SUMMARY,
    findings: [...MOCK_FINDINGS],
    sources: MOCK_SOURCES.map((source) => ({ ...source })),
    completedAt,
  };
}

/** Starts a mocked run. No HTTP. Returns a running status after a short delay. */
export async function startRun(input: ResearchInput): Promise<StartRunResponse> {
  await delay(START_DELAY_MS);
  const runId = createRunId();
  stubRuns.set(runId, {
    input,
    startedAt: Date.now(),
    status: "running",
    result: null,
    message: null,
  });
  return {
    runId,
    status: "running",
    submittedAt: new Date().toISOString(),
  };
}

/**
 * Reads mocked run status. Returns `running` until the stub duration elapses,
 * then `done` with a fixed result. Subsequent polls of a finished run stay terminal.
 */
export async function getRunStatus(runId: string): Promise<RunStatusResponse> {
  await delay(STATUS_DELAY_MS);
  const record = stubRuns.get(runId);
  if (!record) {
    return {
      runId,
      status: "error",
      message: "Run not found.",
    };
  }
  if (record.status === "done" && record.result) {
    return {
      runId,
      status: "done",
      result: record.result,
    };
  }
  if (record.status === "error") {
    return {
      runId,
      status: "error",
      message: record.message ?? "The run failed.",
    };
  }
  if (Date.now() - record.startedAt >= STUB_RUNNING_MS) {
    const result = buildFixedResult(runId, record.input, new Date().toISOString());
    record.status = "done";
    record.result = result;
    return {
      runId,
      status: "done",
      result,
    };
  }
  return {
    runId,
    status: "running",
  };
}

export interface WatchRunStatusHandlers {
  onRunning: () => void;
  onDone: (result: ResearchResult) => void;
  onError: (message: string) => void;
  onTimeout: () => void;
}

/**
 * Polls `getRunStatus` immediately, then every `intervalMs`, until done, error,
 * timeout, or the returned stop function runs (Reset / unmount).
 */
export function watchRunStatus(
  runId: string,
  handlers: WatchRunStatusHandlers,
  options?: { intervalMs?: number; timeoutMs?: number },
): () => void {
  const intervalMs = options?.intervalMs ?? RUN_POLL_INTERVAL_MS;
  const timeoutMs = options?.timeoutMs ?? RUN_POLL_TIMEOUT_MS;
  let stopped = false;
  let inFlight = false;
  let intervalId: number | null = null;
  let timeoutId: number | null = null;

  const stop = (): void => {
    stopped = true;
    if (intervalId !== null) {
      window.clearInterval(intervalId);
      intervalId = null;
    }
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  const tick = async (): Promise<void> => {
    if (stopped || inFlight) {
      return;
    }
    inFlight = true;
    try {
      const status = await getRunStatus(runId);
      if (stopped) {
        return;
      }
      if (status.status === "running") {
        handlers.onRunning();
        return;
      }
      stop();
      if (status.status === "done") {
        handlers.onDone(status.result);
        return;
      }
      handlers.onError(status.message);
    } catch {
      if (stopped) {
        return;
      }
      stop();
      handlers.onError("The run failed.");
    } finally {
      inFlight = false;
    }
  };

  void tick();
  intervalId = window.setInterval(() => {
    void tick();
  }, intervalMs);
  timeoutId = window.setTimeout(() => {
    if (stopped) {
      return;
    }
    stop();
    handlers.onTimeout();
  }, timeoutMs);

  return stop;
}
