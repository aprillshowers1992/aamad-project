"""Onboarding workflow orchestrator: RA → PB → deterministic Checker, then Writer.

Retry loop (application-owned, not CrewAI retries): up to MAX_ATTEMPTS of
Role Analyst → Plan Builder → check_compliance. Document Writer runs only on PASS.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from onboarding.catalog import load_developer_catalog
from onboarding.compliance import check_compliance
from onboarding.models import (
    ComplianceResult,
    ComplianceStatus,
    OnboardingInput,
    Plan,
    RoleAnalysis,
    TaskCatalog,
)
from onboarding.rendering import MarkdownDocumentWriter

logger = logging.getLogger("onboarding.workflow")

MAX_ATTEMPTS = 3
READY_TO_WRITE_MESSAGE = "compliance passed, ready to write files"
NO_APPROVED_OUTPUT_MESSAGE = (
    "No approved output. Compliance failed after {attempts} attempts."
)


class WorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ComplianceStatus
    attempts: int = Field(ge=1)
    violations: list[str] = Field(default_factory=list)
    message: str
    ready_to_write: bool
    plan: Plan | None = None
    output_files: list[str] = Field(default_factory=list)


class RoleAnalyst(Protocol):
    def analyze(
        self,
        inp: OnboardingInput,
        catalog: TaskCatalog,
        *,
        attempt: int,
        max_attempts: int,
        previous_violations: list[str],
    ) -> RoleAnalysis: ...


class PlanBuilder(Protocol):
    def build(
        self,
        analysis: RoleAnalysis,
        catalog: TaskCatalog,
        *,
        attempt: int,
        max_attempts: int,
        previous_violations: list[str],
    ) -> Plan: ...


class ComplianceChecker(Protocol):
    def check(self, plan: Plan, catalog: TaskCatalog) -> ComplianceResult: ...


class DocumentWriter(Protocol):
    def write(
        self,
        inp: OnboardingInput,
        plan: Plan,
        catalog: TaskCatalog,
        compliance: ComplianceResult,
        *,
        output_dir: Path,
    ) -> list[Path]: ...


class DeterministicComplianceChecker:
    """Crew Compliance Checker: pass/fail is check_compliance only."""

    def check(self, plan: Plan, catalog: TaskCatalog) -> ComplianceResult:
        return check_compliance(plan, catalog)


class PlaceholderDocumentWriter:
    """Test double: records a PASS without writing Markdown files."""

    def write(
        self,
        inp: OnboardingInput,
        plan: Plan,
        catalog: TaskCatalog,
        compliance: ComplianceResult,
        *,
        output_dir: Path,
    ) -> list[Path]:
        del inp, plan, catalog, compliance, output_dir
        return []


def restrict_analysis_to_catalog(
    analysis: RoleAnalysis,
    catalog: TaskCatalog,
) -> RoleAnalysis:
    allowed = set(catalog.task_ids())
    return RoleAnalysis(task_ids=[task_id for task_id in analysis.task_ids if task_id in allowed])


def run_onboarding(
    inp: OnboardingInput,
    catalog: TaskCatalog | None = None,
    *,
    role_analyst: RoleAnalyst | None = None,
    plan_builder: PlanBuilder | None = None,
    compliance_checker: ComplianceChecker | None = None,
    document_writer: DocumentWriter | None = None,
    max_attempts: int = MAX_ATTEMPTS,
    output_dir: Path | str | None = None,
) -> WorkflowResult:
    """Run the four-agent workflow. LLM agents are built only when not injected."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if catalog is None:
        catalog = load_developer_catalog()
    if role_analyst is None or plan_builder is None:
        from onboarding.crew_runtime import build_llm_agents

        llm_analyst, llm_builder = build_llm_agents()
        role_analyst = role_analyst or llm_analyst
        plan_builder = plan_builder or llm_builder
    checker = compliance_checker or DeterministicComplianceChecker()
    writer = document_writer or MarkdownDocumentWriter()
    resolved_output_dir = Path(output_dir) if output_dir is not None else Path("output")

    previous_violations: list[str] = []
    last_compliance: ComplianceResult | None = None
    last_plan: Plan | None = None

    for attempt in range(1, max_attempts + 1):
        analysis = role_analyst.analyze(
            inp,
            catalog,
            attempt=attempt,
            max_attempts=max_attempts,
            previous_violations=previous_violations,
        )
        analysis = restrict_analysis_to_catalog(analysis, catalog)
        plan = plan_builder.build(
            analysis,
            catalog,
            attempt=attempt,
            max_attempts=max_attempts,
            previous_violations=previous_violations,
        )
        last_plan = plan
        last_compliance = checker.check(plan, catalog)
        if last_compliance.passed:
            paths = writer.write(
                inp,
                plan,
                catalog,
                last_compliance,
                output_dir=resolved_output_dir,
            )
            logger.info(READY_TO_WRITE_MESSAGE)
            return WorkflowResult(
                status=ComplianceStatus.PASS,
                attempts=attempt,
                violations=[],
                message=READY_TO_WRITE_MESSAGE,
                ready_to_write=True,
                plan=plan,
                output_files=[str(path) for path in paths],
            )
        previous_violations = list(last_compliance.violations)
        logger.error(
            "Compliance FAIL on attempt %s/%s: %s",
            attempt,
            max_attempts,
            "; ".join(previous_violations),
        )

    assert last_compliance is not None
    message = NO_APPROVED_OUTPUT_MESSAGE.format(attempts=max_attempts)
    logger.error("%s Rules: %s", message, "; ".join(last_compliance.violations))
    return WorkflowResult(
        status=ComplianceStatus.FAIL,
        attempts=max_attempts,
        violations=list(last_compliance.violations),
        message=message,
        ready_to_write=False,
        plan=last_plan,
        output_files=[],
    )
