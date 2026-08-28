import { canReset, canRetry, canRun } from "../fsm/runMachine";
import { CREW_STATUS_LABELS, type RunPhase } from "../statusLabels";

interface RunSectionProps {
  phase: RunPhase;
  runId: string | null;
  runError: string | null;
  onRun: () => void;
  onReset: () => void;
  onRetry: () => void;
}

export function RunSection({
  phase,
  runId,
  runError,
  onRun,
  onReset,
  onRetry,
}: RunSectionProps) {
  return (
    <section className="panel" aria-labelledby="run-heading">
      <h2 id="run-heading">Run</h2>
      <p className="lede">
        Finite state machine: <code>{CREW_STATUS_LABELS.idle}</code> →{" "}
        <code>{CREW_STATUS_LABELS.running}</code> →{" "}
        <code>{CREW_STATUS_LABELS.done}</code> or{" "}
        <code>{CREW_STATUS_LABELS.error}</code>.
      </p>
      <dl className="meta">
        <div>
          <dt>Phase</dt>
          <dd>
            <span className={`badge badge-${phase}`}>{CREW_STATUS_LABELS[phase]}</span>
          </dd>
        </div>
        <div>
          <dt>Run ID</dt>
          <dd>
            <code>{runId ?? "—"}</code>
          </dd>
        </div>
      </dl>
      {phase === "running" ? (
        <p className="status">
          {CREW_STATUS_LABELS.running}. Checking status every 2 seconds.
        </p>
      ) : null}
      {phase === "error" ? (
        <p id="run-error" className="error">
          {runError ?? `${CREW_STATUS_LABELS.error}.`}
        </p>
      ) : null}
      <div className="actions">
        <button type="button" disabled={!canRun(phase)} onClick={onRun}>
          Run
        </button>
        <button
          type="button"
          className="secondary"
          disabled={!canReset(phase)}
          onClick={onReset}
        >
          Reset
        </button>
        {canRetry(phase) ? (
          <button
            type="button"
            aria-describedby={runError ? "run-error" : undefined}
            onClick={onRetry}
          >
            Retry
          </button>
        ) : null}
      </div>
    </section>
  );
}
