from __future__ import annotations

import json
from pathlib import Path

from agent_lab.cli import main
from agent_lab.docs import load_docs
from agent_lab.skills import load_skills
from agent_lab.tasks import load_tasks


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
