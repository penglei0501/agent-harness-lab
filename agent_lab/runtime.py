"""Unified runtime for Agent Harness Lab actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .events import load_events
from .paths import EVENTS_PATH, GITHUB_REPORTS_OUTPUT_DIR, PAPERS_OUTPUT_DIR, RECIPES_OUTPUT_DIR, SKILLS_DIR
from .planner import plan_for_action
from .skills import load_skills
from .tools import ToolRegistry, default_tool_registry


ACTION_SKILLS: dict[str, list[str]] = {
    "papers.read": ["paper-reading", "pdf", "research-report-writing"],
    "papers.read_folder": ["paper-reading", "pdf", "research-report-writing"],
    "recipes.suggest": ["recipe-planning", "cooking-instructions", "nutrition-awareness"],
    "recipes.suggest_options": ["recipe-planning", "cooking-instructions", "nutrition-awareness"],
    "repos.summarize": ["github-repo-insight"],
}


@dataclass(frozen=True)
class HarnessResult:
    action: str
    status: str
    plan: list[str]
    skills: list[str]
    artifacts: dict[str, Any]
    events: list[str]
    output: Any


class HarnessRuntime:
    """Coordinate planning, skill selection, tool execution, and event capture."""

    def __init__(
        self,
        *,
        skills_dir: Path = SKILLS_DIR,
        events_path: Path = EVENTS_PATH,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.skills_dir = skills_dir
        self.events_path = events_path
        self.registry = registry or default_tool_registry()

    def run(self, action: str, **kwargs: Any) -> HarnessResult:
        """Run one registered harness action and return structured execution metadata."""
        tool = self.registry.get(action)
        plan = plan_for_action(action)
        skills = self._select_skills(action)
        before_count = len(load_events(self.events_path))
        tool_kwargs = self._normalize_kwargs(action, kwargs)

        output = tool.handler(**tool_kwargs)

        new_events = load_events(self.events_path)[before_count:]
        return HarnessResult(
            action=action,
            status="completed",
            plan=plan,
            skills=skills,
            artifacts=self._artifacts_for(action, output),
            events=[event.event_type for event in new_events],
            output=output,
        )

    def _select_skills(self, action: str) -> list[str]:
        available = {skill.name for skill in load_skills(self.skills_dir)}
        desired = ACTION_SKILLS.get(action, [])
        return [name for name in desired if name in available]

    def _normalize_kwargs(self, action: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(kwargs)
        normalized.setdefault("events_path", self.events_path)
        if action.startswith("papers."):
            normalized.setdefault("output_dir", PAPERS_OUTPUT_DIR)
        elif action.startswith("recipes."):
            normalized.setdefault("output_dir", RECIPES_OUTPUT_DIR)
        elif action.startswith("repos."):
            normalized.setdefault("output_dir", GITHUB_REPORTS_OUTPUT_DIR)
        return normalized

    def _artifacts_for(self, action: str, output: Any) -> dict[str, Any]:
        if action == "papers.read":
            return {"note_path": str(output.note_path), "title": output.title}
        if action == "papers.read_folder":
            return {"note_paths": [str(note.note_path) for note in output], "count": len(output)}
        if action == "recipes.suggest":
            return {"recipe_path": str(output.path), "title": output.title}
        if action == "recipes.suggest_options":
            return {
                "recipe_paths": [str(report.path) for report in output],
                "count": len(output),
            }
        if action == "repos.summarize":
            return {"report_path": str(output.path), "repo": output.repo}
        return {}
