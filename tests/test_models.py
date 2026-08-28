"""Unit tests for onboarding handoff models. No agent behavior."""

from datetime import date

import pytest
from pydantic import ValidationError

from onboarding.models import (
    ComplianceResult,
    ComplianceStatus,
    OnboardingInput,
    Plan,
    Role,
    RoleAnalysis,
    Task,
    TaskCatalog,
    TaskCategory,
)


def _sample_task(**overrides: object) -> Task:
    payload: dict[str, object] = {
        "id": "COMP-001",
        "title": "Sign employment agreement",
        "description": "Review and sign the offer letter.",
        "category": "compliance",
        "source": "https://intranet.example.com/hr/employment-agreement",
    }
    payload.update(overrides)
    return Task.model_validate(payload)


def test_task_accepts_compact_catalog_shape() -> None:
    task = _sample_task()
    assert task.id == "COMP-001"
    assert task.category is TaskCategory.COMPLIANCE
    assert str(task.source).startswith("https://")


def test_task_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Task.model_validate(
            {
                "id": "COMP-001",
                "title": "Sign employment agreement",
                "description": "Review and sign the offer letter.",
                "category": "compliance",
                "source": "https://intranet.example.com/hr/employment-agreement",
                "extra": True,
            }
        )


def test_task_catalog_rejects_duplicate_ids() -> None:
    with pytest.raises(ValidationError, match="Duplicate task id"):
        TaskCatalog(
            role=Role.DEVELOPER,
            tasks=[_sample_task(), _sample_task()],
        )


def test_onboarding_input_trims_department_and_parses_date() -> None:
    inp = OnboardingInput.model_validate(
        {
            "role": "Developer",
            "department": "  AI Engineering  ",
            "start_date": "2026-09-01",
        }
    )
    assert inp.department == "AI Engineering"
    assert inp.start_date == date(2026, 9, 1)
    assert inp.role is Role.DEVELOPER


def test_onboarding_input_rejects_blank_department() -> None:
    with pytest.raises(ValidationError):
        OnboardingInput.model_validate(
            {"role": "Developer", "department": "   ", "start_date": "2026-09-01"}
        )


def test_onboarding_input_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        OnboardingInput.model_validate(
            {"role": "Dev", "department": "AI Engineering", "start_date": "2026-09-01"}
        )


def test_role_analysis_is_id_list() -> None:
    analysis = RoleAnalysis(task_ids=["COMP-001", "IT-001"])
    assert analysis.task_ids == ["COMP-001", "IT-001"]


def test_plan_keeps_bucket_sequence_and_rejects_overlap() -> None:
    plan = Plan(day_30=["COMP-001", "IT-001"], day_60=["ROLE-001"], day_90=["TEAM-001"])
    assert plan.all_task_ids() == ["COMP-001", "IT-001", "ROLE-001", "TEAM-001"]
    with pytest.raises(ValidationError, match="more than one bucket"):
        Plan(day_30=["COMP-001"], day_60=["COMP-001"])


def test_compliance_pass_forbids_violations() -> None:
    result = ComplianceResult(status=ComplianceStatus.PASS, violations=[])
    assert result.passed is True
    with pytest.raises(ValidationError, match="empty violations"):
        ComplianceResult(status="pass", violations=["missing mandatory task"])


def test_compliance_fail_requires_violations() -> None:
    result = ComplianceResult(
        status="fail",
        violations=["Missing mandatory compliance task COMP-001"],
    )
    assert result.passed is False
    with pytest.raises(ValidationError, match="at least one violation"):
        ComplianceResult(status="fail", violations=[])
