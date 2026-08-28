"""CLI entrypoint ``onboard`` (SAD SD-6). Writes Markdown only after compliance PASS."""

from __future__ import annotations

from datetime import date

import click

from onboarding.crew_runtime import load_project_dotenv
from onboarding.models import OnboardingInput, Role
from onboarding.workflow import WorkflowResult, run_onboarding

_ROLE_CHOICES = tuple(role.value for role in Role)
_ROLE_LIST = ", ".join(_ROLE_CHOICES)
_CATALOG_ROLE = Role.DEVELOPER


def _parse_start_date(_ctx: click.Context, _param: click.Parameter, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise click.BadParameter(
            "must be a valid calendar date in YYYY-MM-DD format. "
            "No files were generated."
        ) from exc


def _parse_role(_ctx: click.Context, _param: click.Parameter, value: str) -> Role:
    try:
        return Role(value)
    except ValueError as exc:
        raise click.BadParameter(
            f"must be one of: {_ROLE_LIST}. No files were generated."
        ) from exc


@click.command(name="onboard")
@click.option(
    "--role",
    required=True,
    callback=_parse_role,
    help=f"Canonical role. One of: {_ROLE_LIST}.",
)
@click.option(
    "--department",
    required=True,
    help="Department name (metadata only in MVP).",
)
@click.option(
    "--start-date",
    required=True,
    callback=_parse_start_date,
    help="Employee start date as YYYY-MM-DD.",
)
def cli(role: Role, department: str, start_date: date) -> None:
    """Validate inputs, load the Developer catalog, run the crew, print PASS/FAIL."""
    try:
        payload = OnboardingInput(
            role=role,
            department=department,
            start_date=start_date,
        )
    except ValueError as exc:
        raise click.ClickException(f"{exc} No files were generated.") from exc

    if payload.role is not _CATALOG_ROLE:
        raise click.ClickException(
            f"Role {payload.role.value!r} is not yet supported. "
            f"Only {_CATALOG_ROLE.value} has a task catalog. "
            "No files were generated."
        )

    try:
        result = run_onboarding(payload)
    except Exception as exc:
        raise click.ClickException(f"{exc} No files were generated.") from exc

    click.echo(_format_result(result))
    if not result.ready_to_write:
        raise SystemExit(1)


def _format_result(result: WorkflowResult) -> str:
    return result.model_dump_json(indent=2, exclude={"plan"})


def main() -> None:
    load_project_dotenv()
    cli()


if __name__ == "__main__":
    main()
