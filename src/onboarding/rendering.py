"""Render approved plans to Markdown. Task IDs appear only in Audit Appendix."""

from __future__ import annotations

from pathlib import Path

from onboarding.compliance import check_compliance
from onboarding.models import (
    ComplianceResult,
    OnboardingInput,
    Plan,
    Task,
    TaskCatalog,
)

APPENDIX_HEADING = "## Audit Appendix"
PLAN_FILENAME = "onboarding-plan.md"
CHECKLIST_FILENAME = "manager-checklist.md"
BUCKET_HEADINGS = (
    ("day_30", "30-day"),
    ("day_60", "60-day"),
    ("day_90", "90-day"),
)


class DocumentWriteError(RuntimeError):
    """Rendered Markdown failed the ID-leak check; no files were written."""


def split_markdown(text: str) -> tuple[str, str]:
    """Split a rendered document into visible body and audit appendix."""
    marker = APPENDIX_HEADING
    if marker not in text:
        return text, ""
    body, appendix = text.split(marker, 1)
    return body, f"{marker}{appendix}"


def render_onboarding_plan(inp: OnboardingInput, plan: Plan, catalog: TaskCatalog) -> str:
    lines = [
        "# Onboarding plan",
        "",
        f"- Role: {inp.role.value}",
        f"- Department: {inp.department}",
        f"- Start date: {inp.start_date.isoformat()}",
        "",
    ]
    for field, heading in BUCKET_HEADINGS:
        lines.append(f"## {heading}")
        lines.append("")
        task_ids = getattr(plan, field)
        if not task_ids:
            lines.append("No tasks scheduled in this window.")
            lines.append("")
            continue
        for task_id in task_ids:
            task = _require_task(catalog, task_id)
            lines.extend(
                [
                    f"### {task.title}",
                    "",
                    f"Category: {task.category.value}",
                    f"Source: {task.source}",
                    "",
                    task.description,
                    "",
                ]
            )
    lines.append(_render_appendix(plan, catalog))
    return "\n".join(lines).rstrip() + "\n"


def render_manager_checklist(inp: OnboardingInput, plan: Plan, catalog: TaskCatalog) -> str:
    lines = [
        "# Manager checklist",
        "",
        f"- Role: {inp.role.value}",
        f"- Department: {inp.department}",
        f"- Start date: {inp.start_date.isoformat()}",
        "",
    ]
    for field, heading in BUCKET_HEADINGS:
        lines.append(f"## {heading}")
        lines.append("")
        task_ids = getattr(plan, field)
        if not task_ids:
            lines.append("No tasks scheduled in this window.")
            lines.append("")
            continue
        for task_id in task_ids:
            task = _require_task(catalog, task_id)
            lines.append(f"- [ ] {task.title}")
        lines.append("")
    lines.append(_render_appendix(plan, catalog))
    return "\n".join(lines).rstrip() + "\n"


def _render_appendix(plan: Plan, catalog: TaskCatalog) -> str:
    rows = [
        APPENDIX_HEADING,
        "",
        "Task IDs are listed here for traceability only.",
        "",
        "| Order | Task ID | Title | Category |",
        "| ----- | ------- | ----- | -------- |",
    ]
    for index, task_id in enumerate(plan.all_task_ids(), start=1):
        task = _require_task(catalog, task_id)
        title = task.title.replace("|", "\\|")
        rows.append(
            f"| {index} | {task.id} | {title} | {task.category.value} |"
        )
    rows.append("")
    return "\n".join(rows)


def _require_task(catalog: TaskCatalog, task_id: str) -> Task:
    for task in catalog.tasks:
        if task.id == task_id:
            return task
    raise DocumentWriteError(f"Cannot render unknown task id {task_id}")


class MarkdownDocumentWriter:
    """Write onboarding-plan.md and manager-checklist.md after compliance PASS."""

    def write(
        self,
        inp: OnboardingInput,
        plan: Plan,
        catalog: TaskCatalog,
        compliance: ComplianceResult,
        *,
        output_dir: Path,
    ) -> list[Path]:
        if not compliance.passed:
            raise DocumentWriteError("Document Writer requires compliance PASS.")
        plan_md = render_onboarding_plan(inp, plan, catalog)
        checklist_md = render_manager_checklist(inp, plan, catalog)
        _assert_no_id_leak(plan, catalog, plan_md)
        _assert_no_id_leak(plan, catalog, checklist_md)
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_path = output_dir / PLAN_FILENAME
        checklist_path = output_dir / CHECKLIST_FILENAME
        plan_path.write_text(plan_md, encoding="utf-8")
        checklist_path.write_text(checklist_md, encoding="utf-8")
        return [plan_path, checklist_path]


def _assert_no_id_leak(plan: Plan, catalog: TaskCatalog, markdown: str) -> None:
    body, appendix = split_markdown(markdown)
    result = check_compliance(
        plan,
        catalog,
        body_text=body,
        appendix_text=appendix,
    )
    leaks = [item for item in result.violations if "plan body text" in item]
    if leaks:
        raise DocumentWriteError("; ".join(leaks))
