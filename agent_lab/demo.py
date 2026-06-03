"""Seed demo task and event data for the Web Dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .tasks import claim_task, complete_task, create_task, load_tasks


DEMO_PREFIX = "[demo]"


@dataclass(frozen=True)
class DemoSeedResult:
    created: bool
    task_ids: list[str]


def seed_demo_data(tasks_dir: Path, events_path: Path) -> DemoSeedResult:
    """Create a small non-destructive task graph with lifecycle events."""
    existing = [task for task in load_tasks(tasks_dir) if task.subject.startswith(DEMO_PREFIX)]
    if existing:
        return DemoSeedResult(created=False, task_ids=[task.id for task in existing])

    cli_task = create_task(
        f"{DEMO_PREFIX} Build Agent Lab CLI",
        description="Create a local CLI for tasks, skills, docs, and events.",
        owner="penglei",
        tasks_dir=tasks_dir,
        events_path=events_path,
    )
    claim_task(cli_task.id, "penglei", tasks_dir, events_path)
    complete_task(cli_task.id, tasks_dir, events_path)

    events_task = create_task(
        f"{DEMO_PREFIX} Add JSONL event log",
        description="Record task lifecycle events for dashboard observability.",
        owner="penglei",
        blocked_by=[cli_task.id],
        tasks_dir=tasks_dir,
        events_path=events_path,
    )
    claim_task(events_task.id, "penglei", tasks_dir, events_path)
    complete_task(events_task.id, tasks_dir, events_path)

    dashboard_task = create_task(
        f"{DEMO_PREFIX} Build Web Dashboard",
        description="Show tasks, skills, docs, dependencies, and runtime events.",
        owner="penglei",
        blocked_by=[events_task.id],
        tasks_dir=tasks_dir,
        events_path=events_path,
    )
    claim_task(dashboard_task.id, "penglei", tasks_dir, events_path)

    graph_task = create_task(
        f"{DEMO_PREFIX} Add dependency graph",
        description="Visualize blockedBy relationships in the dashboard.",
        blocked_by=[dashboard_task.id],
        tasks_dir=tasks_dir,
        events_path=events_path,
    )

    return DemoSeedResult(
        created=True,
        task_ids=[cli_task.id, events_task.id, dashboard_task.id, graph_task.id],
    )
