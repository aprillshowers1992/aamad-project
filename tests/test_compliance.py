"""Deterministic compliance checker tests. No LLM."""

from onboarding.compliance import check_compliance
from onboarding.models import (
    ComplianceStatus,
    Plan,
    Role,
    Task,
    TaskCatalog,
)


def _task(task_id: str, category: str) -> Task:
    return Task.model_validate(
        {
            "id": task_id,
            "title": f"Title {task_id}",
            "description": f"Description {task_id}",
            "category": category,
            "source": f"https://intranet.example.com/{task_id.lower()}",
        }
    )


def _catalog() -> TaskCatalog:
    return TaskCatalog(
        role=Role.DEVELOPER,
        tasks=[
            _task("COMP-001", "compliance"),
            _task("IT-001", "it_setup"),
            _task("ROLE-001", "role_work"),
        ],
    )


def _valid_plan() -> Plan:
    return Plan(
        day_30=["COMP-001", "IT-001"],
        day_60=["ROLE-001"],
        day_90=[],
    )


def test_check_compliance_passes_valid_plan() -> None:
    result = check_compliance(
        _valid_plan(),
        _catalog(),
        body_text="Complete laptop setup and sign the employment agreement.",
        appendix_text="Audit: COMP-001, IT-001, ROLE-001",
    )
    assert result.status is ComplianceStatus.PASS
    assert result.passed is True
    assert result.violations == []


def test_check_compliance_fails_invented_task_id() -> None:
    plan = Plan(day_30=["COMP-001", "FAKE-001"], day_60=[], day_90=[])
    result = check_compliance(plan, _catalog())
    assert result.status is ComplianceStatus.FAIL
    assert any("Invented task id not in catalog: FAKE-001" in item for item in result.violations)


def test_check_compliance_fails_without_compliance_task() -> None:
    plan = Plan(day_30=["IT-001"], day_60=["ROLE-001"], day_90=[])
    result = check_compliance(plan, _catalog())
    assert result.status is ComplianceStatus.FAIL
    assert "No compliance-category task is present in the plan" in result.violations


def test_check_compliance_fails_invalid_bucket_assignment() -> None:
    plan = Plan.model_construct(
        day_30=["COMP-001"],
        day_60=["COMP-001"],
        day_90=[],
    )
    result = check_compliance(plan, _catalog())
    assert result.status is ComplianceStatus.FAIL
    assert any(
        "Task id COMP-001 is not assigned to exactly one of day_30, day_60, or day_90"
        in item
        for item in result.violations
    )


def test_check_compliance_fails_task_id_in_body_text() -> None:
    result = check_compliance(
        _valid_plan(),
        _catalog(),
        body_text="New hires must complete COMP-001 in week one.",
        appendix_text="Audit appendix may list COMP-001",
    )
    assert result.status is ComplianceStatus.FAIL
    assert any(
        "Task id COMP-001 appears in plan body text" in item
        for item in result.violations
    )
