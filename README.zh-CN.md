# Agent Harness Lab

[English](README.md) | 简体中文

Agent Harness Lab 是一个基于 Python + Next.js 的 Agent Harness 学习、实验与可视化项目。它通过 12 个递进式 Agent 示例展示工具调用、任务规划、Skill 加载、上下文压缩、后台任务、多 Agent 协作和 worktree 隔离等机制，并在此基础上扩展了科研论文助手、智能食谱助手和 GitHub 仓库洞察助手，展示同一套 Harness 如何扩展到不同领域工作流。

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

## 项目亮点

- 最小 Agent Loop 支持 `tool_use -> tool_result -> continue` 的多轮工具调用流程。
- 工具注册与分发机制将 shell、文件读写、编辑、任务管理等能力抽象为可组合工具。
- 统一 `HarnessRuntime` 串联任务计划、Skill 选择、工具注册、执行产物收集和事件记录。
- Todo 与持久化任务系统支持多步任务规划、任务依赖、状态流转和长期目标管理。
- `agent_lab` CLI 提供任务、事件、技能、文档、论文助手、食谱助手和仓库洞察助手的本地操作入口。
- JSONL 事件日志记录任务创建、认领、完成、论文报告生成、食谱方案生成和仓库报告生成等运行时事件。
- Next.js Web Dashboard 展示任务状态、技能索引、文档统计、事件时间线和任务依赖图。
- 科研论文助手支持 PDF / Markdown / text 上传，并生成结构化科研阅读报告。
- Research Skill Pack 将论文阅读、方法分析、实验分析和科研报告写作沉淀为可复用 Skill。
- 智能食谱助手根据已有食材推荐多个结构化 JSON 食谱方案，给出推荐理由、自动推荐厨具并生成具体烹饪步骤。
- Life Skill Pack 沉淀食谱规划、烹饪步骤和基础营养提醒能力。
- GitHub 仓库洞察助手基于公开仓库元信息、README、语言统计和目录树生成面向开发者的技术分析报告。
- pytest、TypeScript check、Next.js build 和 GitHub Actions 提供基础质量保障。

## 项目结构

```text
.
├── agents/                  # 12 个递进式 Agent Harness 示例 + 综合实现
├── agent_lab/               # 个人扩展的 runtime、工具注册、planner 和 CLI
├── docs/                    # 中英文课程内容源
├── papers/                  # 本地论文输入与报告输出目录，可按需创建
├── recipes/                 # 本地结构化食谱 JSON 报告
├── github_reports/          # 本地 GitHub 仓库洞察报告
├── skills/                  # Skill 按需加载示例、Research Skill Pack 和 Life Skill Pack
├── web/                     # Next.js 可视化学习站、论文助手和食谱页面
├── tests/                   # Python 测试
├── .github/workflows/       # CI 配置
├── requirements.txt         # Python 依赖
└── README.md                # 英文说明
```

## Harness Runtime

项目现在把领域工作流统一接入一个轻量 runtime，而不是让 CLI 或 Web API 直接调用各个功能模块：

```text
CLI / Web API
  -> HarnessRuntime
  -> Planner
  -> Skill selection
  -> Tool registry
  -> Paper / Recipe / Repository tool
  -> Artifact writer
  -> JSONL event log
```

这样论文助手、食谱助手和仓库洞察助手都遵循同一套 Harness 契约：每个 action 都有执行计划、关联 Skill、注册工具、输出产物和运行时事件记录。

## 学习路径

| Session | Topic | 展示内容 |
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

## 快速开始

克隆仓库并安装 Python 依赖：

```bash
git clone https://github.com/penglei0501/agent-harness-lab.git
cd agent-harness-lab

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

启动 Web 页面：

```bash
cd web
npm install
npm run dev
```

打开 Web 助手：

```text
http://localhost:3000/zh/demo
http://localhost:3000/zh/papers
http://localhost:3000/zh/recipes
http://localhost:3000/zh/repos
```

Demo 截图可以保存为：

```text
web/public/demo/dashboard.png
web/public/demo/papers.png
web/public/demo/recipes.png
```

常用命令：

```bash
cd /path/to/agent-harness-lab
python -m agent_lab demo seed
python -m agent_lab papers read papers/input/example.pdf
python -m agent_lab recipes suggest-options --ingredients "egg,tomato,rice" --servings 1 --time 20
python -m agent_lab repos summarize https://github.com/browser-use/browser-use
python -m agent_lab tasks list
python -m agent_lab events list
```

本地运行数据不会提交到 Git，包括 `.tasks/`、`.agent_lab/`、`papers/input/`、`papers/output/`、`recipes/output/` 和 `github_reports/output/`。

## 论文助手

论文助手是 Agent Harness Lab 的科研知识扩展，不改变项目主线。它展示一个通用 Harness 如何扩展到研究生科研工作流。

支持两种使用方式：

```bash
python -m agent_lab papers read papers/input/example.pdf
python -m agent_lab papers read-folder papers/input
```

也可以打开 Web 页面拖拽上传：

```text
http://localhost:3000/zh/papers
```

生成的 Markdown 报告保存在：

```text
papers/output/
```

报告结构包括：

```text
Basic Info
Research Background
Research Gap
Method
Experiments
Results and Conclusion
Limitations
Research Discussion Questions
Research Follow-up Ideas
Concise Research Summary
```

## Research Skill Pack

```text
paper-reading             整体论文结构化阅读流程
method-analysis           方法、模型、算法、系统和假设分析
experiment-analysis       数据集、baseline、指标、消融和结果分析
research-report-writing   结构化科研阅读报告生成
```

这些 Skill 位于 `skills/` 目录，用于展示 Agent 如何按需加载领域知识，而不是只依赖一次性 Prompt。

## 智能食谱助手

食谱助手是生活知识扩展。和论文助手不同，食谱助手不输出 Markdown，而是输出结构化 JSON，方便后续 Web 页面渲染成菜谱卡片、食材标签、步骤时间线、购物清单和替代方案。用户只需要输入食材和约束，系统会推荐多个候选方案，并自动推荐合适厨具。

Web 页面可以直接输入食材并生成菜谱：

```text
http://localhost:3000/zh/recipes
```

网页端会调用本地 Next.js API，再由 API 调用 `agent_lab recipes suggest-options` 生成多个 JSON 菜谱方案。

```bash
python -m agent_lab recipes suggest-options \
  --ingredients "egg,tomato,rice" \
  --servings 1 \
  --time 20 \
  --taste "light" \
  --avoid "spicy"

python -m agent_lab recipes suggest --ingredients "egg,tomato,rice"
python -m agent_lab recipes list
```

生成的 JSON 报告保存在：

```text
recipes/output/
```

在 Web 页面查看已生成食谱：

```bash
cd web
npm run extract
npm run dev
```

然后打开：

```text
http://localhost:3000/zh/recipes
http://localhost:3000/en/recipes
```

## GitHub 仓库洞察助手

GitHub 仓库洞察助手是一个开发者工具扩展。用户输入公开 GitHub 仓库链接后，系统会通过 GitHub REST API 抓取仓库基本信息、README、语言分布和目录结构，并生成结构化 Markdown 技术分析报告。

CLI 使用方式：

```bash
python -m agent_lab repos summarize https://github.com/browser-use/browser-use
python -m agent_lab repos list
```

Web 使用方式：

```text
http://localhost:3000/zh/repos
http://localhost:3000/en/repos
```

生成的报告保存在：

```text
github_reports/output/
```

报告结构包括：

```text
一句话总结
项目目标与使用场景
仓库基本信息
技术栈判断
目录结构说明
核心模块分析
README 中的运行线索
工程质量观察
潜在风险或不足
后续工程改进建议
```

这个助手专注于技术理解和工程分析。

## Life Skill Pack

```text
recipe-planning          根据食材和约束生成可执行食谱方案
cooking-instructions     生成清晰、有时间估计、便于厨房执行的步骤
nutrition-awareness      提供基础饮食提醒，但不提供医疗建议
```

## Web 页面

```bash
cd web
npm run dev
```

常用页面：

```text
http://localhost:3000/zh/demo
http://localhost:3000/zh/dashboard
http://localhost:3000/zh/papers
http://localhost:3000/zh/recipes
http://localhost:3000/zh/timeline
```

`npm run dev` 会先运行 `npm run extract`，把课程文档、任务、事件、技能、论文报告和食谱 JSON 数据提取到 `web/src/data/generated/`。

## 测试

运行 Python 测试：

```bash
source .venv/bin/activate
python -m pytest
```

运行 Web 构建：

```bash
cd web
npm run build
```

## 后续计划

- 为论文助手接入 LLM 总结、引用信息抽取和多篇论文对比报告。
- 增加论文任务规划，让 `papers plan` 自动生成论文阅读任务链。
- 增加章节级缓存和上下文压缩，支持更长论文处理。
- 增加本地论文库检索，将单篇论文助手扩展为本地科研知识库。
- 补充截图、演示 GIF 和在线部署链接。

## 项目来源

本项目基于 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 的学习材料和示例代码进行整理、实验和扩展，目标是将 Claude Code 类编程 Agent 的 Harness 机制沉淀为一个可运行、可测试、可视化的个人学习项目。

原项目保留为本地 upstream，本仓库作为个人学习与改进版本维护。

## License

MIT License.
