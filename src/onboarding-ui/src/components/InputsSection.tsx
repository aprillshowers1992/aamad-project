import {
  CANONICAL_DEPARTMENTS,
  CANONICAL_ROLES,
  CATALOG_ROLE,
  type CanonicalDepartment,
  type CanonicalRole,
  type OnboardingFormInput,
} from "../types";

interface InputsSectionProps {
  value: OnboardingFormInput;
  disabled: boolean;
  validationError: string | null;
  onChange: (next: OnboardingFormInput) => void;
}

export function unsupportedRoleMessage(role: CanonicalRole): string {
  return (
    `Role '${role}' is not yet supported. ` +
    `Only ${CATALOG_ROLE} has a task catalog. ` +
    "No files were generated."
  );
}

export function validateInputs(input: OnboardingFormInput): string | null {
  if (!CANONICAL_ROLES.includes(input.role)) {
    return "Role must be one of the listed values.";
  }
  if (input.role !== CATALOG_ROLE) {
    return unsupportedRoleMessage(input.role);
  }
  if (
    !CANONICAL_DEPARTMENTS.includes(input.department as CanonicalDepartment)
  ) {
    return "Department must be one of the listed values.";
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input.startDate)) {
    return "Start date must be a valid calendar date in YYYY-MM-DD format.";
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
        Generate a 30/60/90-day plan. Only {CATALOG_ROLE} has a catalog in this MVP.
      </p>
      <div className="stack">
        <label className="field" htmlFor="onboarding-role">
          <span>Role</span>
          <select
            id="onboarding-role"
            name="role"
            disabled={disabled}
            value={value.role}
            onChange={(event) =>
              onChange({
                ...value,
                role: event.target.value as CanonicalRole,
              })
            }
          >
            {CANONICAL_ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>
        <label className="field" htmlFor="onboarding-department">
          <span>Department</span>
          <select
            id="onboarding-department"
            name="department"
            required
            disabled={disabled}
            value={value.department}
            aria-invalid={validationError ? true : undefined}
            onChange={(event) =>
              onChange({
                ...value,
                department: event.target.value as CanonicalDepartment | "",
              })
            }
          >
            <option value="">Select department</option>
            {CANONICAL_DEPARTMENTS.map((department) => (
              <option key={department} value={department}>
                {department}
              </option>
            ))}
          </select>
        </label>
        <label className="field" htmlFor="onboarding-start-date">
          <span>Start date</span>
          <input
            id="onboarding-start-date"
            name="startDate"
            type="date"
            required
            disabled={disabled}
            value={value.startDate}
            onChange={(event) =>
              onChange({ ...value, startDate: event.target.value })
            }
          />
        </label>
        {value.role !== CATALOG_ROLE ? (
          <p id="inputs-error" className="error" role="alert">
            {unsupportedRoleMessage(value.role)}
          </p>
        ) : validationError ? (
          <p id="inputs-error" className="error" role="alert">
            {validationError}
          </p>
        ) : null}
      </div>
    </section>
  );
}
