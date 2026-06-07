# Agent Harness Lab

English | [简体中文](README.zh-CN.md)

A Python + Next.js Agent Harness lab for learning, experimenting with, and visualizing coding-agent runtime architecture. The project includes progressive agent examples, a local `agent_lab` CLI, a Web dashboard, and a research knowledge extension that turns PDF / Markdown / text papers into structured research reading reports.

Core idea:

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

The model reasons and decides. The harness provides the observable, executable, and controllable environment around it.

## Project Highlights

- Implements a minimal agent loop with multi-turn `tool_use -> tool_result -> continue` execution.
- Builds a tool registration and dispatch layer for shell, file operations, editing, task management, and skill loading.
- Adds a local `agent_lab` CLI for tasks, events, skills, docs, demo data, and paper reports.
- Persists task state in JSON files and records runtime actions in a local JSONL event log.
- Provides a Next.js dashboard for tasks, skill index, docs inventory, task dependencies, and event timelines.
- Adds a research knowledge extension: paper reading assistant for PDF / Markdown / text files.
- Supports drag-and-drop paper upload in the Web UI and returns generated Markdown reports.
- Adds a Research Skill Pack for paper reading, method analysis, experiment analysis, and research report writing.
- Adds a smart recipe assistant that produces structured JSON recipe reports from available ingredients.
- Adds a Life Skill Pack for recipe planning, cooking instructions, and nutrition-aware notes.
- Demonstrates subagents, context compaction, background tasks, multi-agent coordination, and worktree isolation.
- Uses pytest, TypeScript checks, Next.js build, and GitHub Actions for basic quality coverage.

## Quick Start

Clone the repository and set up Python dependencies:

```bash
git clone https://github.com/penglei0501/agent-harness-lab.git
cd agent-harness-lab

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the Web app:

```bash
cd web
npm install
npm run dev
```

Open the Web assistants:

```text
http://localhost:3000/zh/papers
http://localhost:3000/zh/recipes
```

Useful local commands:

```bash
cd /path/to/agent-harness-lab
python -m agent_lab demo seed
python -m agent_lab papers read papers/input/example.pdf
python -m agent_lab recipes suggest --ingredients "egg,tomato,rice" --servings 1 --time 20
python -m agent_lab tasks list
python -m agent_lab events list
```

Local runtime data such as `.tasks/`, `.agent_lab/`, `papers/input/`, `papers/output/`, and `recipes/output/` is ignored by Git.

## Paper Reading Assistant

The paper assistant is a research knowledge extension built on top of the core Agent Harness Lab. It does not change the main project direction; it demonstrates how a general harness can be extended into a graduate research workflow.

CLI usage:

```bash
mkdir -p papers/input papers/output
python -m agent_lab papers read papers/input/example.pdf
python -m agent_lab papers read-folder papers/input
python -m agent_lab papers list
```

Web usage:

```text
http://localhost:3000/zh/papers
```

The Web page supports local drag-and-drop upload in development/server mode. Uploaded files are saved to `papers/input/`, processed by `agent_lab papers read`, and returned to the page as a Markdown report. Generated notes are saved in `papers/output/`.

Generated reports include:

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

PDF support uses local text extraction when available (`pdftotext`, `pypdf`, or PyMuPDF). Markdown and plain text work without extra dependencies.

## Research Skill Pack

```text
paper-reading             Overall structured paper reading workflow
method-analysis           Method, model, algorithm, system, and assumption analysis
experiment-analysis       Dataset, baseline, metric, ablation, and result analysis
research-report-writing   Structured research report generation
```

These skills live in `skills/` and show how an agent can load domain knowledge on demand instead of relying on one large prompt.

## Smart Recipe Assistant

The recipe assistant is a life knowledge extension. Unlike paper reports, recipe output is stored as structured JSON so the Web UI can later render it as cards, ingredient tags, step timelines, shopping lists, and substitution panels.

The Web page can generate recipes directly from browser input:

```text
http://localhost:3000/zh/recipes
```

The browser calls a local Next.js API route, and the API route invokes `agent_lab recipes suggest` to generate the JSON recipe report.

```bash
python -m agent_lab recipes suggest \
  --ingredients "egg,tomato,rice" \
  --servings 1 \
  --time 20 \
  --taste "light" \
  --avoid "spicy" \
  --tools "pan"

python -m agent_lab recipes list
```

Generated JSON reports are saved in `recipes/output/`.

To view generated recipes in the Web UI:

```bash
cd web
npm run extract
npm run dev
```

Then open:

```text
http://localhost:3000/zh/recipes
http://localhost:3000/en/recipes
```

## Life Skill Pack

```text
recipe-planning          Practical recipe planning from ingredients and constraints
cooking-instructions     Clear, timed, kitchen-friendly cooking steps
nutrition-awareness      Basic dietary-awareness notes without medical advice
```

## Repository Structure

```text
.
├── agents/                  # 12 progressive Agent Harness examples + full reference
├── agent_lab/               # Project-specific Agent Harness Lab CLI
├── docs/                    # English and Chinese learning content
├── papers/                  # Local paper input and report output directories
├── recipes/                 # Local structured recipe JSON reports
├── skills/                  # On-demand skills, Research Skill Pack, and Life Skill Pack
├── web/                     # Next.js learning site, paper assistant, and recipe page
├── tests/                   # Python tests
├── data_pipeline/           # Data pipeline practice module
├── my_package/              # Python package practice module
├── .github/workflows/       # CI workflows
├── requirements.txt         # Python dependencies
└── README.zh-CN.md          # Chinese documentation
```

## Learning Path

| Session | Topic | What It Demonstrates |
| --- | --- | --- |
| s01 | Agent Loop | Minimal model-tool loop |
| s02 | Tool Use | Tool registry and dispatch map |
| s03 | TodoWrite | Multi-step task planning |
| s04 | Subagent | Subtask context isolation |
| s05 | Skills | On-demand knowledge loading |
| s06 | Context Compact | Long-context compression |
| s07 | Task System | File-persisted task graph |
| s08 | Background Tasks | Slow commands in the background |
| s09 | Agent Teams | Persistent teammates and async mailboxes |
| s10 | Team Protocols | Request-response protocols |
| s11 | Autonomous Agents | Autonomous task scanning and claiming |
| s12 | Worktree Isolation | Task-bound git worktree execution |
| s_full | Full Reference | Combined reference implementation |

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

## Agent Lab CLI

```bash
python -m agent_lab --help
python -m agent_lab tasks create "Build Web Dashboard" --description "Show tasks and skills"
python -m agent_lab tasks list
python -m agent_lab tasks show 6
python -m agent_lab tasks claim 6 --owner penglei
python -m agent_lab tasks complete 6
python -m agent_lab events list
python -m agent_lab events tail --limit 10
python -m agent_lab demo seed
python -m agent_lab papers read papers/input/example.pdf
python -m agent_lab papers read-folder papers/input
python -m agent_lab papers list
python -m agent_lab recipes suggest --ingredients "egg,tomato,rice" --servings 1 --time 20
python -m agent_lab recipes list
python -m agent_lab skills list
python -m agent_lab docs list
```

Task commands persist local state in `.tasks/task_N.json`. Runtime events are appended to `.agent_lab/events.jsonl`.

## Web Pages

```bash
cd web
npm run dev
```

Common routes:

```text
http://localhost:3000/en/dashboard
http://localhost:3000/zh/dashboard
http://localhost:3000/en/papers
http://localhost:3000/zh/papers
http://localhost:3000/en/recipes
http://localhost:3000/zh/recipes
http://localhost:3000/en/timeline
http://localhost:3000/zh/timeline
```

`npm run dev` automatically runs `npm run extract`, which extracts Markdown course content, local dashboard data, paper notes, and recipe JSON reports into `web/src/data/generated/`.

## Tests

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

## Future Improvements

- Add LLM-assisted paper summarization, citation extraction, and multi-paper comparison.
- Add `papers plan` to create a task chain for paper reading workflows.
- Add section-level cache and context compression for long papers.
- Add local paper library search and retrieval.
- Add screenshots, demo GIFs, and a public deployment link.

## Project Origin

This project is based on learning materials and example code from [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code). The goal is to turn Claude Code-style Agent Harness mechanisms into a runnable, testable, and visual personal learning project.

The original repository is kept as a local `upstream`; this repository is maintained as a personal learning and extension version.

## License

MIT License.
