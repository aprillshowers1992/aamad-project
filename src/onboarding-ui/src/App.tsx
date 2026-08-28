import { useEffect, useRef, useState } from "react";
import { InputsSection, validateInputs } from "./components/InputsSection";
import { ResultsSection } from "./components/ResultsSection";
import { RunSection } from "./components/RunSection";
import { StatusBanner } from "./components/StatusBanner";
import { canReset, canRetry, canRun, nextPhase, type RunEvent } from "./fsm/runMachine";
import { startRun, watchRunStatus } from "./services/runService";
import { CREW_STATUS_LABELS, type RunPhase } from "./statusLabels";
import { CATALOG_ROLE, type OnboardingFormInput, type OnboardingResult, type RunError } from "./types";

const EMPTY_INPUT: OnboardingFormInput = {
  role: CATALOG_ROLE,
  department: "",
  startDate: "",
};

const TIMEOUT_ERROR_MESSAGE = "This is taking longer than expected";

function trimInput(input: OnboardingFormInput): OnboardingFormInput {
  return {
    role: input.role,
    department: input.department.trim(),
    startDate: input.startDate,
  };
}

function asRunError(caught: unknown, fallback: string): RunError {
  if (caught && typeof caught === "object") {
    const record = caught as Partial<RunError>;
    return {
      message: record.message?.trim() || fallback,
      violations: Array.isArray(record.violations) ? record.violations : [],
    };
  }
  return { message: fallback, violations: [] };
}

export default function App() {
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [lastUpdated, setLastUpdated] = useState(() => new Date().toISOString());
  const [input, setInput] = useState<OnboardingFormInput>(EMPTY_INPUT);
  const [lastSubmitted, setLastSubmitted] = useState<OnboardingFormInput | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [runError, setRunError] = useState<RunError | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [result, setResult] = useState<OnboardingResult | null>(null);
  const stopWatchRef = useRef<(() => void) | null>(null);
  const runGenerationRef = useRef(0);

  const formDisabled = phase === "running" || phase === "error";

  function stopWatching(): void {
    stopWatchRef.current?.();
    stopWatchRef.current = null;
  }

  useEffect(() => {
    return () => {
      runGenerationRef.current += 1;
      stopWatchRef.current?.();
      stopWatchRef.current = null;
    };
  }, []);

  function dispatch(current: RunPhase, event: RunEvent): RunPhase {
    const next = nextPhase(current, event);
    if (next !== current) {
      setPhase(next);
      setLastUpdated(new Date().toISOString());
    }
    return next;
  }

  function failRun(submitted: OnboardingFormInput, error: RunError): void {
    stopWatching();
    setInput(submitted);
    dispatch("running", { type: "FAIL" });
    setRunError(error);
  }

  function completeRun(nextResult: OnboardingResult): void {
    stopWatching();
    setResult(nextResult);
    dispatch("running", { type: "COMPLETE" });
  }

  async function executeRun(
    current: RunPhase,
    submitted: OnboardingFormInput,
    event: Extract<RunEvent, { type: "START" } | { type: "RETRY" }>,
  ): Promise<void> {
    stopWatching();
    const generation = (runGenerationRef.current += 1);
    const startedPhase = dispatch(current, event);
    if (startedPhase !== "running") {
      return;
    }
    setLastSubmitted(submitted);
    setRunError(null);
    setValidationError(null);
    try {
      const started = await startRun(submitted);
      if (generation !== runGenerationRef.current) {
        return;
      }
      setRunId(started.runId);
      stopWatchRef.current = watchRunStatus(started.runId, {
        onRunning: () => {
          if (generation !== runGenerationRef.current) {
            return;
          }
          setLastUpdated(new Date().toISOString());
        },
        onDone: (nextResult) => {
          if (generation !== runGenerationRef.current) {
            return;
          }
          completeRun({ ...nextResult, runId: started.runId });
        },
        onError: (error) => {
          if (generation !== runGenerationRef.current) {
            return;
          }
          failRun(submitted, {
            message: `${error.message} ${CREW_STATUS_LABELS.error}.`.trim(),
            violations: error.violations,
          });
        },
        onTimeout: () => {
          if (generation !== runGenerationRef.current) {
            return;
          }
          failRun(submitted, {
            message: `${TIMEOUT_ERROR_MESSAGE}. ${CREW_STATUS_LABELS.error}.`,
            violations: [],
          });
        },
      });
    } catch (caught) {
      if (generation !== runGenerationRef.current) {
        return;
      }
      failRun(
        submitted,
        asRunError(caught, `The run failed. ${CREW_STATUS_LABELS.error}.`),
      );
    }
  }

  function handleRun(): void {
    if (!canRun(phase)) {
      return;
    }
    const nextValidation = validateInputs(input);
    if (nextValidation) {
      setValidationError(nextValidation);
      return;
    }
    void executeRun(phase, trimInput(input), { type: "START" });
  }

  function handleRetry(): void {
    if (!canRetry(phase) || !lastSubmitted) {
      return;
    }
    void executeRun(phase, lastSubmitted, { type: "RETRY" });
  }

  function handleReset(): void {
    if (!canReset(phase)) {
      return;
    }
    runGenerationRef.current += 1;
    stopWatching();
    if (phase !== "idle") {
      dispatch(phase, { type: "RESET" });
    }
    setRunId(null);
    setResult(null);
    setRunError(null);
    setValidationError(null);
    setLastSubmitted(null);
    setInput(EMPTY_INPUT);
  }

  return (
    <div className="page">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <StatusBanner phase={phase} lastUpdated={lastUpdated} />
      <header className="hero">
        <p className="eyebrow">Onboarding plan · wraps CLI core</p>
        <h1>Onboarding plan</h1>
        <p>
          Enter role, department, and start date. The UI calls the existing onboarding
          API and shows the generated Markdown when compliance passes.
        </p>
      </header>
      <main id="main-content" className="layout" tabIndex={-1}>
        <div className="column">
          <InputsSection
            value={input}
            disabled={formDisabled}
            validationError={validationError}
            onChange={setInput}
          />
          <RunSection
            phase={phase}
            runId={runId}
            runError={runError}
            onRun={handleRun}
            onReset={handleReset}
            onRetry={handleRetry}
          />
        </div>
        <div className="column">
          <ResultsSection phase={phase} result={result} />
        </div>
      </main>
    </div>
  );
}
