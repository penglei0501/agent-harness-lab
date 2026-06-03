"""Command line interface for exploring Agent Harness Lab assets."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .docs import load_docs
from .paths import REPO_ROOT
from .skills import load_skills
from .tasks import load_tasks


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


def list_tasks(_: argparse.Namespace) -> int:
    tasks = load_tasks()
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent_lab",
        description="Explore Agent Harness Lab tasks, skills, and docs.",
    )
    subparsers = parser.add_subparsers(dest="resource", required=True)

    tasks_parser = subparsers.add_parser("tasks", help="Inspect local task board")
    tasks_sub = tasks_parser.add_subparsers(dest="action", required=True)
    tasks_list = tasks_sub.add_parser("list", help="List .tasks/*.json")
    tasks_list.set_defaults(func=list_tasks)

    skills_parser = subparsers.add_parser("skills", help="Inspect local skills")
    skills_sub = skills_parser.add_subparsers(dest="action", required=True)
    skills_list = skills_sub.add_parser("list", help="List skills/*/SKILL.md")
    skills_list.set_defaults(func=list_skills)

    docs_parser = subparsers.add_parser("docs", help="Inspect course documents")
    docs_sub = docs_parser.add_subparsers(dest="action", required=True)
    docs_list = docs_sub.add_parser("list", help="List docs/en and docs/zh")
    docs_list.set_defaults(func=list_docs)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
