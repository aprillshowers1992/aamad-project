"""CLI tests. Developer crew path is stubbed — no live LLM."""

from unittest.mock import patch

from click.testing import CliRunner

from onboarding.cli import cli
from onboarding.models import ComplianceStatus, Role
from onboarding.workflow import READY_TO_WRITE_MESSAGE, WorkflowResult

_DEV_ARGS = [
    "--role",
    "Developer",
    "--department",
    "AI Engineering",
    "--start-date",
    "2026-09-01",
]


def test_onboard_developer_prints_pass_from_workflow() -> None:
    fake = WorkflowResult(
        status=ComplianceStatus.PASS,
        attempts=1,
        violations=[],
        message=READY_TO_WRITE_MESSAGE,
        ready_to_write=True,
    )
    with patch("onboarding.cli.run_onboarding", return_value=fake) as mocked:
        result = CliRunner().invoke(cli, _DEV_ARGS)
    assert result.exit_code == 0, result.output
    assert '"status": "pass"' in result.output
    assert READY_TO_WRITE_MESSAGE in result.output
    mocked.assert_called_once()


def test_onboard_developer_prints_fail_and_exits_nonzero() -> None:
    fake = WorkflowResult(
        status=ComplianceStatus.FAIL,
        attempts=3,
        violations=["No compliance-category task is present in the plan"],
        message="No approved output. Compliance failed after 3 attempts.",
        ready_to_write=False,
    )
    with patch("onboarding.cli.run_onboarding", return_value=fake):
        result = CliRunner().invoke(cli, _DEV_ARGS)
    assert result.exit_code != 0
    assert '"status": "fail"' in result.output
    assert "No compliance-category task is present in the plan" in result.output
    assert "No approved output" in result.output


def test_onboard_canonical_non_developer_is_not_supported() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "--role",
            Role.ENGINEER.value,
            "--department",
            "AI Engineering",
            "--start-date",
            "2026-09-01",
        ],
    )
    assert result.exit_code != 0
    assert "not yet supported" in result.output
    assert "Developer" in result.output


def test_onboard_rejects_unknown_role() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "--role",
            "Dev",
            "--department",
            "AI Engineering",
            "--start-date",
            "2026-09-01",
        ],
    )
    assert result.exit_code != 0
    assert "UI Designer" in result.output
    assert "Engineer" in result.output


def test_onboard_rejects_invalid_start_date() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "--role",
            "Developer",
            "--department",
            "AI Engineering",
            "--start-date",
            "2026-13-40",
        ],
    )
    assert result.exit_code != 0
    assert "YYYY-MM-DD" in result.output


def test_onboard_rejects_impossible_calendar_date() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "--role",
            "Developer",
            "--department",
            "AI Engineering",
            "--start-date",
            "2026-02-31",
        ],
    )
    assert result.exit_code != 0


def test_onboard_rejects_blank_department() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "--role",
            "Developer",
            "--department",
            "   ",
            "--start-date",
            "2026-09-01",
        ],
    )
    assert result.exit_code != 0
    assert "No files were generated" in result.output
