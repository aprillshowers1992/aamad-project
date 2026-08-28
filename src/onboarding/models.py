"""Pydantic v2 handoff schemas for the onboarding-plan workflow.

These shapes match the compact catalog (`id`, `category`, `source`) and the
four-agent sequence. No agent logic lives here.

Handoff map (SAD §2.2, simplified to this operator schema):

- CLI → Role Analyst: ``OnboardingInput``
- Role Analyst → Plan Builder: ``RoleAnalysis`` (task IDs only)
- Plan Builder → Compliance Checker: ``Plan`` (IDs in 30/60/90 buckets)
- Compliance Checker → Document Writer (on pass): ``ComplianceResult`` + ``Plan``

Unknown fields are rejected. Titles and descriptions stay on ``Task`` in the
catalog; agents pass IDs only after Role Analyst.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator


class Role(StrEnum):
    """Canonical supported roles (SAD / PRD). No aliases."""

    UI_DESIGNER = "UI Designer"
    UX_RESEARCHER = "UX Researcher"
    PRODUCT_MANAGER = "Product Manager"
    DEVELOPER = "Developer"
    ENGINEER = "Engineer"


class TaskCategory(StrEnum):
    """Compact catalog categories (developer-tasks.yaml).

    SAD/PRD equivalents: compliance → COMPLIANCE_LEGAL, it_setup →
    IT_PROVISIONING, role_work → ROLE_ENABLEMENT, team_intro → TEAM_INTEGRATION.
    """

    COMPLIANCE = "compliance"
    IT_SETUP = "it_setup"
    ROLE_WORK = "role_work"
    TEAM_INTRO = "team_intro"


class ComplianceStatus(StrEnum):
    """Checker gate. ``pass`` is required before Document Writer runs."""

    PASS = "pass"
    FAIL = "fail"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Task(_StrictModel):
    """One authoritative catalog item. Agents must not invent these."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: TaskCategory
    source: AnyHttpUrl


class TaskCatalog(_StrictModel):
    """Role-scoped catalog: the tasks the Role Analyst may select from."""

    role: Role
    tasks: list[Task] = Field(min_length=0)

    @model_validator(mode="after")
    def unique_task_ids(self) -> TaskCatalog:
        ids = [task.id for task in self.tasks]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise ValueError(f"Duplicate task id(s): {', '.join(duplicates)}")
        return self

    def task_ids(self) -> list[str]:
        return [task.id for task in self.tasks]


class OnboardingInput(_StrictModel):
    """CLI inputs for one generation (Handoff A)."""

    role: Role
    department: str = Field(min_length=1)
    start_date: date

    @field_validator("department")
    @classmethod
    def department_not_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("department must be non-whitespace")
        return value


class RoleAnalysis(_StrictModel):
    """Role Analyst output (Handoff B): applicable catalog IDs only."""

    task_ids: list[str] = Field(min_length=0)

    @field_validator("task_ids")
    @classmethod
    def unique_and_non_empty_ids(cls, value: list[str]) -> list[str]:
        stripped = [item.strip() for item in value]
        if any(not item for item in stripped):
            raise ValueError("task_ids must not contain blank ids")
        duplicates = sorted({item for item in stripped if stripped.count(item) > 1})
        if duplicates:
            raise ValueError(f"Duplicate task id(s): {', '.join(duplicates)}")
        return stripped


class Plan(_StrictModel):
    """Plan Builder output (Handoff C): each selected ID in exactly one bucket.

    List order is sequence within the bucket. Values are catalog task IDs, not
    free-form task definitions.
    """

    day_30: list[str] = Field(default_factory=list)
    day_60: list[str] = Field(default_factory=list)
    day_90: list[str] = Field(default_factory=list)

    @field_validator("day_30", "day_60", "day_90")
    @classmethod
    def bucket_ids_valid(cls, value: list[str]) -> list[str]:
        stripped = [item.strip() for item in value]
        if any(not item for item in stripped):
            raise ValueError("bucket task ids must not be blank")
        return stripped

    @model_validator(mode="after")
    def unique_across_buckets(self) -> Plan:
        combined = [*self.day_30, *self.day_60, *self.day_90]
        duplicates = sorted({item for item in combined if combined.count(item) > 1})
        if duplicates:
            raise ValueError(
                f"Task id(s) appear in more than one bucket: {', '.join(duplicates)}"
            )
        return self

    def all_task_ids(self) -> list[str]:
        return [*self.day_30, *self.day_60, *self.day_90]


class ComplianceResult(_StrictModel):
    """Compliance Checker output (Handoff D). Fail-closed: pass requires no violations."""

    status: ComplianceStatus
    violations: list[str] = Field(default_factory=list)

    @field_validator("violations")
    @classmethod
    def strip_violations(cls, value: list[str]) -> list[str]:
        stripped = [item.strip() for item in value]
        if any(not item for item in stripped):
            raise ValueError("violations must not contain blank messages")
        return stripped

    @model_validator(mode="after")
    def pass_has_no_violations(self) -> ComplianceResult:
        if self.status is ComplianceStatus.PASS and self.violations:
            raise ValueError("pass requires an empty violations list")
        if self.status is ComplianceStatus.FAIL and not self.violations:
            raise ValueError("fail requires at least one violation")
        return self

    @property
    def passed(self) -> bool:
        return self.status is ComplianceStatus.PASS
