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
        "browser",
        "actor",
        "runtime",
        "tools",
        "server/",
        "api/",
        "docs/",
        "examples/",
        "tests/",
        "config",
    ]
    selected = [path for path in paths if any(keyword in path.lower() for keyword in keywords)]
    return selected[:limit]


def _clean_readme_text(readme: str) -> str:
    text = re.sub(r"(?is)<picture.*?</picture>", " ", readme)
    text = re.sub(r"(?is)<svg.*?</svg>", " ", text)
    text = re.sub(r"(?is)<img\b[^>]*>", " ", text)
    text = re.sub(r"(?is)<source\b[^>]*>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[!\[[^\]]*]\([^)]*\)]\([^)]*\)", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_readme_commands(readme: str, limit: int = 12) -> list[str]:
    """Extract likely install/run commands from README text."""
    cleaned = _clean_readme_text(readme)
    command_prefixes = (
        "pip ",
        "uv ",
        "poetry ",
        "python ",
        "python3 ",
        "npm ",
        "pnpm ",
        "yarn ",
        "bun ",
        "npx ",
        "docker ",
        "docker-compose ",
        "git clone ",
        "cd ",
        "pytest",
        "playwright ",
    )
    commands: list[str] = []
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        line = re.sub(r"^(```\w*|```)$", "", line).strip()
        line = re.sub(r"^[$>#]\s*", "", line).strip()
        if not line or line.startswith("#"):
            continue
        lower_line = line.lower()
        is_make_command = line.startswith("make ")
        is_lowercase_command = line == lower_line and lower_line.startswith(command_prefixes)
        if (is_lowercase_command or is_make_command) and line not in commands:
            commands.append(line)
        if len(commands) >= limit:
            break
    return commands


def infer_project_context(snapshot: RepoSnapshot) -> list[str]:
    """Infer concrete use-case bullets from metadata and repository signals."""
    topics = {topic.lower() for topic in snapshot.topics}
    description = snapshot.description.lower()
    readme = snapshot.readme.lower()
    path_text = " ".join(snapshot.tree_paths).lower()
    haystack = " ".join([description, " ".join(topics), readme, path_text])
    contexts: list[str] = []
    has_browser_automation = (
        "browser-automation" in topics
        or "browser automation" in haystack
        or "control browser" in haystack
        or "browser_use/" in path_text
    )
    if has_browser_automation and ("agent" in haystack or "llm" in haystack):
        contexts.append("面向 AI Agent 浏览器自动化场景，适合网页操作、在线任务执行和页面信息提取。")
    if "agent" in haystack:
        contexts.append("包含 Agent workflow 信号，适合观察任务规划、工具调用和运行时组织方式。")
    if re.search(r"\brag\b", haystack):
        contexts.append("包含 RAG 信号，适合分析检索增强生成的数据流和组件边界。")
    if "next" in haystack or "react" in haystack:
        contexts.append("包含 Web 应用信号，适合分析前端页面、API 路由和交互流程。")
    if "docker" in haystack:
        contexts.append("包含容器化信号，适合关注部署环境和服务编排方式。")
    if not contexts:
        contexts.append(f"面向需要理解、运行或复用 `{snapshot.repo}` 的开发者。")
    return contexts


def describe_important_paths(paths: list[str], limit: int = 14) -> list[str]:
    """Explain important directories/files instead of only listing raw paths."""
    descriptions: list[str] = []
    seen_keys: set[str] = set()

    def add(key: str, label: str, description: str) -> None:
        if key not in seen_keys:
            seen_keys.add(key)
            descriptions.append(f"`{label}`：{description}")

    for path in paths:
        lower = path.lower()
        parts = path.split("/")
        segments = [part.lower() for part in parts]
        if lower == "readme.md":
            add("readme", "README.md", "项目说明、安装方式、快速开始和核心概念入口。")
        elif lower in {"requirements.txt", "pyproject.toml", "package.json"}:
            add(lower, path, "依赖管理和项目配置文件，可用于判断运行环境。")
        elif lower.startswith(".github/workflows/"):
            add("workflows", ".github/workflows/", "GitHub Actions 自动化流程，通常包含测试、构建、发布或检查任务。")
        elif "dockerfile" in lower or "docker-compose" in lower:
            add("docker", path, "容器化运行或部署相关配置。")
        elif "agent" in segments and len(parts) >= 2:
            add("agent", f"{parts[0]}/agent/", "Agent 核心模块，通常包含任务执行、prompt、消息管理或运行状态逻辑。")
        elif "browser" in segments and len(parts) >= 2:
            add("browser", f"{parts[0]}/browser/", "浏览器会话或页面状态管理相关模块。")
        elif "actor" in segments and len(parts) >= 2:
            add("actor", f"{parts[0]}/actor/", "动作执行或浏览器操作封装相关模块。")
        elif lower.endswith("runtime.py"):
            add(path, path, "运行时协调逻辑，通常负责串联计划、工具、事件或执行流程。")
        elif lower.endswith("tools.py"):
            add(path, path, "工具注册或工具函数集合，通常负责连接外部能力和内部执行逻辑。")
        elif lower.startswith("src/"):
            add("src", "src/", "主要源码目录。")
        elif lower.startswith("app/"):
            add("app", "app/", "应用入口或路由组织目录。")
        elif lower.startswith("docs/"):
            add("docs", "docs/", "项目文档目录。")
        elif lower.startswith("examples/"):
            add("examples", "examples/", "示例代码目录，适合理解典型用法。")
        elif lower.startswith("tests/") or "/tests/" in lower or "test_" in lower:
            add("tests", "tests/", "自动化测试目录或测试文件。")
        if len(descriptions) >= limit:
            break

    return descriptions


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


def infer_improvement_suggestions(snapshot: RepoSnapshot, path_descriptions: list[str]) -> list[str]:
    """Generate repository-specific engineering improvement suggestions."""
    paths = "\n".join(snapshot.tree_paths).lower()
    commands = extract_readme_commands(snapshot.readme)
    suggestions: list[str] = []

    runtime_item = next((item for item in path_descriptions if "runtime.py" in item), "")
    tools_item = next((item for item in path_descriptions if "tools.py" in item), "")

    if runtime_item:
        runtime_label = runtime_item.split("：", 1)[0]
        suggestions.append(f"针对 {runtime_label} 补充 Harness Runtime 执行流程图，说明 planner、tool registry、skill selection 和 event log 的调用顺序。")
    if tools_item:
        tools_label = tools_item.split("：", 1)[0]
        suggestions.append(f"围绕 {tools_label} 补充工具注册表说明，列出 action 名称、输入参数、输出产物和错误处理方式。")
    if any("agent/" in item for item in path_descriptions):
        agent_label = next(
            item.split("：", 1)[0]
            for item in path_descriptions
            if "agent/" in item
        )
        suggestions.append(f"针对 {agent_label} 补充架构图或执行流程图，说明任务计划、prompt、消息管理和工具调用之间的关系。")
    elif path_descriptions and not runtime_item and not tools_item:
        first_label = path_descriptions[0].split("：", 1)[0]
        suggestions.append(f"围绕 {first_label} 补充模块职责说明，帮助读者从目录结构进入核心代码。")

    has_tests = "test" in paths
    has_ci = ".github/workflows" in paths
    has_examples = "examples/" in paths
    has_docker = "dockerfile" in paths or "docker-compose" in paths

    if has_tests:
        suggestions.append("在现有测试基础上补充关键路径覆盖说明，标明哪些模块已有单元测试、集成测试或端到端测试。")
    else:
        suggestions.append("补充最小测试示例，优先覆盖核心模块的输入输出和错误处理。")

    if has_examples:
        suggestions.append("整理 examples 目录中的典型用例，按入门、进阶和真实场景分层组织。")
    else:
        suggestions.append("增加最小可运行示例，降低新用户理解和验证项目行为的成本。")

    if commands:
        suggestions.append("将 README 中的安装、初始化和运行命令整理成 Quick Start，减少用户从长文档中查找命令的成本。")
    else:
        suggestions.append("补充清晰的安装、配置和启动命令，最好提供可复制的 Quick Start。")

    if has_ci and has_docker:
        suggestions.append("把 CI、Docker 和发布流程之间的关系写清楚，方便开发者理解本地运行与线上构建的差异。")
    elif has_ci:
        suggestions.append("说明 CI workflow 的触发条件和检查内容，方便贡献者理解质量门禁。")
    elif has_docker:
        suggestions.append("补充 Docker 使用场景，说明它适合开发、测试还是部署。")

    if snapshot.open_issues > 100:
        suggestions.append("对 Open Issues 进行分类，例如 bug、feature、documentation 和 question，降低维护和检索成本。")

    unique: list[str] = []
    for suggestion in suggestions:
        if suggestion not in unique:
            unique.append(suggestion)
    return unique[:6]


def _readme_preview(readme: str) -> str:
    compact = re.sub(r"\s+", " ", _clean_readme_text(readme)).strip()
    return textwrap.shorten(compact, width=800, placeholder="...") if compact else "README 未获取到内容。"


def _render_run_flow(readme: str) -> str:
    commands = extract_readme_commands(readme)
    if not commands:
        return _readme_preview(readme)
    command_block = "\n".join(commands)
    return f"""README 中识别到以下安装或运行命令：

```bash
{command_block}
```"""


def generate_markdown_report(snapshot: RepoSnapshot) -> str:
    """Generate a developer-focused Markdown report from a repository snapshot."""
    languages = top_languages(snapshot.languages)
    tech_stack = infer_tech_stack(snapshot)
    important_paths = pick_important_paths(snapshot.tree_paths)
    path_descriptions = describe_important_paths(important_paths)
    project_context = infer_project_context(snapshot)
    suggestions = infer_improvement_suggestions(snapshot, path_descriptions)
    topics = ", ".join(snapshot.topics) if snapshot.topics else "暂无 topics"
    license_name = snapshot.license_name or "未声明"

    return f"""# {snapshot.owner}/{snapshot.repo} 仓库技术分析

## 1. 一句话总结

{snapshot.description or "这个仓库没有填写 GitHub description，需要结合 README 和目录结构进一步判断。"}

## 2. 项目目标与使用场景

{chr(10).join(f"- {item}" for item in project_context)}

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

{chr(10).join(f"- {item}" for item in path_descriptions) if path_descriptions else "- 暂未识别到典型关键目录或配置文件。"}

## 6. 核心模块分析

{chr(10).join(f"- {item}" for item in path_descriptions[:8]) if path_descriptions else "- 当前只能从 README、语言统计和目录树进行粗粒度分析，具体模块职责仍需要结合源码逐文件确认。"}

## 7. 主要运行流程

{_render_run_flow(snapshot.readme)}

## 8. 工程质量观察

{chr(10).join(f"- {item}" for item in engineering_observations(snapshot))}

## 9. 潜在风险或不足

{chr(10).join(f"- {item}" for item in infer_risks(snapshot))}

## 10. 后续改进建议

{chr(10).join(f"- {item}" for item in suggestions)}
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
