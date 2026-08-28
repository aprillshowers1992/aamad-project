"""Document Writer Markdown tests. ID-leak checks call check_compliance."""

from datetime import date
from pathlib import Path

import pytest

from onboarding.compliance import check_compliance
from onboarding.models import (
    ComplianceResult,
    ComplianceStatus,
    OnboardingInput,
    Plan,
    Role,
    RoleAnalysis,
    Task,
    TaskCatalog,
)
from onboarding.rendering import (
    APPENDIX_HEADING,
    CHECKLIST_FILENAME,
    PLAN_FILENAME,
    DocumentWriteError,
    MarkdownDocumentWriter,
    split_markdown,
)
from onboarding.workflow import (
    MAX_ATTEMPTS,
    PlaceholderDocumentWriter,
    run_onboarding,
)


def _task(task_id: str, title: str, description: str, category: str) -> Task:
    return Task.model_validate(
        {
            "id": task_id,
            "title": title,
            "description": description,
            "category": category,
            "source": "https://intranet.example.com/onboarding/tasks",
        }
    )


def _catalog() -> TaskCatalog:
    return TaskCatalog(
        role=Role.DEVELOPER,
        tasks=[
            _task(
                "COMP-001",
                "Sign employment agreement",
                "Review and sign the offer letter.",
                "compliance",
            ),
            _task(
                "IT-001",
                "Set up laptop",
                "Receive a company laptop and complete initial setup.",
                "it_setup",
            ),
            _task(
                "ROLE-001",
                "Clone the main repo",
                "Get the local development environment running.",
                "role_work",
            ),
        ],
    )


def _input() -> OnboardingInput:
    return OnboardingInput(
        role=Role.DEVELOPER,
        department="AI Engineering",
        start_date=date(2026, 9, 1),
    )


def _passing_plan() -> Plan:
    return Plan(
        day_30=["COMP-001", "IT-001"],
        day_60=["ROLE-001"],
        day_90=[],
    )


def _failing_plan() -> Plan:
    return Plan(day_30=["IT-001"], day_60=[], day_90=[])


def _pass_result() -> ComplianceResult:
    return ComplianceResult(status=ComplianceStatus.PASS, violations=[])


def _assert_body_has_no_id_leaks(plan: Plan, catalog: TaskCatalog, markdown: str) -> None:
    body, appendix = split_markdown(markdown)
    assert APPENDIX_HEADING in markdown
    assert appendix.startswith(APPENDIX_HEADING)
    for task_id in plan.all_task_ids():
        assert task_id in appendix
        assert task_id not in body
    result = check_compliance(
        plan,
        catalog,
        body_text=body,
        appendix_text=appendix,
    )
    assert result.status is ComplianceStatus.PASS, result.violations
    assert result.violations == []


class Analyst:
    def __init__(self, task_ids: list[str]) -> None:
        self.task_ids = task_ids

    def analyze(self, inp, catalog, *, attempt, max_attempts, previous_violations):
        del inp, catalog, attempt, max_attempts, previous_violations
        return RoleAnalysis(task_ids=list(self.task_ids))


class Builder:
    def __init__(self, plans: list[Plan]) -> None:
        self.plans = plans
        self.calls = 0

    def build(self, analysis, catalog, *, attempt, max_attempts, previous_violations):
        del analysis, catalog, attempt, max_attempts, previous_violations
        plan = self.plans[min(self.calls, len(self.plans) - 1)]
        self.calls += 1
        return plan


def test_pass_writes_two_markdown_files_with_ids_only_in_appendix(tmp_path: Path) -> None:
    catalog = _catalog()
    plan = _passing_plan()
    result = run_onboarding(
        _input(),
        catalog,
        role_analyst=Analyst(["COMP-001", "IT-001", "ROLE-001"]),
        plan_builder=Builder([plan]),
        output_dir=tmp_path,
    )
    assert result.status is ComplianceStatus.PASS
    plan_path = tmp_path / PLAN_FILENAME
    checklist_path = tmp_path / CHECKLIST_FILENAME
    assert plan_path.is_file()
    assert checklist_path.is_file()
    assert sorted(result.output_files) == sorted([str(plan_path), str(checklist_path)])

    plan_md = plan_path.read_text(encoding="utf-8")
    checklist_md = checklist_path.read_text(encoding="utf-8")
    _assert_body_has_no_id_leaks(plan, catalog, plan_md)
    _assert_body_has_no_id_leaks(plan, catalog, checklist_md)

    assert "Sign employment agreement" in plan_md
    assert "Review and sign the offer letter." in plan_md
    assert "Set up laptop" in plan_md
    assert "Clone the main repo" in plan_md
    assert "## 30-day" in plan_md
    assert "## 60-day" in plan_md
    assert "## 90-day" in plan_md
    assert "- [ ] Sign employment agreement" in checklist_md
    assert "- [ ] Set up laptop" in checklist_md
    assert "- [ ] Clone the main repo" in checklist_md
    assert "COMP-001" not in plan_md.split(APPENDIX_HEADING, 1)[0]
    assert "IT-001" not in checklist_md.split(APPENDIX_HEADING, 1)[0]


def test_fail_does_not_write_any_files(tmp_path: Path) -> None:
    catalog = _catalog()
    result = run_onboarding(
        _input(),
        catalog,
        role_analyst=Analyst(["IT-001"]),
        plan_builder=Builder([_failing_plan()]),
        max_attempts=MAX_ATTEMPTS,
        output_dir=tmp_path,
    )
    assert result.status is ComplianceStatus.FAIL
    assert result.ready_to_write is False
    assert result.output_files == []
    assert "No approved output" in result.message
    assert list(tmp_path.iterdir()) == []


def test_writer_refuses_fail_compliance_and_writes_nothing(tmp_path: Path) -> None:
    writer = MarkdownDocumentWriter()
    with pytest.raises(DocumentWriteError, match="requires compliance PASS"):
        writer.write(
            _input(),
            _passing_plan(),
            _catalog(),
            ComplianceResult(
                status=ComplianceStatus.FAIL,
                violations=["No compliance-category task is present in the plan"],
            ),
            output_dir=tmp_path,
        )
    assert list(tmp_path.iterdir()) == []


def test_placeholder_writer_does_not_create_files(tmp_path: Path) -> None:
    paths = PlaceholderDocumentWriter().write(
        _input(),
        _passing_plan(),
        _catalog(),
        _pass_result(),
        output_dir=tmp_path,
    )
    assert paths == []
    assert list(tmp_path.iterdir()) == []


def test_title_containing_task_id_is_rejected_before_write(tmp_path: Path) -> None:
    catalog = TaskCatalog(
        role=Role.DEVELOPER,
        tasks=[
            _task(
                "COMP-001",
                "Complete COMP-001 paperwork",
                "Sign the offer letter.",
                "compliance",
            ),
        ],
    )
    plan = Plan(day_30=["COMP-001"], day_60=[], day_90=[])
    with pytest.raises(DocumentWriteError, match="plan body text"):
        MarkdownDocumentWriter().write(
            _input(),
            plan,
            catalog,
            _pass_result(),
            output_dir=tmp_path,
        )
    assert list(tmp_path.iterdir()) == []
