import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CREW_STATUS_LABELS, type RunPhase } from "../statusLabels";
import type { OnboardingResult } from "../types";

interface ResultsSectionProps {
  phase: RunPhase;
  result: OnboardingResult | null;
}

export function ResultsSection({ phase, result }: ResultsSectionProps) {
  return (
    <section className="panel" aria-labelledby="results-heading">
      <h2 id="results-heading">Results</h2>
      {phase !== "done" || !result ? (
        <p className="lede">
          The onboarding plan and manager checklist appear here when a run reaches{" "}
          {CREW_STATUS_LABELS.done}.
        </p>
      ) : (
        <div className="stack">
          <dl className="meta">
            <div>
              <dt>Run ID</dt>
              <dd>
                <code>{result.runId}</code>
              </dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{result.role}</dd>
            </div>
            <div>
              <dt>Department</dt>
              <dd>{result.department}</dd>
            </div>
            <div>
              <dt>Start date</dt>
              <dd>{result.startDate}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{result.completedAt}</dd>
            </div>
          </dl>
          <article className="markdown-doc" aria-labelledby="plan-heading">
            <h3 id="plan-heading">onboarding-plan.md</h3>
            <div className="markdown-body">
              <Markdown remarkPlugins={[remarkGfm]}>{result.onboardingPlan}</Markdown>
            </div>
          </article>
          <article className="markdown-doc" aria-labelledby="checklist-heading">
            <h3 id="checklist-heading">manager-checklist.md</h3>
            <div className="markdown-body">
              <Markdown remarkPlugins={[remarkGfm]}>{result.managerChecklist}</Markdown>
            </div>
          </article>
        </div>
      )}
    </section>
  );
}
