"""CrewAI-backed Role Analyst and Plan Builder. Secrets from env vars only."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from onboarding.models import OnboardingInput, Plan, RoleAnalysis, TaskCatalog

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini/gemini-3.6-flash"
DEFAULT_TEMPERATURE = 0.2


class CrewRuntimeError(RuntimeError):
    """CrewAI runtime is misconfigured or returned unusable output."""


def load_project_dotenv() -> None:
    """Load repo-root ``.env``. Non-empty process env vars win; blank ones are filled."""
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    _load_dotenv_fill_blanks(env_path)


def live_llm_configured() -> bool:
    """True when a provider key is present (OpenAI or Gemini). Does not load ``.env``."""
    return bool(
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
    )


def _load_dotenv_fill_blanks(env_path: Path) -> None:
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and not os.environ.get(key, "").strip():
            os.environ[key] = value


def build_llm_agents() -> tuple["CrewAIRoleAnalyst", "CrewAIPlanBuilder"]:
    agents_cfg = _load_yaml("agents.yaml")
    tasks_cfg = _load_yaml("tasks.yaml")
    llm = _build_llm()
    role_agent = _build_agent(agents_cfg["role_analyst"], llm)
    plan_agent = _build_agent(agents_cfg["plan_builder"], llm)
    return (
        CrewAIRoleAnalyst(role_agent, tasks_cfg["analyze_role"]),
        CrewAIPlanBuilder(plan_agent, tasks_cfg["build_plan"]),
    )


class CrewAIRoleAnalyst:
    def __init__(self, agent: Any, task_cfg: dict[str, Any]) -> None:
        self._agent = agent
        self._task_cfg = task_cfg

    def analyze(
        self,
        inp: OnboardingInput,
        catalog: TaskCatalog,
        *,
        attempt: int,
        max_attempts: int,
        previous_violations: list[str],
    ) -> RoleAnalysis:
        raw = _kickoff(
            agent=self._agent,
            description=self._task_cfg["description"],
            expected_output=self._task_cfg["expected_output"],
            inputs={
                "role": inp.role.value,
                "department": inp.department,
                "start_date": inp.start_date.isoformat(),
                "attempt": str(attempt),
                "max_attempts": str(max_attempts),
                "previous_violations": _format_violations(previous_violations),
                "catalog_json": json.dumps(_catalog_payload(catalog), indent=2),
            },
        )
        return _parse_output(raw, RoleAnalysis)


class CrewAIPlanBuilder:
    def __init__(self, agent: Any, task_cfg: dict[str, Any]) -> None:
        self._agent = agent
        self._task_cfg = task_cfg

    def build(
        self,
        analysis: RoleAnalysis,
        catalog: TaskCatalog,
        *,
        attempt: int,
        max_attempts: int,
        previous_violations: list[str],
    ) -> Plan:
        selected = [task for task in catalog.tasks if task.id in set(analysis.task_ids)]
        raw = _kickoff(
            agent=self._agent,
            description=self._task_cfg["description"],
            expected_output=self._task_cfg["expected_output"],
            inputs={
                "selected_task_ids": json.dumps(analysis.task_ids),
                "selected_tasks_json": json.dumps(
                    [
                        {
                            "id": task.id,
                            "category": task.category.value,
                            "title": task.title,
                        }
                        for task in selected
                    ],
                    indent=2,
                ),
                "attempt": str(attempt),
                "max_attempts": str(max_attempts),
                "previous_violations": _format_violations(previous_violations),
            },
        )
        return _parse_output(raw, Plan)


def _load_yaml(filename: str) -> dict[str, Any]:
    path = CONFIG_DIR / filename
    if not path.is_file():
        raise CrewRuntimeError(f"Missing CrewAI config file: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise CrewRuntimeError(f"CrewAI config must be a mapping: {path}")
    return loaded


def _build_llm() -> Any:
    load_project_dotenv()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if openai_key:
        model, api_key = OPENAI_MODEL, openai_key
    elif gemini_key:
        model, api_key = GEMINI_MODEL, gemini_key
    else:
        raise CrewRuntimeError(
            "Neither OPENAI_API_KEY nor GEMINI_API_KEY is set. "
            "CrewAI agents cannot run. No files were generated."
        )
    try:
        from crewai import LLM
    except ImportError as exc:
        raise CrewRuntimeError(
            "crewai is not installed (current CrewAI wheels require Python 3.10–3.13). "
            "No files were generated."
        ) from exc
    return LLM(model=model, temperature=DEFAULT_TEMPERATURE, api_key=api_key)


def _build_agent(cfg: dict[str, Any], llm: Any) -> Any:
    from crewai import Agent

    return Agent(
        role=cfg["role"],
        goal=cfg["goal"],
        backstory=cfg["backstory"],
        llm=llm,
        allow_delegation=bool(cfg.get("allow_delegation", False)),
        max_iter=int(cfg.get("max_iter", 12)),
        verbose=False,
    )


def _kickoff(
    *,
    agent: Any,
    description: str,
    expected_output: str,
    inputs: dict[str, str],
) -> Any:
    from crewai import Crew, Process, Task

    try:
        task = Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            output_pydantic=None,
        )
    except TypeError:
        task = Task(description=description, expected_output=expected_output, agent=agent)
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        memory=False,
        verbose=False,
    )
    return crew.kickoff(inputs=inputs)


def _catalog_payload(catalog: TaskCatalog) -> list[dict[str, str]]:
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category.value,
            "source": str(task.source),
        }
        for task in catalog.tasks
    ]


def _format_violations(violations: list[str]) -> str:
    if not violations:
        return "(none)"
    return " | ".join(violations)


def _parse_output(raw: Any, model_cls: type):
    if isinstance(raw, model_cls):
        return raw
    pydantic_out = getattr(raw, "pydantic", None)
    if isinstance(pydantic_out, model_cls):
        return pydantic_out
    if isinstance(raw, dict):
        return model_cls.model_validate(raw)
    json_attr = getattr(raw, "json_dict", None)
    if isinstance(json_attr, dict):
        return model_cls.model_validate(json_attr)
    text = getattr(raw, "raw", None) or getattr(raw, "json", None) or str(raw)
    if isinstance(text, dict):
        return model_cls.model_validate(text)
    payload = _extract_json_object(str(text))
    try:
        return model_cls.model_validate(payload)
    except Exception as exc:
        raise CrewRuntimeError(
            f"CrewAI output could not be parsed as {model_cls.__name__}: {exc}"
        ) from exc


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if "```" in stripped:
        parts = stripped.split("```")
        for part in parts:
            chunk = part.strip()
            if chunk.startswith("json"):
                chunk = chunk[4:].strip()
            if chunk.startswith("{") and chunk.endswith("}"):
                stripped = chunk
                break
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise CrewRuntimeError("CrewAI output did not contain a JSON object.")
    loaded = json.loads(stripped[start : end + 1])
    if not isinstance(loaded, dict):
        raise CrewRuntimeError("CrewAI JSON output must be an object.")
    return loaded
