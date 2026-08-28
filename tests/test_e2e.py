"""End-to-end CLI tests. Role Analyst and Plan Builder are stubs — no live LLM (OQ-13)."""

from pathlib import Path

from click.testing import CliRunner

from onboarding.catalog import load_developer_catalog
from onboarding.models import Plan, TaskCatalog
from onboarding.cli import cli
from onboarding.compliance import check_compliance
from onboarding.rendering import (
    APPENDIX_HEADING,
    CHECKLIST_FILENAME,
    PLAN_FILENAME,
    split_markdown,
)
from onboarding.stubs import (
    StubPlanBuilder,
    StubRoleAnalyst,
    passing_plan_from_catalog,
)

_DEV_ARGS = [
    "--role",
    "Developer",
    "--department",
    "AI Engineering",
    "--start-date",
    "2026-09-01",
]


def _install_stubs(monkeypatch, catalog: TaskCatalog) -> Plan:
    plan = passing_plan_from_catalog(catalog)
    monkeypatch.setattr(
        "onboarding.crew_runtime.build_llm_agents",
        lambda: (
            StubRoleAnalyst(list(plan.all_task_ids())),
            StubPlanBuilder([plan]),
        ),
    )
    return plan


def _appendix_task_ids(appendix: str) -> list[str]:
    ids: list[str] = []
    for line in appendix.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Order", "-----"}:
            continue
        ids.append(cells[1])
    return ids


def _assert_output_traces_to_catalog(
    plan: Plan,
    catalog: TaskCatalog,
    markdown: str,
) -> None:
    catalog_ids = set(catalog.task_ids())
    titles_by_id = {task.id: task.title for task in catalog.tasks}
    body, appendix = split_markdown(markdown)
    assert APPENDIX_HEADING in markdown

    for task_id in plan.all_task_ids():
        assert task_id in catalog_ids
        assert task_id in appendix
        assert task_id not in body

    appendix_ids = _appendix_task_ids(appendix)
    assert appendix_ids == plan.all_task_ids()
    assert set(appendix_ids) <= catalog_ids

    result = check_compliance(
        plan,
        catalog,
        body_text=body,
        appendix_text=appendix,
    )
    assert result.passed, result.violations
    assert result.violations == []

    for task_id in plan.all_task_ids():
        assert titles_by_id[task_id] in body


def test_e2e_happy_path_developer_cli(tmp_path: Path, monkeypatch) -> None:
    catalog = load_developer_catalog()
    plan = _install_stubs(monkeypatch, catalog)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(cli, _DEV_ARGS)

    assert result.exit_code == 0, result.output
    plan_path = Path("output") / PLAN_FILENAME
    checklist_path = Path("output") / CHECKLIST_FILENAME
    assert plan_path.is_file()
    assert checklist_path.is_file()

    plan_md = plan_path.read_text(encoding="utf-8")
    checklist_md = checklist_path.read_text(encoding="utf-8")
    _assert_output_traces_to_catalog(plan, catalog, plan_md)
    _assert_output_traces_to_catalog(plan, catalog, checklist_md)

    expected_titles = [task.title for task in catalog.tasks if task.id in set(plan.all_task_ids())]
    checklist_body, _ = split_markdown(checklist_md)
    checklist_titles = [
        line[len("- [ ] ") :]
        for line in checklist_body.splitlines()
        if line.startswith("- [ ] ")
    ]
    assert checklist_titles == [
        next(task.title for task in catalog.tasks if task.id == task_id)
        for task_id in plan.all_task_ids()
    ]
    assert set(checklist_titles) <= set(expected_titles)


def test_e2e_bad_input_unknown_role_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "--role",
            "Researcher",
            "--department",
            "AI Engineering",
            "--start-date",
            "2026-09-01",
        ],
    )

    assert result.exit_code != 0
    assert "must be one of" in result.output
    assert "No files were generated" in result.output
    output_dir = Path("output")
    assert not output_dir.exists()
    assert not (output_dir / PLAN_FILENAME).exists()
    assert not (output_dir / CHECKLIST_FILENAME).exists()
