"""Shared filesystem paths for the Agent Harness Lab CLI."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / ".tasks"
SKILLS_DIR = REPO_ROOT / "skills"
DOCS_DIR = REPO_ROOT / "docs"
AGENT_LAB_DIR = REPO_ROOT / ".agent_lab"
EVENTS_PATH = AGENT_LAB_DIR / "events.jsonl"
PAPERS_DIR = REPO_ROOT / "papers"
PAPERS_OUTPUT_DIR = PAPERS_DIR / "output"
RECIPES_DIR = REPO_ROOT / "recipes"
RECIPES_OUTPUT_DIR = RECIPES_DIR / "output"
