"""Deterministic Compliance Checker. No LLM — hard-coded rules only."""

from __future__ import annotations

import re

from onboarding.models import (
    ComplianceResult,
    ComplianceStatus,
    Plan,
    Task,
    TaskCatalog,
    TaskCategory,
)

VALID_BUCKETS = ("day_30", "day_60", "day_90")


def check_compliance(
    plan: Plan,
    catalog: TaskCatalog,
    *,
    body_text: str = "",
    appendix_text: str = "",
) -> ComplianceResult:
    """Validate ``plan`` against ``catalog`` and optional rendered Markdown.

    ``body_text`` is the visible plan/checklist body. ``appendix_text`` is the
    audit appendix, where task IDs are allowed. Neither argument changes the
    Plan/TaskCatalog models.
    """
    del appendix_text  # IDs may appear here; only body_text is scanned for leaks.
    violations: list[str] = []
    catalog_ids = set(catalog.task_ids())
    tasks_by_id = {task.id: task for task in catalog.tasks}
    plan_ids = plan.all_task_ids()

    violations.extend(_invented_task_violations(plan_ids, catalog_ids))
    violations.extend(_compliance_coverage_violations(plan_ids, tasks_by_id))
    violations.extend(_bucket_violations(plan))
    violations.extend(_id_leak_violations(plan_ids, catalog_ids, body_text))

    if violations:
        return ComplianceResult(status=ComplianceStatus.FAIL, violations=violations)
    return ComplianceResult(status=ComplianceStatus.PASS, violations=[])


def _invented_task_violations(plan_ids: list[str], catalog_ids: set[str]) -> list[str]:
    unknown = sorted({task_id for task_id in plan_ids if task_id not in catalog_ids})
    return [f"Invented task id not in catalog: {task_id}" for task_id in unknown]


def _compliance_coverage_violations(
    plan_ids: list[str],
    tasks_by_id: dict[str, Task],
) -> list[str]:
    for task_id in plan_ids:
        task = tasks_by_id.get(task_id)
        if task is not None and task.category is TaskCategory.COMPLIANCE:
            return []
    return ["No compliance-category task is present in the plan"]


def _bucket_violations(plan: Plan) -> list[str]:
    membership: dict[str, list[str]] = {}
    for bucket in VALID_BUCKETS:
        for task_id in getattr(plan, bucket):
            membership.setdefault(task_id, []).append(bucket)
    violations: list[str] = []
    for task_id, buckets in sorted(membership.items()):
        if len(buckets) != 1:
            violations.append(
                f"Task id {task_id} is not assigned to exactly one of "
                f"day_30, day_60, or day_90"
            )
    return violations


def _id_leak_violations(
    plan_ids: list[str],
    catalog_ids: set[str],
    body_text: str,
) -> list[str]:
    if not body_text:
        return []
    ids_to_scan = sorted(set(plan_ids) | catalog_ids)
    leaks: list[str] = []
    for task_id in ids_to_scan:
        if _id_appears_in_text(task_id, body_text):
            leaks.append(
                f"Task id {task_id} appears in plan body text; "
                "IDs are allowed only in the audit appendix"
            )
    return leaks


def _id_appears_in_text(task_id: str, text: str) -> bool:
    pattern = rf"(?<![\w-]){re.escape(task_id)}(?![\w-])"
    return re.search(pattern, text) is not None
