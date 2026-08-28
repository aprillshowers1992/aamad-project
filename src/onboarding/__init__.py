"""Onboarding workflow package."""

from onboarding.catalog import (
    CatalogLoadError,
    DEFAULT_DEVELOPER_CATALOG_PATH,
    load_developer_catalog,
    load_task_catalog,
)
from onboarding.compliance import check_compliance
from onboarding.workflow import WorkflowResult, run_onboarding
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

__all__ = [
    "CatalogLoadError",
    "ComplianceResult",
    "ComplianceStatus",
    "DEFAULT_DEVELOPER_CATALOG_PATH",
    "OnboardingInput",
    "Plan",
    "Role",
    "RoleAnalysis",
    "Task",
    "TaskCatalog",
    "TaskCategory",
    "check_compliance",
    "run_onboarding",
    "WorkflowResult",
    "load_developer_catalog",
    "load_task_catalog",
]
