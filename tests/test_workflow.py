"""Workflow retry-loop tests. Role Analyst and Plan Builder are stubs — no LLM."""

from datetime import date

from onboarding.models import (
    ComplianceStatus,
    OnboardingInput,
    Plan,
    Role,
    RoleAnalysis,
    Task,
    TaskCatalog,
)
from onboarding.stubs import StubPlanBuilder, StubRoleAnalyst
from onboarding.workflow import (
    MAX_ATTEMPTS,
    READY_TO_WRITE_MESSAGE,
    PlaceholderDocumentWriter,
    restrict_analysis_to_catalog,
    run_onboarding,
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
        ],
    )


def _input() -> OnboardingInput:
    return OnboardingInput(
        role=Role.DEVELOPER,
        department="AI Engineering",
        start_date=date(2026, 9, 1),
    )


class RecordingWriter(PlaceholderDocumentWriter):
    def __init__(self) -> None:
        self.calls = 0

    def write(self, inp, plan, catalog, compliance, *, output_dir):
        self.calls += 1
        return super().write(inp, plan, catalog, compliance, output_dir=output_dir)


def _passing_plan() -> Plan:
    return Plan(day_30=["COMP-001", "IT-001"], day_60=[], day_90=[])


def _failing_plan() -> Plan:
    return Plan(day_30=["IT-001"], day_60=[], day_90=[])


def test_restrict_analysis_drops_invented_ids() -> None:
    analysis = RoleAnalysis(task_ids=["COMP-001", "FAKE-001"])
    restricted = restrict_analysis_to_catalog(analysis, _catalog())
    assert restricted.task_ids == ["COMP-001"]


def test_workflow_pass_runs_writer_once() -> None:
    analyst = StubRoleAnalyst(["COMP-001", "IT-001"])
    builder = StubPlanBuilder([_passing_plan()])
    writer = RecordingWriter()
    result = run_onboarding(
        _input(),
        _catalog(),
        role_analyst=analyst,
        plan_builder=builder,
        document_writer=writer,
    )
    assert result.status is ComplianceStatus.PASS
    assert result.attempts == 1
    assert result.ready_to_write is True
    assert result.message == READY_TO_WRITE_MESSAGE
    assert result.violations == []
    assert analyst.calls == 1
    assert builder.calls == 1
    assert writer.calls == 1


def test_workflow_retries_then_passes() -> None:
    analyst = StubRoleAnalyst(["COMP-001", "IT-001"])
    builder = StubPlanBuilder([_failing_plan(), _passing_plan()])
    writer = RecordingWriter()
    result = run_onboarding(
        _input(),
        _catalog(),
        role_analyst=analyst,
        plan_builder=builder,
        document_writer=writer,
    )
    assert result.status is ComplianceStatus.PASS
    assert result.attempts == 2
    assert analyst.calls == 2
    assert builder.calls == 2
    assert writer.calls == 1


def test_workflow_retry_loop_stops_after_three_forced_failures() -> None:
    analyst = StubRoleAnalyst(["IT-001"])
    builder = StubPlanBuilder([_failing_plan()])
    writer = RecordingWriter()
    result = run_onboarding(
        _input(),
        _catalog(),
        role_analyst=analyst,
        plan_builder=builder,
        document_writer=writer,
        max_attempts=MAX_ATTEMPTS,
    )
    assert result.status is ComplianceStatus.FAIL
    assert result.attempts == MAX_ATTEMPTS
    assert result.ready_to_write is False
    assert "No approved output" in result.message
    assert any("compliance-category" in item for item in result.violations)
    assert analyst.calls == MAX_ATTEMPTS
    assert builder.calls == MAX_ATTEMPTS
    assert writer.calls == 0
