import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CREW_STATUS_LABELS, type RunPhase } from "../statusLabels";
import type { OnboardingResult } from "../types";

interface ResultsSectionProps {
  phase: RunPhase;
  result: OnboardingResult | null;
}

function InteractiveMarkdown({
  markdown,
  resetKey,
}: {
  markdown: string;
  resetKey: string;
}) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  useEffect(() => {
    setChecked({});
  }, [resetKey]);

  let checkboxIndex = 0;

  return (
    <Markdown
      remarkPlugins={[remarkGfm]}
      components={{
        input({ type, ...props }) {
          if (type !== "checkbox") {
            return <input type={type} {...props} />;
          }
          const index = checkboxIndex;
          checkboxIndex += 1;
          return (
            <input
              type="checkbox"
              checked={Boolean(checked[index])}
              onChange={() =>
                setChecked((current) => ({
                  ...current,
                  [index]: !current[index],
                }))
              }
            />
          );
        },
      }}
    >
      {markdown}
    </Markdown>
  );
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
              <InteractiveMarkdown
                markdown={result.onboardingPlan}
                resetKey={`${result.runId}-plan`}
              />
            </div>
          </article>
          <article className="markdown-doc" aria-labelledby="checklist-heading">
            <h3 id="checklist-heading">manager-checklist.md</h3>
            <div className="markdown-body">
              <InteractiveMarkdown
                markdown={result.managerChecklist}
                resetKey={`${result.runId}-checklist`}
              />
            </div>
          </article>
        </div>
      )}
    </section>
  );
}
