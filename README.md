# Agent Harness Lab

English | [简体中文](README.zh-CN.md)

A Python + Next.js Agent Harness lab for learning, experimenting with, and visualizing coding-agent runtime architecture. The project includes progressive agent examples, a local `agent_lab` CLI, a Web dashboard, a research paper assistant, a health record assistant, a smart recipe assistant, and a GitHub repository insight assistant that demonstrates how the same harness can expand into domain workflows.

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

- Minimal agent loop with multi-turn `tool_use -> tool_result -> continue` execution.
- Tool registration and dispatch layer for shell commands, file operations, editing, task management, and skill loading.
- Unified `HarnessRuntime` for action planning, skill selection, registered tool execution, artifact collection, and event capture.
- Persistent Todo and task systems for multi-step planning, dependency tracking, status transitions, and long-running goals.
- `agent_lab` CLI for local task, event, skill, doc, paper assistant, health assistant, recipe assistant, and repository insight workflows.
- JSONL event log for task lifecycle events, paper report generation, health summary generation, recipe option generation, and repository insight reports.
- Next.js Web Dashboard for task status, skill index, docs inventory, event timelines, and task dependencies.
- Paper reading assistant for PDF / Markdown / text upload and structured research reading reports.
- Health record assistant for safety-bounded checkup report summaries with non-diagnostic guidance.
- Research Skill Pack for reusable paper reading, method analysis, experiment analysis, and research report writing workflows.
- Smart recipe assistant for multiple structured JSON recipe options, recommendation reasons, cooking tool selection, and detailed cooking steps.
- Life Skill Pack for recipe planning, cooking instructions, and nutrition-aware notes.
- GitHub repository insight assistant for public repository metadata, README, language statistics, file tree analysis, and developer-focused Markdown reports.
- Subagent, context compaction, background task, multi-agent coordination, and worktree isolation examples.
- pytest, TypeScript checks, Next.js build, and GitHub Actions for basic quality coverage.

## Repository Structure

```text
.
├── agents/                  # 12 progressive Agent Harness examples + full reference
├── agent_lab/               # Project-specific runtime, tool registry, planner, and CLI
├── docs/                    # English and Chinese learning content
├── papers/                  # Local paper input and report output directories
├── health_records/          # Local health record input and safety-bounded report output directories
├── recipes/                 # Local structured recipe JSON reports
├── github_reports/          # Local GitHub repository insight reports
├── skills/                  # On-demand skills, Research Skill Pack, and Life Skill Pack
├── web/                     # Next.js learning site, paper assistant, and recipe page
├── tests/                   # Python tests
├── data_pipeline/           # Data pipeline practice module
├── my_package/              # Python package practice module
├── .github/workflows/       # CI workflows
├── requirements.txt         # Python dependencies
└── README.zh-CN.md          # Chinese documentation
```

## Harness Runtime

The project now routes domain workflows through a small shared runtime instead of calling feature modules directly:

```text
CLI / Web API
  -> HarnessRuntime
  -> Planner
  -> Skill selection
  -> Tool registry
  -> Paper / Health / Recipe / Repository tool
  -> Artifact writer
  -> JSONL event log
```

This keeps the paper assistant, health assistant, recipe assistant, and repository insight assistant under the same harness contract. Each action has a plan, a related skill set, a registered local tool, generated artifacts, and captured runtime events.

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
http://localhost:3000/zh/demo
http://localhost:3000/zh/papers
http://localhost:3000/zh/health
http://localhost:3000/zh/recipes
http://localhost:3000/zh/repos
```

Demo screenshots can be saved as:

```text
web/public/demo/dashboard.png
web/public/demo/papers.png
web/public/demo/recipes.png
```

Useful local commands:

```bash
cd /path/to/agent-harness-lab
python -m agent_lab demo seed
python -m agent_lab papers read papers/input/example.pdf
python -m agent_lab health analyze health_records/input/checkup.txt
python -m agent_lab recipes suggest-options --ingredients "egg,tomato,rice" --servings 1 --time 20
python -m agent_lab repos summarize https://github.com/browser-use/browser-use
python -m agent_lab tasks list
python -m agent_lab events list
```

Local runtime data such as `.tasks/`, `.agent_lab/`, `papers/input/`, `papers/output/`, `health_records/input/`, `health_records/output/`, `recipes/output/`, and `github_reports/output/` is ignored by Git.

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

## Health Record Assistant

The health record assistant is a safety-bounded health information extension. It reads local checkup reports or health record files, extracts common indicators, and writes a structured Markdown summary for learning and doctor-communication preparation.

Safety boundary:

```text
This assistant organizes health information only.
It does not diagnose disease, prescribe medication, or replace a licensed clinician.
```

CLI usage:

```bash
mkdir -p health_records/input health_records/output
python -m agent_lab health analyze health_records/input/checkup.txt
python -m agent_lab health list
```

Web usage:

```text
http://localhost:3000/zh/health
http://localhost:3000/en/health
```

Generated reports include extracted indicators, general interpretation notes, a doctor communication checklist, non-diagnostic lifestyle information, and a clear safety notice.

## Smart Recipe Assistant

The recipe assistant is a life knowledge extension. Unlike paper reports, recipe output is stored as structured JSON so the Web UI can later render it as cards, ingredient tags, step timelines, shopping lists, and substitution panels. Users provide ingredients and constraints; the assistant recommends multiple candidate recipes and suitable cooking tools automatically.

The Web page can generate recipes directly from browser input:

```text
http://localhost:3000/zh/recipes
```

The browser calls a local Next.js API route, and the API route invokes `agent_lab recipes suggest-options` to generate multiple JSON recipe options.

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

## GitHub Repository Insight Assistant

The repository insight assistant is a developer tool extension. It accepts a public GitHub repository URL, fetches repository metadata, README content, language statistics, and file tree information through the GitHub REST API, then writes a structured Markdown technical report.

CLI usage:

```bash
python -m agent_lab repos summarize https://github.com/browser-use/browser-use
python -m agent_lab repos summarize https://github.com/browser-use/browser-use --refresh
python -m agent_lab repos list
```

By default, `repos summarize` reuses an existing local report in `github_reports/output/`.
Use `--refresh` to fetch the repository again and overwrite the cached report.

For more stable GitHub REST API usage, set an optional token in `.env`:

```env
GITHUB_TOKEN=
```

Web usage:

```text
http://localhost:3000/zh/repos
http://localhost:3000/en/repos
```

The Web page can generate a report, show progress, refresh the local cache, copy the Markdown,
download the Markdown file, and expand historical reports.

Generated reports are saved in:

```text
github_reports/output/
```

Generated reports include:

```text
One-sentence summary
Project goals and use cases
Repository metadata
Technology stack signals
Important folders and files
Core module analysis
Setup and run hints from README
Engineering quality observations
Potential risks or missing information
Engineering improvement suggestions
```

This assistant intentionally focuses on technical repository understanding and engineering analysis.

## Life Skill Pack

```text
recipe-planning          Practical recipe planning from ingredients and constraints
cooking-instructions     Clear, timed, kitchen-friendly cooking steps
nutrition-awareness      Basic dietary-awareness notes without medical advice
```

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
python -m agent_lab recipes suggest-options --ingredients "egg,tomato,rice" --servings 1 --time 20
python -m agent_lab recipes suggest --ingredients "egg,tomato,rice"
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
http://localhost:3000/en/demo
http://localhost:3000/zh/demo
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
