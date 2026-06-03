# Agent Harness Lab

A Python + Next.js lab for learning and visualizing coding agent harness architecture.

这是一个用于学习、实验和可视化编程 Agent Harness 架构的工程项目。项目以 Claude Code 类编程 Agent 的核心机制为研究对象，用 Python 实现一组递进式 agent runtime 示例，并用 Next.js 构建可视化学习站，帮助理解一个模型如何通过工具、上下文、任务系统和执行环境完成真实软件工程工作。

核心观点：

```text
Agent Product = Model + Harness

Harness = Tools
        + Knowledge
        + Observation
        + Action Interfaces
        + Permissions
        + Context Management
        + Task Runtime
```

模型负责推理和决策，Harness 负责提供可观察、可执行、可控制的工作环境。

## Project Highlights

- 实现最小 agent loop：支持 `tool_use -> tool_result -> continue` 的多轮工具调用流程。
- 设计工具注册与分发机制：将 shell、文件读写、编辑、任务管理等能力抽象为可组合工具。
- 实现 Todo 和持久化任务系统：支持多步任务规划、任务依赖、状态流转和长期目标管理。
- 新增 `agent_lab` CLI：支持本地任务创建、查看、认领、完成，以及 skills/docs 资产索引。
- 新增 JSONL 事件日志：记录任务创建、认领、完成等本地运行时事件。
- 新增 Web Dashboard：聚合展示任务状态、技能索引、文档统计和事件日志概览。
- 实现 Subagent 上下文隔离：将探索性任务放入独立 `messages[]`，减少主上下文污染。
- 实现 Skill 按需加载：只在需要时加载领域知识，降低 system prompt 占用。
- 实现上下文压缩策略：通过微压缩、自动压缩和手动压缩支撑长会话。
- 实现后台任务机制：长时间命令异步执行，完成后通过通知回到 agent loop。
- 实现多 Agent 团队协作：基于 JSONL mailbox 的队友身份、消息通信和协议握手。
- 实现 Git worktree 任务隔离：让并行任务在独立目录中执行，减少文件冲突。
- 构建 Next.js 可视化学习站：展示课程文档、执行流程、架构演进和代码差异。
- 配置 Python 与 Web CI：使用 pytest、TypeScript check 和 Next.js build 做基础质量保障。

## Tech Stack

- Python 3.11+
- Anthropic SDK
- pytest
- TypeScript
- React
- Next.js
- Tailwind CSS
- Git worktree
- JSON / JSONL
- Markdown content extraction
- GitHub Actions

## Repository Structure

```text
.
├── agents/                  # 12 个递进式 Agent Harness 示例 + 综合实现
├── agent_lab/               # 个人扩展的 Agent Harness Lab CLI
├── docs/                    # 中英文课程内容源
├── skills/                  # Skill 按需加载示例
├── web/                     # Next.js 可视化学习站
├── tests/                   # Agent 脚本 smoke tests
├── data_pipeline/           # 数据处理流水线练习模块
├── my_package/              # Python 包与测试练习
├── .github/workflows/       # CI 配置
├── requirements.txt         # Python 依赖
└── README.md                # 项目说明
```

## Learning Path

`agents/` 目录按照从简单到复杂的顺序组织：

| Session | Topic | What It Demonstrates |
| --- | --- | --- |
| s01 | Agent Loop | 最小模型-工具循环 |
| s02 | Tool Use | 工具注册与 dispatch map |
| s03 | TodoWrite | 多步任务规划 |
| s04 | Subagent | 子任务上下文隔离 |
| s05 | Skills | 知识按需加载 |
| s06 | Context Compact | 长上下文压缩 |
| s07 | Task System | 文件持久化任务图 |
| s08 | Background Tasks | 慢任务后台执行 |
| s09 | Agent Teams | 持久队友与异步邮箱 |
| s10 | Team Protocols | request-response 协议 |
| s11 | Autonomous Agents | 自主扫描和认领任务 |
| s12 | Worktree Isolation | task 与 git worktree 绑定 |
| s_full | Full Reference | 多机制综合参考实现 |

## Architecture

```text
User Request
    |
    v
messages[]
    |
    v
LLM / Agent Model
    |
    | tool_use
    v
Tool Dispatch
    |
    +-- Shell / Bash
    +-- File Read / Write / Edit
    +-- Todo Manager
    +-- Skill Loader
    +-- Context Compactor
    +-- Background Runner
    +-- Task Store
    +-- Team Mailbox
    +-- Worktree Manager
    |
    v
tool_result
    |
    v
messages[] continues until the model stops using tools
```

## Getting Started

### 1. Agent Lab CLI

This project includes a lightweight CLI for inspecting local harness assets:

```bash
python -m agent_lab --help
python -m agent_lab tasks create "Build Web Dashboard" --description "Show tasks and skills"
python -m agent_lab tasks list
python -m agent_lab tasks show 6
python -m agent_lab tasks claim 6 --owner penglei
python -m agent_lab tasks complete 6
python -m agent_lab events list
python -m agent_lab events tail --limit 10
python -m agent_lab skills list
python -m agent_lab docs list
```

It provides a project-specific tooling layer over the task board, event log, skill files, and course content. Task commands persist local state in `.tasks/task_N.json`; task lifecycle events are appended to `.agent_lab/events.jsonl`, which can later feed a Web dashboard or runtime timeline.

### 2. Python Agent Examples

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` from the example file and set your model configuration:

```bash
cp .env.example .env
```

Then run a teaching session:

```bash
python agents/s01_agent_loop.py
python agents/s_full.py
```

### 3. Web Visualization

```bash
cd web
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

Dashboard routes:

```text
http://localhost:3000/en/dashboard
http://localhost:3000/zh/dashboard
```

`npm run dev` automatically runs `npm run extract` first, which extracts Markdown course content and dashboard data into `web/src/data/generated/`.

### 4. Tests

Run Python tests:

```bash
source .venv/bin/activate
python -m pytest
```

Run Web checks:

```bash
cd web
npm run build
```

## Project Summary

```text
Agent Harness Lab
基于 Python + Next.js 构建的编程 Agent Harness 学习与可视化系统，复现 Claude Code 类 Agent 的核心运行机制，包括工具调用循环、任务规划、Subagent 隔离、Skill 按需加载、上下文压缩、后台任务、多 Agent 协作和 Git worktree 隔离执行。
```

Implemented capabilities:

```text
- 实现模型驱动的 agent loop，支持 tool_use 到 tool_result 的多轮执行机制。
- 设计可扩展工具分发层，将 shell、文件操作、任务管理、技能加载等能力抽象为可组合工具。
- 抽象 `agent_lab` CLI，支持任务创建、查看、认领、完成和 JSON 文件持久化。
- 实现基于 JSONL 的事件日志系统，记录任务生命周期并支持 `events list/tail` 查询。
- 构建 Web Dashboard，聚合展示 tasks、skills、docs 和 events 的本地运行状态。
- 实现文件持久化 DAG 任务系统和 JSONL mailbox，支持多 Agent 协作、任务认领和协议握手。
- 使用 Next.js 构建可视化学习站，展示 Agent Harness 的架构演进、执行流程和课程内容。
- 配置 pytest 与 GitHub Actions，保障 Python 示例和 Web 构建稳定性。
```

## Future Improvements

- 抽象统一 CLI，例如 `agent-lab run --mode s03`、`agent-lab tasks list`。
- 扩展 Dashboard，加入工具调用、任务依赖图、team inbox 和 worktree 状态。
- 增强任务系统，加入 priority、labels、retry 和更完整的依赖解锁策略。
- 增加端到端 Demo，让用户从 Web 页面触发一次 agent task 并观察执行流程。
- 补充架构图、截图和部署链接，使项目更适合公开展示。

## Project Origin

本项目基于 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 的学习材料和示例代码进行整理、实验和扩展，目标是将 Claude Code 类编程 Agent 的 Harness 机制沉淀为一个可运行、可测试、可视化的个人学习项目。

原项目保留为本地 upstream，本仓库作为个人学习与改进版本维护。

## License

MIT License.
