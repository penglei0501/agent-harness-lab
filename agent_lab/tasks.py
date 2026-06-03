"""Read and update task board state in the local .tasks directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from .events import append_event
from .paths import EVENTS_PATH, TASKS_DIR


@dataclass(frozen=True)
class TaskItem:
    id: str
    subject: str
    description: str
    status: str
    owner: str
    blocked_by: list[str]
    path: Path


def _task_sort_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    suffix = stem.removeprefix("task_")
    return (int(suffix), stem) if suffix.isdigit() else (10**9, stem)


def _as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _load_task_data(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _task_path(task_id: str | int, tasks_dir: Path = TASKS_DIR) -> Path:
    return tasks_dir / f"task_{task_id}.json"


def _normalize_blocked_by(blocked_by: list[str | int] | None) -> list[str | int]:
    if blocked_by is None:
        return []
    normalized: list[str | int] = []
    for item in blocked_by:
        value = str(item).strip()
        if not value:
            continue
        normalized.append(int(value) if value.isdigit() else value)
    return normalized


def _next_task_id(tasks_dir: Path = TASKS_DIR) -> int:
    ids: list[int] = []
    if tasks_dir.exists():
        for path in tasks_dir.glob("task_*.json"):
            suffix = path.stem.removeprefix("task_")
            if suffix.isdigit():
                ids.append(int(suffix))
    return max(ids, default=0) + 1


def _write_task(data: dict[str, Any], tasks_dir: Path = TASKS_DIR) -> Path:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    path = _task_path(data["id"], tasks_dir)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_tasks(tasks_dir: Path = TASKS_DIR) -> list[TaskItem]:
    """Load task JSON files into a stable, display-friendly shape."""
    if not tasks_dir.exists():
        return []

    tasks: list[TaskItem] = []
    for path in sorted(tasks_dir.glob("*.json"), key=_task_sort_key):
        data = _load_task_data(path)
        if data is None:
            continue

        task_id = str(data.get("id") or path.stem)
        subject = str(data.get("subject") or data.get("title") or "(untitled)")
        description = str(data.get("description") or "")
        status = str(data.get("status") or "unknown")
        owner = str(data.get("owner") or "-")
        blocked_by = _as_list_of_strings(data.get("blockedBy"))
        tasks.append(TaskItem(task_id, subject, description, status, owner, blocked_by, path))

    return tasks


def get_task(task_id: str | int, tasks_dir: Path = TASKS_DIR) -> TaskItem:
    """Return one task by ID, raising FileNotFoundError when missing."""
    path = _task_path(task_id, tasks_dir)
    data = _load_task_data(path)
    if data is None:
        raise FileNotFoundError(f"Task not found: {task_id}")

    task_id_str = str(data.get("id") or task_id)
    subject = str(data.get("subject") or data.get("title") or "(untitled)")
    description = str(data.get("description") or "")
    status = str(data.get("status") or "unknown")
    owner = str(data.get("owner") or "-")
    blocked_by = _as_list_of_strings(data.get("blockedBy"))
    return TaskItem(task_id_str, subject, description, status, owner, blocked_by, path)


def create_task(
    subject: str,
    *,
    description: str = "",
    owner: str = "",
    blocked_by: list[str | int] | None = None,
    tasks_dir: Path = TASKS_DIR,
    events_path: Path | None = EVENTS_PATH,
) -> TaskItem:
    """Create a new pending task and persist it as task_N.json."""
    task_id = _next_task_id(tasks_dir)
    now = time.time()
    data: dict[str, Any] = {
        "id": task_id,
        "subject": subject,
        "description": description,
        "status": "pending",
        "owner": owner,
        "worktree": "",
        "blockedBy": _normalize_blocked_by(blocked_by),
        "created_at": now,
        "updated_at": now,
    }
    _write_task(data, tasks_dir)
    task = get_task(task_id, tasks_dir)
    if events_path is not None:
        append_event(
            "task_created",
            {
                "task_id": task.id,
                "subject": task.subject,
                "owner": "" if task.owner == "-" else task.owner,
                "blockedBy": task.blocked_by,
            },
            events_path=events_path,
        )
    return task


def claim_task(
    task_id: str | int,
    owner: str,
    tasks_dir: Path = TASKS_DIR,
    events_path: Path | None = EVENTS_PATH,
) -> TaskItem:
    """Assign a task to an owner and mark it in progress."""
    path = _task_path(task_id, tasks_dir)
    data = _load_task_data(path)
    if data is None:
        raise FileNotFoundError(f"Task not found: {task_id}")

    data["owner"] = owner
    data["status"] = "in_progress"
    data["updated_at"] = time.time()
    _write_task(data, tasks_dir)
    task = get_task(task_id, tasks_dir)
    if events_path is not None:
        append_event(
            "task_claimed",
            {"task_id": task.id, "subject": task.subject, "owner": task.owner},
            events_path=events_path,
        )
    return task


def complete_task(
    task_id: str | int,
    tasks_dir: Path = TASKS_DIR,
    events_path: Path | None = EVENTS_PATH,
) -> TaskItem:
    """Mark a task completed."""
    path = _task_path(task_id, tasks_dir)
    data = _load_task_data(path)
    if data is None:
        raise FileNotFoundError(f"Task not found: {task_id}")

    data["status"] = "completed"
    data["updated_at"] = time.time()
    _write_task(data, tasks_dir)
    task = get_task(task_id, tasks_dir)
    if events_path is not None:
        append_event(
            "task_completed",
            {"task_id": task.id, "subject": task.subject, "owner": task.owner},
            events_path=events_path,
        )
    return task
