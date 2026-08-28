/**
 * Single source of status wording. Banner, pills, buttons, and error copy
 * must read these strings — do not retype idle/running/done/error elsewhere.
 */
export const CREW_STATUS_LABELS = {
  idle: "Crew: idle",
  running: "Crew: running",
  done: "Crew: done",
  error: "Crew: error",
} as const;

export type RunPhase = keyof typeof CREW_STATUS_LABELS;
