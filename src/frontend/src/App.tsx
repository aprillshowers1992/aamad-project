import { useEffect, useMemo, useRef, useState } from "react";
import { HistorySection } from "./components/HistorySection";
import { InputsSection, validateInputs } from "./components/InputsSection";
import { ResultsSection } from "./components/ResultsSection";
import { RunSection } from "./components/RunSection";
import { StatusBanner } from "./components/StatusBanner";
import { canReset, canRetry, canRun, nextPhase, type RunEvent } from "./fsm/runMachine";
import { startRun, watchRunStatus } from "./services/runService";
import { CREW_STATUS_LABELS, type RunPhase } from "./statusLabels";
import type { HistoryEntry, ResearchInput, ResearchResult } from "./types";

const EMPTY_INPUT: ResearchInput = {
  question: "",
  domain: "general",
  scope: "",
};

const SEEDED_HISTORY: HistoryEntry = {
  runId: "run-mock-seed",
  question: "What constraints should a critical-research run record for later audit?",
  domain: "general",
  completedAt: "2026-08-23T00:00:00.000Z",
  status: "done",
};

const TIMEOUT_ERROR_MESSAGE = "This is taking longer than expected";

function trimInput(input: ResearchInput): ResearchInput {
  return {
    question: input.question.trim(),
    domain: input.domain,
    scope: input.scope.trim(),
  };
}

export default function App() {
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [lastUpdated, setLastUpdated] = useState(() => new Date().toISOString());
  const [input, setInput] = useState<ResearchInput>(EMPTY_INPUT);
  const [lastSubmitted, setLastSubmitted] = useState<ResearchInput | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([SEEDED_HISTORY]);
  const stopWatchRef = useRef<(() => void) | null>(null);
  const runGenerationRef = useRef(0);

  const formDisabled = phase === "running" || phase === "error";

  const activeRunId = useMemo(() => {
    if (phase === "done" && result) {
      return result.runId;
    }
    return runId;
  }, [phase, result, runId]);

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

  function failRun(submitted: ResearchInput, message: string): void {
    stopWatching();
    setInput(submitted);
    dispatch("running", { type: "FAIL" });
    setRunError(message);
  }

  function completeRun(nextResult: ResearchResult): void {
    stopWatching();
    setResult(nextResult);
    setHistory((entries) => [
      {
        runId: nextResult.runId,
        question: nextResult.question,
        domain: nextResult.domain,
        completedAt: nextResult.completedAt,
        status: "done",
      },
      ...entries,
    ]);
    dispatch("running", { type: "COMPLETE" });
  }

  async function executeRun(
    current: RunPhase,
    submitted: ResearchInput,
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
          completeRun(nextResult);
        },
        onError: (message) => {
          if (generation !== runGenerationRef.current) {
            return;
          }
          failRun(
            submitted,
            `${message} ${CREW_STATUS_LABELS.error}.`.trim(),
          );
        },
        onTimeout: () => {
          if (generation !== runGenerationRef.current) {
            return;
          }
          failRun(
            submitted,
            `${TIMEOUT_ERROR_MESSAGE}. ${CREW_STATUS_LABELS.error}.`,
          );
        },
      });
    } catch {
      if (generation !== runGenerationRef.current) {
        return;
      }
      failRun(submitted, `The run failed. ${CREW_STATUS_LABELS.error}.`);
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
        <p className="eyebrow">Prototype · stub services only</p>
        <h1>Critical Research Workflow</h1>
        <p>
          Single route. Enter a question, start a mocked run, then review results and
          session history.
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
          <HistorySection entries={history} activeRunId={activeRunId} />
        </div>
      </main>
    </div>
  );
}
