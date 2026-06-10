"""GitHub repository insight assistant."""

from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import textwrap
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .events import append_event
from .paths import EVENTS_PATH, GITHUB_REPORTS_OUTPUT_DIR

GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class RepoId:
    owner: str
    repo: str


@dataclass(frozen=True)
class RepoSnapshot:
    owner: str
    repo: str
    html_url: str
    description: str
    stars: int
    forks: int
    open_issues: int
    default_branch: str
    license_name: str | None
    topics: list[str]
    languages: dict[str, int]
    readme: str
    tree_paths: list[str]


@dataclass(frozen=True)
class RepoReport:
    repo: str
    markdown: str
    path: Path


def parse_github_url(url: str) -> RepoId:
    """Parse a GitHub repository URL into owner/repo."""
    parsed = urlparse(url.strip())
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError("Expected a GitHub repository URL, for example https://github.com/owner/repo")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("Could not find owner/repo in GitHub URL")

    return RepoId(owner=parts[0], repo=parts[1].removesuffix(".git"))


def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "agent-harness-lab",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_get(path: str) -> Any:
    """Fetch JSON from the GitHub REST API."""
    request = Request(f"{GITHUB_API}{path}", headers=_github_headers())
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"GitHub resource not found: {path}") from exc
        if exc.code in {403, 429}:
            raise RuntimeError("GitHub API rate limit reached. Set GITHUB_TOKEN to raise the limit.") from exc
        raise


def fetch_readme(owner: str, repo: str) -> str:
    """Fetch and decode the repository README."""
    data = github_get(f"/repos/{owner}/{repo}/readme")
    content = str(data.get("content") or "")
    if data.get("encoding") == "base64" and content:
        return base64.b64decode(content).decode("utf-8", errors="ignore")
    return ""


def fetch_tree(owner: str, repo: str, branch: str) -> list[str]:
    """Fetch repository file paths from the default branch tree."""
    data = github_get(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    tree = data.get("tree", [])
    if not isinstance(tree, list):
        return []
    return [
        str(item.get("path"))
        for item in tree
        if isinstance(item, dict) and item.get("type") == "blob" and item.get("path")
    ]


def fetch_repo_snapshot(github_url: str) -> RepoSnapshot:
    """Fetch metadata needed to generate a developer-focused repository report."""
    repo_id = parse_github_url(github_url)
    repo_data = github_get(f"/repos/{repo_id.owner}/{repo_id.repo}")
    languages = github_get(f"/repos/{repo_id.owner}/{repo_id.repo}/languages")
    default_branch = str(repo_data.get("default_branch") or "main")
    license_info = repo_data.get("license") or {}

    return RepoSnapshot(
        owner=repo_id.owner,
        repo=repo_id.repo,
        html_url=str(repo_data.get("html_url") or github_url),
        description=str(repo_data.get("description") or ""),
        stars=int(repo_data.get("stargazers_count") or 0),
        forks=int(repo_data.get("forks_count") or 0),
        open_issues=int(repo_data.get("open_issues_count") or 0),
        default_branch=default_branch,
        license_name=license_info.get("name") if isinstance(license_info, dict) else None,
        topics=[str(topic) for topic in repo_data.get("topics", [])],
        languages={str(key): int(value) for key, value in dict(languages or {}).items()},
        readme=fetch_readme(repo_id.owner, repo_id.repo),
        tree_paths=fetch_tree(repo_id.owner, repo_id.repo, default_branch),
    )


def top_languages(languages: dict[str, int], limit: int = 5) -> list[str]:
    return [
        name
        for name, _ in sorted(languages.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]


def pick_important_paths(paths: list[str], limit: int = 40) -> list[str]:
    keywords = [
        "readme",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "dockerfile",
        "docker-compose",
        ".github/workflows",
        "src/",
        "app/",
        "agent",
        "server/",
        "api/",
        "docs/",
        "examples/",
        "tests/",
        "config",
    ]
    selected = [path for path in paths if any(keyword in path.lower() for keyword in keywords)]
    return selected[:limit]


def infer_tech_stack(snapshot: RepoSnapshot) -> list[str]:
    paths = "\n".join(snapshot.tree_paths).lower()
    readme = snapshot.readme.lower()
    stack = top_languages(snapshot.languages)

    if "next.config" in paths or "next.js" in readme or "nextjs" in readme:
        stack.append("Next.js")
    if "playwright" in readme or "playwright" in paths:
        stack.append("Playwright")
    if "dockerfile" in paths or "docker-compose" in paths:
        stack.append("Docker")
    if "pytest" in readme or "pytest" in paths:
        stack.append("pytest")
    if ".github/workflows" in paths:
        stack.append("GitHub Actions")
    if "agent" in readme or "agent" in paths:
        stack.append("Agent workflow")

    unique: list[str] = []
    for item in stack:
        if item and item not in unique:
            unique.append(item)
    return unique


def engineering_observations(snapshot: RepoSnapshot) -> list[str]:
    paths = "\n".join(snapshot.tree_paths).lower()
    observations: list[str] = []
    if "test" in paths:
        observations.append("包含 pytest / test 相关文件，具备自动化测试线索。")
    if ".github/workflows" in paths:
        observations.append("包含 GitHub Actions workflow，具备 CI 配置线索。")
    if "dockerfile" in paths or "docker-compose" in paths:
        observations.append("包含 Docker 相关文件，具备容器化部署线索。")
    if "docs/" in paths:
        observations.append("包含 docs 目录，说明项目有额外文档组织。")
    if "examples/" in paths:
        observations.append("包含 examples 目录，便于用户理解典型用法。")
    if not observations:
        observations.append("暂未从目录结构中识别出测试、CI、Docker 或 examples 等工程化线索。")
    return observations


def infer_risks(snapshot: RepoSnapshot) -> list[str]:
    risks: list[str] = []
    readme_len = len(snapshot.readme.strip())
    if readme_len < 500:
        risks.append("README 内容较少，项目目标、安装方式或使用示例可能不够完整。")
    if not snapshot.license_name:
        risks.append("未识别到 License，复用或二次开发前需要确认许可。")
    if snapshot.open_issues > 100:
        risks.append("Open Issues 数量较多，需要关注维护压力和问题响应情况。")
    if not any("test" in path.lower() for path in snapshot.tree_paths):
        risks.append("未识别到测试目录或测试文件，质量保障信息可能不足。")
    if not risks:
        risks.append("未从基础元信息中发现明显风险，仍建议结合源码和 issue 进一步检查。")
    return risks


def _readme_preview(readme: str) -> str:
    compact = re.sub(r"\s+", " ", readme).strip()
    return textwrap.shorten(compact, width=800, placeholder="...") if compact else "README 未获取到内容。"


def generate_markdown_report(snapshot: RepoSnapshot) -> str:
    """Generate a developer-focused Markdown report from a repository snapshot."""
    languages = top_languages(snapshot.languages)
    tech_stack = infer_tech_stack(snapshot)
    important_paths = pick_important_paths(snapshot.tree_paths)
    topics = ", ".join(snapshot.topics) if snapshot.topics else "暂无 topics"
    license_name = snapshot.license_name or "未声明"

    return f"""# {snapshot.owner}/{snapshot.repo} 仓库技术分析

## 1. 一句话总结

{snapshot.description or "这个仓库没有填写 GitHub description，需要结合 README 和目录结构进一步判断。"}

## 2. 项目目标与使用场景

根据仓库描述、README 和目录结构，这个项目主要面向需要理解、运行或复用 `{snapshot.repo}` 的开发者。V1 规则版只根据公开仓库元信息推断，不会编造 README 中没有出现的功能。

## 3. 仓库基本信息

- GitHub 地址：{snapshot.html_url}
- Stars：{snapshot.stars}
- Forks：{snapshot.forks}
- Open Issues：{snapshot.open_issues}
- 默认分支：{snapshot.default_branch}
- License：{license_name}
- Topics：{topics}
- 主要语言：{", ".join(languages) if languages else "暂未识别"}

## 4. 技术栈判断

{chr(10).join(f"- {item}" for item in tech_stack) if tech_stack else "- 暂未从语言统计和关键文件中识别出明确技术栈。"}

## 5. 目录结构说明

{chr(10).join(f"- `{path}`" for path in important_paths) if important_paths else "- 暂未识别到典型关键目录或配置文件。"}

## 6. 核心模块分析

- README 通常用于说明项目目标、安装方式和快速开始。
- 语言统计可以帮助判断主要实现语言。
- 关键源码目录、配置文件、测试目录和 CI 文件可以帮助定位核心工程结构。
- 具体模块职责仍需要结合源码逐文件阅读确认。

## 7. 主要运行流程

{_readme_preview(snapshot.readme)}

## 8. 工程质量观察

{chr(10).join(f"- {item}" for item in engineering_observations(snapshot))}

## 9. 潜在风险或不足

{chr(10).join(f"- {item}" for item in infer_risks(snapshot))}

## 10. 后续改进建议

- 补充更清晰的安装、运行和配置说明。
- 为核心模块补充测试和最小可运行示例。
- 在 README 中增加架构图或模块职责说明。
- 如果项目依赖外部服务，建议提供 `.env.example` 和配置说明。
"""


def _report_filename(snapshot: RepoSnapshot) -> str:
    safe_owner = re.sub(r"[^A-Za-z0-9_.-]+", "-", snapshot.owner).strip("-")
    safe_repo = re.sub(r"[^A-Za-z0-9_.-]+", "-", snapshot.repo).strip("-")
    return f"{safe_owner}-{safe_repo}.md"


def summarize_github_repo(
    github_url: str,
    *,
    output_dir: Path = GITHUB_REPORTS_OUTPUT_DIR,
    events_path: Path = EVENTS_PATH,
    fetcher: Callable[[str], RepoSnapshot] | None = None,
) -> RepoReport:
    """Fetch a GitHub repository and save a structured Markdown insight report."""
    append_event("repo_summary_requested", {"url": github_url}, events_path=events_path)
    snapshot = (fetcher or fetch_repo_snapshot)(github_url)
    markdown = generate_markdown_report(snapshot)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / _report_filename(snapshot)
    path.write_text(markdown, encoding="utf-8")
    repo_name = f"{snapshot.owner}/{snapshot.repo}"
    append_event(
        "repo_summary_generated",
        {"repo": repo_name, "report_path": str(path), "title": repo_name},
        events_path=events_path,
    )
    return RepoReport(repo=repo_name, markdown=markdown, path=path)


def list_repo_reports(output_dir: Path = GITHUB_REPORTS_OUTPUT_DIR) -> list[Path]:
    """Return generated GitHub repository reports."""
    if not output_dir.exists():
        return []
    return sorted(output_dir.glob("*.md"))
