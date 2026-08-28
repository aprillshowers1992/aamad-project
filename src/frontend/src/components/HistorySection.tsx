import { CREW_STATUS_LABELS } from "../statusLabels";
import type { HistoryEntry } from "../types";

interface HistorySectionProps {
  entries: HistoryEntry[];
  activeRunId: string | null;
}

export function HistorySection({ entries, activeRunId }: HistorySectionProps) {
  return (
    <section className="panel" aria-labelledby="history-heading">
      <h2 id="history-heading">History</h2>
      <p className="lede">
        Session-only. Refresh restores the seeded example and clears runs started in
        this tab.
      </p>
      <ul className="history">
        {entries.map((entry) => (
          <li
            key={entry.runId}
            className={entry.runId === activeRunId ? "history-item active" : "history-item"}
          >
            <div className="history-top">
              <code>{entry.runId}</code>
              <span className="badge badge-done">{CREW_STATUS_LABELS[entry.status]}</span>
            </div>
            <p>{entry.question}</p>
            <p className="muted">
              {entry.domain} · {entry.completedAt}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
