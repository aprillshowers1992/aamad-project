"""Catalog loader tests. Fail-closed: invalid YAML must raise CatalogLoadError."""

from pathlib import Path

import pytest

from onboarding.catalog import (
    CatalogLoadError,
    DEFAULT_DEVELOPER_CATALOG_PATH,
    load_developer_catalog,
    load_task_catalog,
)
from onboarding.models import Role, TaskCategory

EXPECTED_DEVELOPER_TASK_COUNT = 15
EXPECTED_CATEGORIES = {
    TaskCategory.COMPLIANCE,
    TaskCategory.IT_SETUP,
    TaskCategory.ROLE_WORK,
    TaskCategory.TEAM_INTRO,
}


def test_load_real_developer_catalog() -> None:
    catalog = load_developer_catalog()
    assert catalog.role is Role.DEVELOPER
    assert len(catalog.tasks) == EXPECTED_DEVELOPER_TASK_COUNT
    ids = catalog.task_ids()
    assert len(ids) == len(set(ids))
    assert {task.category for task in catalog.tasks} == EXPECTED_CATEGORIES
    for task in catalog.tasks:
        assert task.id
        assert task.title
        assert task.description
        assert str(task.source)


def test_load_task_catalog_accepts_explicit_path() -> None:
    catalog = load_task_catalog(DEFAULT_DEVELOPER_CATALOG_PATH, role=Role.DEVELOPER)
    assert len(catalog.tasks) == EXPECTED_DEVELOPER_TASK_COUNT


def test_load_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-catalog.yaml"
    with pytest.raises(CatalogLoadError, match="not found"):
        load_task_catalog(missing)


def test_load_rejects_blank_title(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        "\n".join(
            [
                "tasks:",
                "  - id: COMP-001",
                "    title: '   '",
                "    description: Sign the agreement.",
                "    category: compliance",
                "    source: https://intranet.example.com/hr/employment-agreement",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogLoadError, match="Invalid task"):
        load_task_catalog(path)


def test_load_rejects_unknown_category(tmp_path: Path) -> None:
    path = tmp_path / "bad-category.yaml"
    path.write_text(
        "\n".join(
            [
                "tasks:",
                "  - id: COMP-001",
                "    title: Sign employment agreement",
                "    description: Sign the agreement.",
                "    category: not_a_category",
                "    source: https://intranet.example.com/hr/employment-agreement",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogLoadError, match="Invalid task"):
        load_task_catalog(path)


def test_load_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "dupes.yaml"
    path.write_text(
        "\n".join(
            [
                "tasks:",
                "  - id: COMP-001",
                "    title: First",
                "    description: One.",
                "    category: compliance",
                "    source: https://intranet.example.com/a",
                "  - id: COMP-001",
                "    title: Second",
                "    description: Two.",
                "    category: compliance",
                "    source: https://intranet.example.com/b",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogLoadError, match="Duplicate task id"):
        load_task_catalog(path)
