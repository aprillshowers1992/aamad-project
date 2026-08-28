"""HTTP API tests. Crew path uses package stubs — no live LLM (OQ-13)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from click.testing import CliRunner
from fastapi.testclient import TestClient

from onboarding.api import GENERIC_RUN_ERROR_MESSAGE, app, reset_store
from onboarding.cli import cli
from onboarding.rendering import CHECKLIST_FILENAME, PLAN_FILENAME
from onboarding.stubs import stub_agents_for_catalog

_DEV_BODY = {
    "role": "Developer",
    "department": "AI Engineering",
    "start_date": "2026-09-01",
}

_DEV_ARGS = [
    "--role",
    "Developer",
    "--department",
    "AI Engineering",
    "--start-date",
    "2026-09-01",
]


def _poll_until_terminal(client: TestClient, run_id: str) -> dict:
    payload = None
    for _ in range(200):
        polled = client.get(f"/runs/{run_id}")
        assert polled.status_code == 200, polled.text
        payload = polled.json()
        if payload["status"] != "running":
            break
        time.sleep(0.05)
    assert payload is not None
    return payload


def test_post_developer_polls_until_done_matches_cli(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    reset_store()
    caplog.set_level(logging.INFO, logger="onboarding.api")
    client = TestClient(app)

    started = client.post("/runs", json=_DEV_BODY)
    assert started.status_code == 202, started.text
    body = started.json()
    assert body["status"] == "running"
    assert body["runId"].startswith("run-")
    assert "submittedAt" in body
    run_id = body["runId"]

    payload = _poll_until_terminal(client, run_id)
    assert payload["status"] == "done"
    assert payload["runId"] == run_id
    result = payload["result"]
    assert result["role"] == "Developer"
    assert result["department"] == "AI Engineering"
    assert result["startDate"] == "2026-09-01"
    assert result["onboardingPlan"]
    assert result["managerChecklist"]
    assert result["completedAt"]

    monkeypatch.setattr("onboarding.crew_runtime.build_llm_agents", stub_agents_for_catalog)
    cli_result = CliRunner().invoke(cli, _DEV_ARGS)
    assert cli_result.exit_code == 0, cli_result.output
    cli_plan = (tmp_path / "output" / PLAN_FILENAME).read_text(encoding="utf-8")
    cli_checklist = (tmp_path / "output" / CHECKLIST_FILENAME).read_text(encoding="utf-8")
    assert result["onboardingPlan"] == cli_plan
    assert result["managerChecklist"] == cli_checklist
    assert (tmp_path / "output" / run_id / PLAN_FILENAME).is_file()
    messages = [record.getMessage() for record in caplog.records if record.name == "onboarding.api"]
    assert any("Run started" in item and run_id in item for item in messages)
    assert any("Run finished" in item and "outcome=success" in item for item in messages)


def test_crew_exception_returns_error_not_500(tmp_path: Path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    reset_store()
    caplog.set_level(logging.ERROR, logger="onboarding.api")

    def boom(*_args, **_kwargs):
        raise RuntimeError("secret stack should not leak")

    monkeypatch.setattr("onboarding.api.run_onboarding", boom)
    client = TestClient(app)
    started = client.post("/runs", json=_DEV_BODY)
    assert started.status_code == 202, started.text
    run_id = started.json()["runId"]
    payload = _poll_until_terminal(client, run_id)

    assert payload["status"] == "error"
    assert payload["message"] == GENERIC_RUN_ERROR_MESSAGE
    assert "secret" not in payload["message"]
    assert "Traceback" not in str(payload)
    assert payload.get("violations") == []
    messages = [record.getMessage() for record in caplog.records if record.name == "onboarding.api"]
    assert any("Run failed unexpectedly" in item and run_id in item for item in messages)
