"""Deterministic Role Analyst / Plan Builder stubs (OQ-13). No live LLM."""

from __future__ import annotations

from onboarding.catalog import load_developer_catalog
from onboarding.models import Plan, RoleAnalysis, TaskCatalog, TaskCategory


class StubRoleAnalyst:
    def __init__(self, task_ids: list[str]) -> None:
        self.task_ids = task_ids
        self.calls = 0

    def analyze(self, inp, catalog, *, attempt, max_attempts, previous_violations):
        del inp, catalog, attempt, max_attempts, previous_violations
        self.calls += 1
        return RoleAnalysis(task_ids=list(self.task_ids))


class StubPlanBuilder:
    def __init__(self, plans: list[Plan]) -> None:
        self.plans = plans
        self.calls = 0

    def build(self, analysis, catalog, *, attempt, max_attempts, previous_violations):
        del analysis, catalog, attempt, max_attempts, previous_violations
        plan = self.plans[min(self.calls, len(self.plans) - 1)]
        self.calls += 1
        return plan


def passing_plan_from_catalog(catalog: TaskCatalog) -> Plan:
    """Catalog IDs only, split across 30/60/90. Always includes compliance tasks."""
    by_category: dict[TaskCategory, list[str]] = {category: [] for category in TaskCategory}
    for task in catalog.tasks:
        by_category[task.category].append(task.id)
    return Plan(
        day_30=by_category[TaskCategory.COMPLIANCE] + by_category[TaskCategory.IT_SETUP],
        day_60=by_category[TaskCategory.ROLE_WORK],
        day_90=by_category[TaskCategory.TEAM_INTRO],
    )


def stub_agents_for_catalog(
    catalog: TaskCatalog | None = None,
) -> tuple[StubRoleAnalyst, StubPlanBuilder]:
    """Same stub pair used by CLI e2e tests: real Developer catalog, no LLM."""
    resolved = catalog or load_developer_catalog()
    plan = passing_plan_from_catalog(resolved)
    return StubRoleAnalyst(list(plan.all_task_ids())), StubPlanBuilder([plan])
