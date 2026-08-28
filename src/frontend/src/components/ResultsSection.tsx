import { CREW_STATUS_LABELS, type RunPhase } from "../statusLabels";
import type { ResearchResult } from "../types";

interface ResultsSectionProps {
  phase: RunPhase;
  result: ResearchResult | null;
}

export function ResultsSection({ phase, result }: ResultsSectionProps) {
  return (
    <section className="panel" aria-labelledby="results-heading">
      <h2 id="results-heading">Results</h2>
      {phase !== "done" || !result ? (
        <p className="lede">
          Results appear here when a run reaches {CREW_STATUS_LABELS.done}.
        </p>
      ) : (
        <div className="stack">
          <p className="lede">{result.summary}</p>
          <dl className="meta">
            <div>
              <dt>Run ID</dt>
              <dd>
                <code>{result.runId}</code>
              </dd>
            </div>
            <div>
              <dt>Domain</dt>
              <dd>{result.domain}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{result.completedAt}</dd>
            </div>
          </dl>
          <p>
            <strong>Question.</strong> {result.question}
          </p>
          <div>
            <h3>Findings</h3>
            <ol>
              {result.findings.map((finding) => (
                <li key={finding}>{finding}</li>
              ))}
            </ol>
          </div>
          <div>
            <h3>Sources</h3>
            <ul>
              {result.sources.map((source) => (
                <li key={source.title}>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {source.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
