"""Command line interface for exploring Agent Harness Lab assets."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .demo import seed_demo_data
from .docs import load_docs
from .events import load_events, tail_events
from .paths import REPO_ROOT
from .skills import load_skills
from .tasks import claim_task, complete_task, create_task, get_task, load_tasks


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _print_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    if not rows:
        print("(none)")
        return

    widths = [
        max(len(str(value)) for value in [header, *[row[index] for row in rows]])
        for index, header in enumerate(headers)
    ]

    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))


def _parse_blocked_by(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _print_task_detail(task) -> None:
    rows = [
        ["ID", task.id],
        ["Subject", task.subject],
        ["Status", task.status],
        ["Owner", task.owner],
        ["BlockedBy", ",".join(task.blocked_by) if task.blocked_by else "-"],
        ["Path", _rel(task.path)],
    ]
    if task.description:
        rows.insert(2, ["Description", task.description])
    _print_table(["Field", "Value"], rows)


def create_task_command(args: argparse.Namespace) -> int:
    task = create_task(
        args.subject,
        description=args.description,
        owner=args.owner,
        blocked_by=_parse_blocked_by(args.blocked_by),
        tasks_dir=args.tasks_dir,
        events_path=args.events_path,
    )
    print(f"Created task {task.id}: {task.subject}")
    return 0


def show_task_command(args: argparse.Namespace) -> int:
    try:
        task = get_task(args.task_id, args.tasks_dir)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    _print_task_detail(task)
    return 0


def claim_task_command(args: argparse.Namespace) -> int:
    try:
        task = claim_task(args.task_id, args.owner, args.tasks_dir, args.events_path)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    print(f"Claimed task {task.id} for {task.owner}")
    return 0


def complete_task_command(args: argparse.Namespace) -> int:
    try:
        task = complete_task(args.task_id, args.tasks_dir, args.events_path)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    print(f"Completed task {task.id}: {task.subject}")
    return 0


def list_tasks_command(args: argparse.Namespace) -> int:
    tasks = load_tasks(args.tasks_dir)
    rows = [
        [
            task.id,
            task.status,
            task.owner,
            ",".join(task.blocked_by) if task.blocked_by else "-",
            task.subject,
        ]
        for task in tasks
    ]
    _print_table(["ID", "Status", "Owner", "BlockedBy", "Subject"], rows)
    return 0


def list_skills(_: argparse.Namespace) -> int:
    skills = load_skills()
    rows = [[skill.name, skill.description, _rel(skill.path)] for skill in skills]
    _print_table(["Name", "Description", "Path"], rows)
    return 0


def list_docs(_: argparse.Namespace) -> int:
    docs = load_docs()
    rows = [[doc.locale, doc.version, doc.title, _rel(doc.path)] for doc in docs]
    _print_table(["Locale", "Version", "Title", "Path"], rows)
    return 0


def _event_rows(events) -> list[list[str]]:
    rows: list[list[str]] = []
    for event in events:
        task_id = str(event.payload.get("task_id", "-"))
        owner = str(event.payload.get("owner", "-") or "-")
        subject = str(event.payload.get("subject", "-"))
        rows.append([event.timestamp, event.event_type, task_id, owner, subject])
    return rows


def list_events_command(args: argparse.Namespace) -> int:
    events = load_events(args.events_path)
    _print_table(["Timestamp", "Type", "Task", "Owner", "Subject"], _event_rows(events))
    return 0


def tail_events_command(args: argparse.Namespace) -> int:
    events = tail_events(args.limit, args.events_path)
    _print_table(["Timestamp", "Type", "Task", "Owner", "Subject"], _event_rows(events))
    return 0


def seed_demo_command(args: argparse.Namespace) -> int:
    result = seed_demo_data(args.tasks_dir, args.events_path)
    if result.created:
        print(f"Seeded demo tasks: {', '.join(result.task_ids)}")
    else:
        print(f"Demo tasks already exist: {', '.join(result.task_ids)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent_lab",
        description="Explore Agent Harness Lab tasks, skills, and docs.",
    )
    subparsers = parser.add_subparsers(dest="resource", required=True)

    tasks_parser = subparsers.add_parser("tasks", help="Manage local task board")
    tasks_parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    tasks_parser.add_argument(
        "--events-path",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    tasks_sub = tasks_parser.add_subparsers(dest="action", required=True)
    tasks_list = tasks_sub.add_parser("list", help="List .tasks/*.json")
    tasks_list.set_defaults(func=list_tasks_command)

    tasks_create = tasks_sub.add_parser("create", help="Create a new pending task")
    tasks_create.add_argument("subject", help="Task subject")
    tasks_create.add_argument("--description", default="", help="Task description")
    tasks_create.add_argument("--owner", default="", help="Initial task owner")
    tasks_create.add_argument(
        "--blocked-by",
        default="",
        help="Comma-separated dependency task IDs, for example: 1,2",
    )
    tasks_create.set_defaults(func=create_task_command)

    tasks_show = tasks_sub.add_parser("show", help="Show one task")
    tasks_show.add_argument("task_id", help="Task ID")
    tasks_show.set_defaults(func=show_task_command)

    tasks_claim = tasks_sub.add_parser("claim", help="Claim a task for an owner")
    tasks_claim.add_argument("task_id", help="Task ID")
    tasks_claim.add_argument("--owner", required=True, help="Owner name")
    tasks_claim.set_defaults(func=claim_task_command)

    tasks_complete = tasks_sub.add_parser("complete", help="Mark a task completed")
    tasks_complete.add_argument("task_id", help="Task ID")
    tasks_complete.set_defaults(func=complete_task_command)

    skills_parser = subparsers.add_parser("skills", help="Inspect local skills")
    skills_sub = skills_parser.add_subparsers(dest="action", required=True)
    skills_list = skills_sub.add_parser("list", help="List skills/*/SKILL.md")
    skills_list.set_defaults(func=list_skills)

    docs_parser = subparsers.add_parser("docs", help="Inspect course documents")
    docs_sub = docs_parser.add_subparsers(dest="action", required=True)
    docs_list = docs_sub.add_parser("list", help="List docs/en and docs/zh")
    docs_list.set_defaults(func=list_docs)

    events_parser = subparsers.add_parser("events", help="Inspect local event log")
    events_parser.add_argument(
        "--events-path",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    events_sub = events_parser.add_subparsers(dest="action", required=True)
    events_list = events_sub.add_parser("list", help="List all events")
    events_list.set_defaults(func=list_events_command)
    events_tail = events_sub.add_parser("tail", help="Show recent events")
    events_tail.add_argument("--limit", type=int, default=10, help="Number of events to show")
    events_tail.set_defaults(func=tail_events_command)

    demo_parser = subparsers.add_parser("demo", help="Generate local demo data")
    demo_parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    demo_parser.add_argument(
        "--events-path",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    demo_sub = demo_parser.add_subparsers(dest="action", required=True)
    demo_seed = demo_sub.add_parser("seed", help="Seed dashboard demo tasks and events")
    demo_seed.set_defaults(func=seed_demo_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "tasks_dir", None) is None:
        from .paths import TASKS_DIR

        args.tasks_dir = TASKS_DIR
    if getattr(args, "events_path", None) is None:
        from .paths import EVENTS_PATH

        args.events_path = EVENTS_PATH
    return args.func(args)
