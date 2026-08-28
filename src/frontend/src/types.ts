export const RESEARCH_DOMAINS = [
  "general",
  "product",
  "technical",
  "operations",
] as const;

export type ResearchDomain = (typeof RESEARCH_DOMAINS)[number];

export type { RunPhase } from "./statusLabels";

export interface ResearchInput {
  question: string;
  domain: ResearchDomain;
  scope: string;
}

export interface ResearchSource {
  title: string;
  url: string;
}

export interface ResearchResult {
  runId: string;
  question: string;
  domain: ResearchDomain;
  summary: string;
  findings: string[];
  sources: ResearchSource[];
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
  result: ResearchResult;
}

export interface RunStatusErrorResponse {
  runId: string;
  status: "error";
  message: string;
}

export type RunStatusResponse =
  | RunStatusRunningResponse
  | RunStatusDoneResponse
  | RunStatusErrorResponse;

export interface HistoryEntry {
  runId: string;
  question: string;
  domain: ResearchDomain;
  completedAt: string;
  status: "done";
}
