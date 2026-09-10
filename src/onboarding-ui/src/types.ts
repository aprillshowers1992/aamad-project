export const CANONICAL_ROLES = [
  "UI Designer",
  "UX Researcher",
  "Product Manager",
  "Developer",
  "Engineer",
] as const;

export type CanonicalRole = (typeof CANONICAL_ROLES)[number];

export const CATALOG_ROLE: CanonicalRole = "Developer";

/** Operator-facing metadata only (SAD SD-7). Does not filter the catalog. */
export const CANONICAL_DEPARTMENTS = [
  "AI Engineering",
  "Product",
  "Design",
  "Engineering",
  "Research",
] as const;

export type CanonicalDepartment = (typeof CANONICAL_DEPARTMENTS)[number];

export type { RunPhase } from "./statusLabels";

export interface OnboardingFormInput {
  role: CanonicalRole;
  department: CanonicalDepartment | "";
  startDate: string;
}

export interface OnboardingResult {
  runId: string;
  role: string;
  department: string;
  startDate: string;
  onboardingPlan: string;
  managerChecklist: string;
  completedAt: string;
}

export interface StartRunResponse {
  runId: string;
  status: "running";
  submittedAt: string;
}

export interface RunStatusRunningResponse {
  runId: string;
  status: "running";
}

export interface RunStatusDoneResponse {
  runId: string;
  status: "done";
  result: OnboardingResult;
}

export interface RunStatusErrorResponse {
  runId: string;
  status: "error";
  message: string;
  violations: string[];
}

export type RunStatusResponse =
  | RunStatusRunningResponse
  | RunStatusDoneResponse
  | RunStatusErrorResponse;

export interface RunError {
  message: string;
  violations: string[];
}
