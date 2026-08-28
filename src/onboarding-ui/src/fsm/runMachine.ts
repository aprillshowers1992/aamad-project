import type { RunPhase } from "../statusLabels";

export type RunEvent =
  | { type: "START" }
  | { type: "COMPLETE" }
  | { type: "FAIL" }
  | { type: "RETRY" }
  | { type: "RESET" };

/**
 * Lightweight FSM for a single onboarding run.
 * Legal path: idle --START--> running --COMPLETE--> done --RESET--> idle
 *                          \--FAIL--> error --RESET--> idle
 *                          \--FAIL--> error --RETRY--> running
 *                          \--RESET--> idle  (stops polling; not a backend cancel)
 * Pause, cancel, and retry-diff are out of scope.
 * Illegal events leave the current phase unchanged.
 */
export function nextPhase(phase: RunPhase, event: RunEvent): RunPhase {
  switch (phase) {
    case "idle":
      return event.type === "START" ? "running" : phase;
    case "running":
      if (event.type === "COMPLETE") {
        return "done";
      }
      if (event.type === "FAIL") {
        return "error";
      }
      if (event.type === "RESET") {
        return "idle";
      }
      return phase;
    case "done":
      return event.type === "RESET" ? "idle" : phase;
    case "error":
      if (event.type === "RETRY") {
        return "running";
      }
      if (event.type === "RESET") {
        return "idle";
      }
      return phase;
    default: {
      const _exhaustive: never = phase;
      return _exhaustive;
    }
  }
}

export function canRun(phase: RunPhase): boolean {
  return phase === "idle";
}

export function canReset(phase: RunPhase): boolean {
  void phase;
  return true;
}

export function canRetry(phase: RunPhase): boolean {
  return phase === "error";
}
