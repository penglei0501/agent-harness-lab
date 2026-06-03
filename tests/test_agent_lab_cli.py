from __future__ import annotations

import json
from pathlib import Path

from agent_lab.cli import main
from agent_lab.docs import load_docs
from agent_lab.events import append_event, load_events, tail_events
from agent_lab.skills import load_skills
from agent_lab.tasks import claim_task, complete_task, create_task, load_tasks


def test_load_tasks_from_directory(tmp_path: Path) -> None:
    task_path = tmp_path / "task_2.json"
    task_path.write_text(
        json.dumps({
            "id": 2,
            "subject": "Build CLI",
            "status": "pending",
            "owner": "penglei",
            "blockedBy": [1],
        }),
        encoding="utf-8",
    )

    tasks = load_tasks(tmp_path)

    assert len(tasks) == 1
    assert tasks[0].id == "2"
    assert tasks[0].subject == "Build CLI"
    assert tasks[0].blocked_by == ["1"]


def test_create_claim_and_complete_task(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    task = create_task(
        "Build dashboard",
        description="Add task panels",
        owner="",
        blocked_by=["1", "setup"],
        tasks_dir=tmp_path,
        events_path=events_path,
    )

    assert task.id == "1"
    assert task.status == "pending"
    assert task.blocked_by == ["1", "setup"]

    claimed = claim_task(task.id, "penglei", tmp_path, events_path)
    assert claimed.status == "in_progress"
    assert claimed.owner == "penglei"

    completed = complete_task(task.id, tmp_path, events_path)
    assert completed.status == "completed"

    events = load_events(events_path)
    assert [event.event_type for event in events] == [
        "task_created",
        "task_claimed",
        "task_completed",
    ]
    assert events[0].payload["task_id"] == "1"


def test_event_log_tail(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    append_event("first", {"task_id": "1", "subject": "One"}, events_path=events_path)
    append_event("second", {"task_id": "2", "subject": "Two"}, events_path=events_path)

    events = tail_events(1, events_path)

    assert len(events) == 1
    assert events[0].event_type == "second"


def test_load_skills_reads_frontmatter(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: demo-skill
description: Demo skill for tests.
---

# Demo
""",
        encoding="utf-8",
    )

    skills = load_skills(tmp_path)

    assert len(skills) == 1
    assert skills[0].name == "demo-skill"
    assert skills[0].description == "Demo skill for tests."


def test_load_docs_keeps_english_and_chinese_only(tmp_path: Path) -> None:
    for locale in ("en", "zh", "ja"):
        locale_dir = tmp_path / locale
        locale_dir.mkdir()
        (locale_dir / "s01-demo.md").write_text(f"# Title {locale}\n", encoding="utf-8")

    docs = load_docs(tmp_path)

    assert [doc.locale for doc in docs] == ["en", "zh"]
    assert [doc.title for doc in docs] == ["Title en", "Title zh"]


def test_cli_lists_skills(capsys) -> None:
    exit_code = main(["skills", "list"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "agent-builder" in captured.out
    assert "code-review" in captured.out


def test_cli_task_lifecycle(tmp_path: Path, capsys) -> None:
    events_path = tmp_path / "events.jsonl"
    base_args = [
        "tasks",
        "--tasks-dir",
        str(tmp_path),
        "--events-path",
        str(events_path),
    ]

    assert main([*base_args, "create", "Build CLI", "--owner", "penglei"]) == 0
    created = capsys.readouterr()
    assert "Created task 1" in created.out

    assert main([*base_args, "show", "1"]) == 0
    shown = capsys.readouterr()
    assert "Build CLI" in shown.out

    assert main([*base_args, "claim", "1", "--owner", "alice"]) == 0
    claimed = capsys.readouterr()
    assert "Claimed task 1 for alice" in claimed.out

    assert main([*base_args, "complete", "1"]) == 0
    completed = capsys.readouterr()
    assert "Completed task 1" in completed.out

    assert main([*base_args, "list"]) == 0
    listed = capsys.readouterr()
    assert "completed" in listed.out
    assert "alice" in listed.out

    assert main(["events", "--events-path", str(events_path), "list"]) == 0
    events_listed = capsys.readouterr()
    assert "task_created" in events_listed.out
    assert "task_claimed" in events_listed.out
    assert "task_completed" in events_listed.out

    assert main(["events", "--events-path", str(events_path), "tail", "--limit", "1"]) == 0
    events_tail = capsys.readouterr()
    assert "task_completed" in events_tail.out
    assert "task_created" not in events_tail.out
