from __future__ import annotations

from pathlib import Path

from agent_lab.cli import main
from agent_lab.events import load_events
from agent_lab.repos import (
    RepoSnapshot,
    generate_markdown_report,
    list_repo_reports,
    parse_github_url,
    summarize_github_repo,
)
from agent_lab.runtime import HarnessRuntime


def sample_snapshot() -> RepoSnapshot:
    return RepoSnapshot(
        owner="example",
        repo="agent-demo",
        html_url="https://github.com/example/agent-demo",
        description="A small agent runtime demo.",
        stars=42,
        forks=7,
        open_issues=3,
        default_branch="main",
        license_name="MIT License",
        topics=["agent", "python"],
        languages={"Python": 9000, "TypeScript": 1000},
        readme=(
            "# Agent Demo\n\n"
            "Install with `pip install -r requirements.txt`.\n\n"
            "Run with `python -m agent_demo`.\n\n"
            "This project demonstrates agent tool use and event logging."
        ),
        tree_paths=[
            "README.md",
            "requirements.txt",
            "agent_demo/runtime.py",
            "agent_demo/tools.py",
            "tests/test_runtime.py",
            ".github/workflows/ci.yml",
        ],
    )


def test_parse_github_url_accepts_common_repo_urls() -> None:
    assert parse_github_url("https://github.com/example/agent-demo").owner == "example"
    assert parse_github_url("https://github.com/example/agent-demo.git").repo == "agent-demo"
    assert parse_github_url("https://github.com/example/agent-demo/tree/main").repo == "agent-demo"


def test_generate_markdown_report_is_developer_focused() -> None:
    report = generate_markdown_report(sample_snapshot())

    assert "# example/agent-demo 仓库技术分析" in report
    assert "## 4. 技术栈判断" in report
    assert "## 8. 工程质量观察" in report
    assert "Python, TypeScript" in report
    assert "`agent_demo/runtime.py`" in report
    assert "pytest / test" in report
    assert "简历" not in report
    assert "面试" not in report


def test_summarize_github_repo_writes_report_and_events(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    output_dir = tmp_path / "repo-reports"

    report = summarize_github_repo(
        "https://github.com/example/agent-demo",
        output_dir=output_dir,
        events_path=events_path,
        fetcher=lambda _: sample_snapshot(),
    )

    assert report.path.exists()
    assert report.path == output_dir / "example-agent-demo.md"
    assert "仓库技术分析" in report.markdown
    assert list_repo_reports(output_dir) == [report.path]

    events = load_events(events_path)
    assert [event.event_type for event in events] == [
        "repo_summary_requested",
        "repo_summary_generated",
    ]
    assert events[-1].payload["repo"] == "example/agent-demo"


def test_harness_runtime_runs_repo_summary(tmp_path: Path) -> None:
    output_dir = tmp_path / "repo-reports"
    events_path = tmp_path / "events.jsonl"
    runtime = HarnessRuntime(events_path=events_path)

    result = runtime.run(
        "repos.summarize",
        github_url="https://github.com/example/agent-demo",
        output_dir=output_dir,
        fetcher=lambda _: sample_snapshot(),
    )

    assert result.action == "repos.summarize"
    assert result.status == "completed"
    assert result.plan == [
        "Parse GitHub repository URL",
        "Fetch repository metadata, README, languages, and tree",
        "Infer technology stack and important paths",
        "Write structured Markdown repository report",
        "Record repository insight events",
    ]
    assert "github-repo-insight" in result.skills
    assert Path(result.artifacts["report_path"]).exists()
    assert result.events == ["repo_summary_requested", "repo_summary_generated"]


def test_cli_repos_summarize_and_list(tmp_path: Path, monkeypatch, capsys) -> None:
    import agent_lab.repos as repos

    monkeypatch.setattr(repos, "fetch_repo_snapshot", lambda _: sample_snapshot())
    events_path = tmp_path / "events.jsonl"
    output_dir = tmp_path / "repo-reports"
    base_args = [
        "repos",
        "--output-dir",
        str(output_dir),
        "--events-path",
        str(events_path),
    ]

    assert main([*base_args, "summarize", "https://github.com/example/agent-demo"]) == 0
    generated = capsys.readouterr()
    assert "Generated repo report" in generated.out
    assert "example-agent-demo.md" in generated.out

    assert main([*base_args, "list"]) == 0
    listed = capsys.readouterr()
    assert "example-agent-demo" in listed.out
