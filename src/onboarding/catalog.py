"""Load a compact role task catalog YAML into ``TaskCatalog``.

Expected file shape (see ``project-context/2.build/developer-tasks.yaml``):

```yaml
role: Developer   # optional; defaults to the ``role`` argument
tasks:
  - id: COMP-001
    title: ...
    description: ...
    category: compliance
    source: https://...
```

Validation failures raise ``CatalogLoadError``. Bad entries are never skipped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from onboarding.models import Role, Task, TaskCatalog

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEVELOPER_CATALOG_PATH = (
    REPO_ROOT / "project-context" / "2.build" / "developer-tasks.yaml"
)

_ALLOWED_ROOT_KEYS = frozenset({"tasks", "role"})


class CatalogLoadError(Exception):
    """Catalog file is missing, malformed, or fails Task/TaskCatalog validation."""


def load_task_catalog(
    path: str | Path,
    *,
    role: Role = Role.DEVELOPER,
) -> TaskCatalog:
    """Parse ``path`` into a ``TaskCatalog``. Fail on the first invalid task."""
    catalog_path = Path(path)
    if not catalog_path.is_file():
        raise CatalogLoadError(f"Task catalog file not found: {catalog_path}")

    try:
        raw_text = catalog_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogLoadError(f"Could not read task catalog {catalog_path}: {exc}") from exc

    try:
        loaded = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise CatalogLoadError(f"Invalid YAML in {catalog_path}: {exc}") from exc

    if loaded is None:
        raise CatalogLoadError(f"Task catalog is empty: {catalog_path}")
    if not isinstance(loaded, dict):
        raise CatalogLoadError(
            f"Task catalog root must be a mapping with a 'tasks' list, got "
            f"{type(loaded).__name__}: {catalog_path}"
        )

    unknown = sorted(set(loaded) - _ALLOWED_ROOT_KEYS)
    if unknown:
        raise CatalogLoadError(
            f"Unknown top-level key(s) in {catalog_path}: {', '.join(unknown)}"
        )

    if "tasks" not in loaded:
        raise CatalogLoadError(f"Task catalog missing 'tasks' list: {catalog_path}")

    raw_tasks = loaded["tasks"]
    if not isinstance(raw_tasks, list):
        raise CatalogLoadError(
            f"'tasks' must be a list, got {type(raw_tasks).__name__}: {catalog_path}"
        )
    if not raw_tasks:
        raise CatalogLoadError(f"Task catalog 'tasks' list is empty: {catalog_path}")

    resolved_role = _resolve_role(loaded.get("role"), role, catalog_path)
    tasks = [_parse_task(index, item, catalog_path) for index, item in enumerate(raw_tasks)]

    try:
        return TaskCatalog(role=resolved_role, tasks=tasks)
    except ValidationError as exc:
        raise CatalogLoadError(
            f"Task catalog validation failed for {catalog_path}: {_format_pydantic(exc)}"
        ) from exc


def load_developer_catalog(
    path: str | Path | None = None,
) -> TaskCatalog:
    """Load the Developer catalog (default: repo ``developer-tasks.yaml``)."""
    return load_task_catalog(
        path or DEFAULT_DEVELOPER_CATALOG_PATH,
        role=Role.DEVELOPER,
    )


def _resolve_role(raw_role: Any, default: Role, catalog_path: Path) -> Role:
    if raw_role is None:
        return default
    try:
        return Role(raw_role)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Role)
        raise CatalogLoadError(
            f"Invalid role {raw_role!r} in {catalog_path}; expected one of: {allowed}"
        ) from exc


def _parse_task(index: int, item: Any, catalog_path: Path) -> Task:
    if not isinstance(item, dict):
        raise CatalogLoadError(
            f"Task at index {index} in {catalog_path} must be a mapping, "
            f"got {type(item).__name__}"
        )
    try:
        return Task.model_validate(item)
    except ValidationError as exc:
        task_id = item.get("id", "<missing id>")
        raise CatalogLoadError(
            f"Invalid task {task_id!r} at index {index} in {catalog_path}: "
            f"{_format_pydantic(exc)}"
        ) from exc


def _format_pydantic(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        loc = ".".join(str(piece) for piece in error.get("loc", ()))
        msg = error.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) if parts else str(exc)
