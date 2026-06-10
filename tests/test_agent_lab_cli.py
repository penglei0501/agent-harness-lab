from __future__ import annotations

import json
from pathlib import Path

from agent_lab.cli import main
from agent_lab.docs import load_docs
from agent_lab.events import append_event, load_events, tail_events
from agent_lab.papers import generate_notes_for_folder, generate_paper_note
from agent_lab.recipes import list_recipe_reports, suggest_recipe, suggest_recipe_options
from agent_lab.runtime import HarnessRuntime
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


def test_cli_demo_seed_is_non_destructive(tmp_path: Path, capsys) -> None:
    events_path = tmp_path / "events.jsonl"
    base_args = [
        "demo",
        "--tasks-dir",
        str(tmp_path),
        "--events-path",
        str(events_path),
        "seed",
    ]

    assert main(base_args) == 0
    seeded = capsys.readouterr()
    assert "Seeded demo tasks" in seeded.out

    tasks = load_tasks(tmp_path)
    assert len(tasks) == 4
    assert any(task.status == "in_progress" for task in tasks)
    assert any(task.blocked_by for task in tasks)

    events = load_events(events_path)
    assert [event.event_type for event in events].count("task_created") == 4
    assert [event.event_type for event in events].count("task_completed") == 2

    assert main(base_args) == 0
    repeated = capsys.readouterr()
    assert "Demo tasks already exist" in repeated.out
    assert len(load_tasks(tmp_path)) == 4


def test_generate_paper_note_from_text_file(tmp_path: Path) -> None:
    paper_path = tmp_path / "sample-paper.txt"
    output_dir = tmp_path / "notes"
    events_path = tmp_path / "events.jsonl"
    paper_path.write_text(
        """A Tiny Agent Harness Study

Abstract
This paper studies lightweight agent harnesses for software engineering tasks.

Introduction
Research students need repeatable tools for reading agent behavior.

Method
We combine task logs, event streams, and structured Markdown notes.

Experiments
We evaluate the workflow on classroom paper reading examples.

Conclusion
The harness improves traceability for student research workflows.
""",
        encoding="utf-8",
    )

    note = generate_paper_note(paper_path, output_dir=output_dir, events_path=events_path)

    assert note.title == "A Tiny Agent Harness Study"
    assert note.note_path.exists()
    note_text = note.note_path.read_text(encoding="utf-8")
    assert "## 2. Research Background" in note_text
    assert "## 8. Research Discussion Questions" in note_text
    assert "## 9. Research Follow-up Ideas" in note_text
    assert "task logs, event streams" in note_text

    events = load_events(events_path)
    assert [event.event_type for event in events] == [
        "paper_read",
        "paper_note_generated",
    ]
    assert events[0].payload["title"] == "A Tiny Agent Harness Study"


def test_generate_notes_for_folder_and_cli(tmp_path: Path, capsys) -> None:
    input_dir = tmp_path / "papers"
    output_dir = tmp_path / "notes"
    events_path = tmp_path / "events.jsonl"
    input_dir.mkdir()
    (input_dir / "one.md").write_text("# First Research Paper\n\nAbstract\nOne.", encoding="utf-8")
    (input_dir / "two.txt").write_text("Second Research Paper\n\nAbstract\nTwo.", encoding="utf-8")
    (input_dir / "ignore.csv").write_text("nope", encoding="utf-8")

    notes = generate_notes_for_folder(input_dir, output_dir=output_dir, events_path=events_path)
    assert len(notes) == 2

    base_args = [
        "papers",
        "--output-dir",
        str(output_dir),
        "--events-path",
        str(events_path),
    ]
    assert main([*base_args, "list"]) == 0
    listed = capsys.readouterr()
    assert "one" in listed.out
    assert "two" in listed.out

    single_path = input_dir / "one.md"
    assert main([*base_args, "read", str(single_path)]) == 0
    generated = capsys.readouterr()
    assert "Generated paper note" in generated.out


def test_suggest_recipe_writes_structured_json(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    report = suggest_recipe(
        "egg,tomato,rice",
        servings=1,
        time_minutes=20,
        taste="light",
        avoid="spicy",
        tools="pan",
        output_dir=tmp_path,
        events_path=events_path,
    )

    assert report.title == "Tomato Egg Rice Bowl"
    assert report.path is not None
    assert report.path.exists()
    assert report.steps[0].order == 1
    assert "egg" in report.ingredients_used

    data = json.loads(report.path.read_text(encoding="utf-8"))
    assert data["title"] == "Tomato Egg Rice Bowl"
    assert data["servings"] == 1
    assert [step["title"] for step in data["steps"]] == [
        "Prep ingredients",
        "Scramble eggs",
        "Cook tomato sauce",
        "Combine and season",
        "Top the rice",
    ]
    assert "Spoon the tomato eggs over rice" in data["steps"][-1]["description"]
    assert data["shopping_list"]

    events = load_events(events_path)
    assert [event.event_type for event in events] == [
        "recipe_requested",
        "recipe_generated",
        "shopping_list_generated",
    ]


def test_suggest_recipe_handles_chinese_inputs_and_serving_tools(tmp_path: Path) -> None:
    report = suggest_recipe(
        "土豆,牛肉,辣椒,香菜,葱花",
        servings=2,
        time_minutes=20,
        taste="重口",
        tools="盘子",
        output_dir=tmp_path,
        events_path=tmp_path / "events.jsonl",
    )

    assert report.title == "土豆牛肉小炒"
    assert report.summary.startswith("这是一道约 20 分钟完成")
    assert report.difficulty == "简单"
    assert report.tools == ["炒锅"]
    assert [step.title for step in report.steps] == [
        "处理食材",
        "腌牛肉",
        "快炒牛肉",
        "炒土豆辣椒",
        "回锅合炒",
    ]
    assert "盘子" not in " ".join(step.description for step in report.steps)
    assert "牛肉逆纹切薄片" in report.steps[0].description
    assert "马上盛出避免变老" in report.steps[2].description
    assert sum(step.time_minutes for step in report.steps) == 20
    assert "盐" in report.missing_ingredients
    assert "食用油" in report.missing_ingredients
    assert "生抽" in report.shopping_list
    assert "葱花" not in report.missing_ingredients

    data = json.loads(report.path.read_text(encoding="utf-8"))
    assert data["title"] == "土豆牛肉小炒"
    assert data["steps"][0]["title"] == "处理食材"


def test_suggest_recipe_recommends_tools_when_not_provided(tmp_path: Path) -> None:
    report = suggest_recipe(
        "鸡蛋,番茄,面条",
        servings=1,
        time_minutes=15,
        taste="清淡",
        output_dir=tmp_path,
        events_path=tmp_path / "events.jsonl",
    )

    assert report.title == "番茄鸡蛋面"
    assert report.tools == ["汤锅"]
    assert [step.title for step in report.steps] == [
        "处理食材",
        "炒番茄鸡蛋浇头",
        "煮面",
        "组合装碗",
    ]
    assert "面条刚熟后捞出" in report.steps[2].description


def test_suggest_recipe_options_generates_multiple_reports(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    reports = suggest_recipe_options(
        "鸡蛋,番茄,米饭",
        servings=1,
        time_minutes=20,
        taste="家常",
        output_dir=tmp_path,
        events_path=events_path,
    )

    assert [report.title for report in reports] == [
        "番茄鸡蛋盖饭",
        "番茄蛋炒饭",
        "番茄鸡蛋汤泡饭",
    ]
    assert all(report.path and report.path.exists() for report in reports)
    assert all(report.recommendation_reason for report in reports)

    data = json.loads(reports[0].path.read_text(encoding="utf-8"))
    assert data["recommendation_reason"] == "最快，适合一人食或工作日晚餐。"
    assert [step["title"] for step in data["steps"]] == [
        "处理食材",
        "先炒鸡蛋",
        "炒番茄出汁",
        "回锅调味",
        "盖饭装盘",
    ]
    assert "浇在米饭上" in data["steps"][-1]["description"]

    events = load_events(events_path)
    assert [event.event_type for event in events] == [
        "recipe_options_requested",
        "recipe_options_generated",
    ]


def test_cli_recipes_suggest_and_list(tmp_path: Path, capsys) -> None:
    events_path = tmp_path / "events.jsonl"
    base_args = [
        "recipes",
        "--output-dir",
        str(tmp_path),
        "--events-path",
        str(events_path),
    ]

    assert main([
        *base_args,
        "suggest",
        "--ingredients",
        "egg,tomato,rice",
        "--servings",
        "2",
        "--time",
        "25",
        "--taste",
        "savory",
        "--tools",
        "pan",
    ]) == 0
    generated = capsys.readouterr()
    assert "Generated recipe report" in generated.out

    reports = list_recipe_reports(tmp_path)
    assert len(reports) == 1

    assert main([*base_args, "list"]) == 0
    listed = capsys.readouterr()
    assert "tomato-egg-rice-bowl" in listed.out


def test_cli_recipes_suggest_options(tmp_path: Path, capsys) -> None:
    events_path = tmp_path / "events.jsonl"
    base_args = [
        "recipes",
        "--output-dir",
        str(tmp_path),
        "--events-path",
        str(events_path),
    ]

    assert main([
        *base_args,
        "suggest-options",
        "--ingredients",
        "egg,tomato,rice",
        "--servings",
        "1",
        "--time",
        "20",
        "--taste",
        "balanced",
    ]) == 0
    generated = capsys.readouterr()
    assert "Generated 3 recipe options" in generated.out
    assert "tomato-egg-rice-bowl" in generated.out
    assert len(list_recipe_reports(tmp_path)) == 3


def test_harness_runtime_runs_paper_reading_with_plan_skills_and_events(tmp_path: Path) -> None:
    paper_path = tmp_path / "paper.md"
    output_dir = tmp_path / "paper-notes"
    events_path = tmp_path / "events.jsonl"
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "paper-reading"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: paper-reading
description: Read academic papers into structured research notes.
---

# Paper Reading
""",
        encoding="utf-8",
    )
    paper_path.write_text(
        "# Runtime Harness Paper\n\nAbstract\nA runtime coordinates tools and skills.",
        encoding="utf-8",
    )

    runtime = HarnessRuntime(skills_dir=skills_dir, events_path=events_path)
    result = runtime.run(
        "papers.read",
        paper_path=paper_path,
        output_dir=output_dir,
    )

    assert result.action == "papers.read"
    assert result.status == "completed"
    assert result.plan == [
        "Read paper text",
        "Extract coarse research sections",
        "Write structured Markdown note",
        "Record paper reading events",
    ]
    assert result.skills == ["paper-reading"]
    assert result.artifacts["note_path"].endswith("paper.md")
    assert Path(result.artifacts["note_path"]).exists()
    assert result.events == ["paper_read", "paper_note_generated"]


def test_harness_runtime_runs_recipe_options_with_registered_tool(tmp_path: Path) -> None:
    output_dir = tmp_path / "recipes"
    events_path = tmp_path / "events.jsonl"
    runtime = HarnessRuntime(events_path=events_path)

    result = runtime.run(
        "recipes.suggest_options",
        ingredients="鸡蛋,番茄,米饭",
        servings=1,
        time_minutes=20,
        taste="家常",
        output_dir=output_dir,
    )

    assert result.action == "recipes.suggest_options"
    assert result.status == "completed"
    assert result.plan[0] == "Parse available ingredients and constraints"
    assert "recipe-planning" in result.skills
    assert len(result.artifacts["recipe_paths"]) == 3
    assert all(Path(path).exists() for path in result.artifacts["recipe_paths"])
    assert result.events == ["recipe_options_requested", "recipe_options_generated"]
