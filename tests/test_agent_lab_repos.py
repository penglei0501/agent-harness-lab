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


def browser_style_snapshot() -> RepoSnapshot:
    return RepoSnapshot(
        owner="browser-use",
        repo="browser-use",
        html_url="https://github.com/browser-use/browser-use",
        description="Make websites accessible for AI agents.",
        stars=98002,
        forks=10936,
        open_issues=280,
        default_branch="main",
        license_name="MIT License",
        topics=["ai-agents", "browser-automation", "llm", "playwright", "python"],
        languages={"Python": 9000, "Dockerfile": 300, "Shell": 200},
        readme=(
            "<picture><source srcset='logo-dark.png'><img src='logo.png'></picture>\n\n"
            "# Browser Use\n\n"
            "Make websites accessible for AI agents.\n\n"
            "Python API -> Rust core -> Browser harness -> Web task done\n\n"
            "```bash\n"
            "pip install browser-use\n"
            "playwright install chromium\n"
            "python examples/simple.py\n"
            "```\n\n"
            "The agent observes browser state and executes actions online."
        ),
        tree_paths=[
            "README.md",
            "Dockerfile",
            ".github/workflows/test.yaml",
            "browser_use/agent/service.py",
            "browser_use/agent/prompts.py",
            "browser_use/browser/session.py",
            "browser_use/actor/service.py",
            "examples/simple.py",
            "tests/test_agent.py",
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


def test_generate_markdown_report_extracts_commands_and_explains_paths() -> None:
    report = generate_markdown_report(browser_style_snapshot())

    assert "AI Agent" in report
    assert "浏览器自动化" in report
    assert "`browser_use/agent/`：Agent 核心模块" in report
    assert "`browser_use/browser/`：浏览器会话或页面状态管理相关模块" in report
    assert "`browser_use/actor/`：动作执行或浏览器操作封装相关模块" in report
    assert "```bash\npip install browser-use" in report
    assert "playwright install chromium" in report
    assert "python examples/simple.py" in report
    assert "Python API -> Rust core" not in report
    assert "<picture>" not in report
    assert "srcset" not in report
    assert "README 通常用于说明" not in report


def test_generate_markdown_report_has_contextual_improvement_suggestions() -> None:
    report = generate_markdown_report(browser_style_snapshot())

    assert "## 10. 后续改进建议" in report
    assert "针对 `browser_use/agent/`" in report
    assert "补充架构图或执行流程图" in report
    assert "对 Open Issues 进行分类" in report
    assert "补充更清晰的安装、运行和配置说明" not in report
    assert "为核心模块补充测试和最小可运行示例" not in report


def test_generate_markdown_report_avoids_false_positive_project_context() -> None:
    report = generate_markdown_report(sample_snapshot())

    assert "Agent workflow" in report
    assert "AI Agent 浏览器自动化" not in report
    assert "RAG 信号" not in report
    assert "针对 `agent_demo/runtime.py`" in report


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
