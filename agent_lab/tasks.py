"""Read task board state from the local .tasks directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import TASKS_DIR


@dataclass(frozen=True)
class TaskItem:
    id: str
    subject: str
    status: str
    owner: str
    blocked_by: list[str]


def _task_sort_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    suffix = stem.removeprefix("task_")
    return (int(suffix), stem) if suffix.isdigit() else (10**9, stem)


def _as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def load_tasks(tasks_dir: Path = TASKS_DIR) -> list[TaskItem]:
    """Load task JSON files into a stable, display-friendly shape."""
    if not tasks_dir.exists():
        return []

    tasks: list[TaskItem] = []
    for path in sorted(tasks_dir.glob("*.json"), key=_task_sort_key):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        task_id = str(data.get("id") or path.stem)
        subject = str(data.get("subject") or data.get("title") or "(untitled)")
        status = str(data.get("status") or "unknown")
        owner = str(data.get("owner") or "-")
        blocked_by = _as_list_of_strings(data.get("blockedBy"))
        tasks.append(TaskItem(task_id, subject, status, owner, blocked_by))

    return tasks
