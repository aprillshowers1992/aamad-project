import { RESEARCH_DOMAINS, type ResearchDomain, type ResearchInput } from "../types";

const QUESTION_MIN = 8;
const SCOPE_MAX = 500;

interface InputsSectionProps {
  value: ResearchInput;
  disabled: boolean;
  validationError: string | null;
  onChange: (next: ResearchInput) => void;
}

export function validateInputs(input: ResearchInput): string | null {
  const question = input.question.trim();
  if (question.length < QUESTION_MIN) {
    return `Question must be at least ${QUESTION_MIN} characters after trim.`;
  }
  if (!RESEARCH_DOMAINS.includes(input.domain)) {
    return "Domain must be one of the listed values.";
  }
  if (input.scope.trim().length > SCOPE_MAX) {
    return `Scope must be at most ${SCOPE_MAX} characters.`;
  }
  return null;
}

export function InputsSection({
  value,
  disabled,
  validationError,
  onChange,
}: InputsSectionProps) {
  return (
    <section className="panel" aria-labelledby="inputs-heading">
      <h2 id="inputs-heading">Inputs</h2>
      <p className="lede">
        Submit a research question. The run stays on this page; nothing is sent to a
        backend.
      </p>
      <div className="stack">
        <label className="field" htmlFor="research-question">
          <span>Research question</span>
          <textarea
            id="research-question"
            name="question"
            rows={3}
            required
            minLength={QUESTION_MIN}
            disabled={disabled}
            value={value.question}
            aria-invalid={validationError ? true : undefined}
            aria-describedby={validationError ? "question-error" : undefined}
            onChange={(event) =>
              onChange({ ...value, question: event.target.value })
            }
          />
        </label>
        <label className="field" htmlFor="research-domain">
          <span>Domain</span>
          <select
            id="research-domain"
            name="domain"
            disabled={disabled}
            value={value.domain}
            onChange={(event) =>
              onChange({
                ...value,
                domain: event.target.value as ResearchDomain,
              })
            }
          >
            {RESEARCH_DOMAINS.map((domain) => (
              <option key={domain} value={domain}>
                {domain}
              </option>
            ))}
          </select>
        </label>
        <label className="field" htmlFor="research-scope">
          <span>Scope (optional)</span>
          <textarea
            id="research-scope"
            name="scope"
            rows={2}
            maxLength={SCOPE_MAX}
            disabled={disabled}
            value={value.scope}
            onChange={(event) => onChange({ ...value, scope: event.target.value })}
          />
        </label>
        {validationError ? (
          <p id="question-error" className="error">
            {validationError}
          </p>
        ) : null}
      </div>
    </section>
  );
}
