"""Thin FastAPI wrapper around ``run_onboarding``. No duplicated crew logic."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError

from onboarding.crew_runtime import live_llm_configured
from onboarding.models import OnboardingInput, Role
from onboarding.rendering import CHECKLIST_FILENAME, PLAN_FILENAME
from onboarding.stubs import stub_agents_for_catalog
from onboarding.workflow import WorkflowResult, run_onboarding

logger = logging.getLogger("onboarding.api")

_ROLE_LIST = ", ".join(role.value for role in Role)
_CATALOG_ROLE = Role.DEVELOPER
_VITE_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
)

RUN_TIMEOUT_SECONDS = 300
GENERIC_RUN_ERROR_MESSAGE = "The run failed due to an unexpected error."
RUN_TIMEOUT_MESSAGE = "Run timed out after 5 minutes"

RunStatus = Literal["running", "done", "error"]


class RunCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: str
    department: str
    start_date: date


class RunRecord:
    def __init__(self, run_id: str, payload: OnboardingInput, submitted_at: str) -> None:
        self.run_id = run_id
        self.payload = payload
        self.submitted_at = submitted_at
        self.status: RunStatus = "running"
        self.onboarding_plan: str | None = None
        self.manager_checklist: str | None = None
        self.violations: list[str] = []
        self.message: str | None = None
        self.completed_at: str | None = None


_lock = threading.Lock()
_runs: dict[str, RunRecord] = {}

app = FastAPI(title="Onboarding plan API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_VITE_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def reset_store() -> None:
    """Test helper: drop in-memory runs. Does not delete Markdown files."""
    with _lock:
        _runs.clear()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error_body(message: str, *, run_id: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"status": "error", "message": message}
    if run_id is not None:
        body["runId"] = run_id
    return body


@app.exception_handler(RequestValidationError)
async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content=_error_body(_format_validation(exc)))


@app.exception_handler(HTTPException)
async def _http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(message),
    )


@app.exception_handler(Exception)
async def _unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
    del exc
    logger.exception("Unhandled API exception")
    return JSONResponse(status_code=500, content=_error_body("Internal error."))


def _format_validation(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        loc = ".".join(str(piece) for piece in error.get("loc", ()) if piece != "body")
        msg = error.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) if parts else "Invalid request."


def _parse_input(body: RunCreateBody) -> OnboardingInput:
    try:
        role = Role(body.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"must be one of: {_ROLE_LIST}. No files were generated.",
        ) from exc
    try:
        payload = OnboardingInput(
            role=role,
            department=body.department,
            start_date=body.start_date,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{exc.errors()[0]['msg']}. No files were generated.",
        ) from exc
    if payload.role is not _CATALOG_ROLE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Role {payload.role.value!r} is not yet supported. "
                f"Only {_CATALOG_ROLE.value} has a task catalog. "
                "No files were generated."
            ),
        )
    return payload


def _use_live_llm() -> bool:
    return live_llm_configured()


def _mark_error(run_id: str, message: str, *, violations: list[str] | None = None) -> None:
    with _lock:
        record = _runs.get(run_id)
        if record is None or record.status != "running":
            return
        record.status = "error"
        record.violations = list(violations or [])
        record.message = message
        record.completed_at = _now()


def _mark_done(run_id: str, plan_text: str, checklist_text: str) -> None:
    with _lock:
        record = _runs.get(run_id)
        if record is None or record.status != "running":
            return
        record.status = "done"
        record.onboarding_plan = plan_text
        record.manager_checklist = checklist_text
        record.completed_at = _now()


def _invoke_crew(payload: OnboardingInput, output_dir: Path) -> WorkflowResult:
    kwargs: dict[str, Any] = {"output_dir": output_dir}
    if not _use_live_llm():
        analyst, builder = stub_agents_for_catalog()
        kwargs["role_analyst"] = analyst
        kwargs["plan_builder"] = builder
    return run_onboarding(payload, **kwargs)


def _read_output_files(output_dir: Path) -> tuple[str, str]:
    plan_text = (output_dir / PLAN_FILENAME).read_text(encoding="utf-8")
    checklist_text = (output_dir / CHECKLIST_FILENAME).read_text(encoding="utf-8")
    return plan_text, checklist_text


async def _execute_run_async(run_id: str, payload: OnboardingInput) -> None:
    started = time.monotonic()
    role = payload.role.value
    output_dir = Path("output") / run_id
    logger.info("Run started runId=%s role=%s", run_id, role)
    outcome = "error"
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_invoke_crew, payload, output_dir),
            timeout=RUN_TIMEOUT_SECONDS,
        )
        if result.ready_to_write:
            plan_text, checklist_text = await asyncio.to_thread(_read_output_files, output_dir)
            _mark_done(run_id, plan_text, checklist_text)
            outcome = "success"
        else:
            _mark_error(run_id, result.message, violations=list(result.violations))
            outcome = "fail"
    except TimeoutError:
        logger.error(
            "Run timed out runId=%s role=%s elapsed_s=%.3f",
            run_id,
            role,
            time.monotonic() - started,
        )
        _mark_error(run_id, RUN_TIMEOUT_MESSAGE)
    except Exception:
        logger.exception(
            "Run failed unexpectedly runId=%s role=%s elapsed_s=%.3f",
            run_id,
            role,
            time.monotonic() - started,
        )
        _mark_error(run_id, GENERIC_RUN_ERROR_MESSAGE)
    else:
        logger.info(
            "Run finished runId=%s role=%s outcome=%s elapsed_s=%.3f",
            run_id,
            role,
            outcome,
            time.monotonic() - started,
        )


def _execute_run(run_id: str, payload: OnboardingInput) -> None:
    asyncio.run(_execute_run_async(run_id, payload))


@app.post("/runs", status_code=202)
def create_run(body: RunCreateBody) -> dict[str, str]:
    payload = _parse_input(body)
    run_id = f"run-{uuid.uuid4()}"
    submitted_at = _now()
    record = RunRecord(run_id, payload, submitted_at)
    with _lock:
        _runs[run_id] = record
    worker = threading.Thread(
        target=_execute_run,
        args=(run_id, payload),
        name=f"onboarding-{run_id}",
        daemon=True,
    )
    worker.start()
    return {"runId": run_id, "status": "running", "submittedAt": submitted_at}


def _snapshot_run(run_id: str) -> dict[str, Any]:
    with _lock:
        record = _runs.get(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Run not found.")
        snapshot = {
            "runId": record.run_id,
            "status": record.status,
            "onboarding_plan": record.onboarding_plan,
            "manager_checklist": record.manager_checklist,
            "violations": list(record.violations),
            "message": record.message,
            "completed_at": record.completed_at,
            "role": record.payload.role.value,
            "department": record.payload.department,
            "start_date": record.payload.start_date.isoformat(),
        }
    if snapshot["status"] == "done":
        plan, checklist = _markdown_for_get(run_id, snapshot)
        snapshot["onboarding_plan"] = plan
        snapshot["manager_checklist"] = checklist
    return snapshot


def _markdown_for_get(run_id: str, snapshot: dict[str, Any]) -> tuple[str, str]:
    plan = snapshot.get("onboarding_plan")
    checklist = snapshot.get("manager_checklist")
    if isinstance(plan, str) and isinstance(checklist, str) and plan and checklist:
        return plan, checklist
    try:
        return _read_output_files(Path("output") / run_id)
    except OSError:
        logger.exception("Failed to read Markdown for runId=%s", run_id)
        raise HTTPException(status_code=500, detail="Internal error.") from None


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    try:
        snapshot = _snapshot_run(run_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("GET /runs/%s failed unexpectedly", run_id)
        raise HTTPException(status_code=500, detail="Internal error.") from None

    status = snapshot["status"]
    if status == "running":
        return {"runId": snapshot["runId"], "status": "running"}
    if status == "done":
        return {
            "runId": snapshot["runId"],
            "status": "done",
            "result": {
                "role": snapshot["role"],
                "department": snapshot["department"],
                "startDate": snapshot["start_date"],
                "onboardingPlan": snapshot["onboarding_plan"],
                "managerChecklist": snapshot["manager_checklist"],
                "completedAt": snapshot["completed_at"],
            },
        }
    return {
        "runId": snapshot["runId"],
        "status": "error",
        "violations": snapshot["violations"],
        "message": snapshot["message"],
    }
