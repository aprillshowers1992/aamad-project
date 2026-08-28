import type {
  OnboardingFormInput,
  OnboardingResult,
  RunError,
  RunStatusResponse,
  StartRunResponse,
} from "../types";

export const RUN_POLL_INTERVAL_MS = 2000;
export const RUN_POLL_TIMEOUT_MS = 60000;

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function readError(response: Response): Promise<RunError> {
  try {
    const body = (await response.json()) as {
      message?: string;
      violations?: string[];
    };
    return {
      message: body.message?.trim() || `Request failed (${response.status}).`,
      violations: Array.isArray(body.violations) ? body.violations : [],
    };
  } catch {
    return {
      message: `Request failed (${response.status}).`,
      violations: [],
    };
  }
}

function toApiBody(input: OnboardingFormInput): {
  role: string;
  department: string;
  start_date: string;
} {
  return {
    role: input.role,
    department: input.department,
    start_date: input.startDate,
  };
}

function asDoneResult(runId: string, raw: Record<string, unknown>): OnboardingResult {
  return {
    runId,
    role: String(raw.role ?? ""),
    department: String(raw.department ?? ""),
    startDate: String(raw.startDate ?? ""),
    onboardingPlan: String(raw.onboardingPlan ?? ""),
    managerChecklist: String(raw.managerChecklist ?? ""),
    completedAt: String(raw.completedAt ?? ""),
  };
}

export async function startRun(input: OnboardingFormInput): Promise<StartRunResponse> {
  const response = await fetch(`${API_BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toApiBody(input)),
  });
  if (!response.ok) {
    const error = await readError(response);
    throw error;
  }
  const body = (await response.json()) as StartRunResponse;
  if (body.status !== "running" || !body.runId) {
    throw { message: "The server did not accept the run.", violations: [] } satisfies RunError;
  }
  return body;
}

export async function getRunStatus(runId: string): Promise<RunStatusResponse> {
  const response = await fetch(`${API_BASE}/runs/${encodeURIComponent(runId)}`);
  if (response.status === 404) {
    const error = await readError(response);
    return {
      runId,
      status: "error",
      message: error.message,
      violations: error.violations,
    };
  }
  if (!response.ok) {
    const error = await readError(response);
    throw error;
  }
  const body = (await response.json()) as {
    runId?: string;
    status?: string;
    result?: Record<string, unknown>;
    message?: string;
    violations?: string[];
  };
  const id = body.runId ?? runId;
  if (body.status === "running") {
    return { runId: id, status: "running" };
  }
  if (body.status === "done" && body.result) {
    return {
      runId: id,
      status: "done",
      result: asDoneResult(id, body.result),
    };
  }
  if (body.status === "error") {
    return {
      runId: id,
      status: "error",
      message: body.message?.trim() || "The run failed.",
      violations: Array.isArray(body.violations) ? body.violations : [],
    };
  }
  throw { message: "Unexpected run status.", violations: [] } satisfies RunError;
}

export interface WatchRunStatusHandlers {
  onRunning: () => void;
  onDone: (result: OnboardingResult) => void;
  onError: (error: RunError) => void;
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
      handlers.onError({
        message: status.message,
        violations: status.violations,
      });
    } catch (caught) {
      if (stopped) {
        return;
      }
      stop();
      const error = caught as Partial<RunError>;
      handlers.onError({
        message: error.message?.trim() || "The run failed.",
        violations: Array.isArray(error.violations) ? error.violations : [],
      });
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
