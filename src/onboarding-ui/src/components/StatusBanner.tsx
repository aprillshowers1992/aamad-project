import { CREW_STATUS_LABELS, type RunPhase } from "../statusLabels";

interface StatusBannerProps {
  phase: RunPhase;
  lastUpdated: string;
}

export function StatusBanner({ phase, lastUpdated }: StatusBannerProps) {
  return (
    <div className="status-banner">
      <span className={`status-pill status-pill-${phase}`} aria-hidden="true" />
      <strong>{CREW_STATUS_LABELS[phase]}</strong>
      <span className="last-updated">Last updated: {lastUpdated}</span>
    </div>
  );
}
