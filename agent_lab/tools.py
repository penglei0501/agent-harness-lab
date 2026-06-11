"""Tool registry used by the Agent Harness Lab runtime."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .papers import generate_notes_for_folder, generate_paper_note
from .recipes import suggest_recipe, suggest_recipe_options
from .repos import summarize_github_repo

ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler


class ToolRegistry:
    """Map runtime action names to callable local tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, name: str, description: str, handler: ToolHandler) -> None:
        self._tools[name] = ToolSpec(name=name, description=description, handler=handler)

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown harness action: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._tools)


def _read_paper_tool(**kwargs: Any) -> Any:
    return generate_paper_note(
        Path(kwargs["paper_path"]),
        output_dir=Path(kwargs["output_dir"]),
        events_path=Path(kwargs["events_path"]),
    )


def _read_paper_folder_tool(**kwargs: Any) -> Any:
    return generate_notes_for_folder(
        Path(kwargs["folder_path"]),
        output_dir=Path(kwargs["output_dir"]),
        events_path=Path(kwargs["events_path"]),
    )


def _suggest_recipe_tool(**kwargs: Any) -> Any:
    return suggest_recipe(
        kwargs["ingredients"],
        servings=int(kwargs.get("servings", 1)),
        time_minutes=int(kwargs.get("time_minutes", 20)),
        taste=str(kwargs.get("taste", "balanced")),
        avoid=kwargs.get("avoid"),
        tools=kwargs.get("tools"),
        output_dir=Path(kwargs["output_dir"]),
        events_path=Path(kwargs["events_path"]),
    )


def _suggest_recipe_options_tool(**kwargs: Any) -> Any:
    return suggest_recipe_options(
        kwargs["ingredients"],
        servings=int(kwargs.get("servings", 1)),
        time_minutes=int(kwargs.get("time_minutes", 20)),
        taste=str(kwargs.get("taste", "balanced")),
        avoid=kwargs.get("avoid"),
        tools=kwargs.get("tools"),
        limit=int(kwargs.get("limit", 3)),
        output_dir=Path(kwargs["output_dir"]),
        events_path=Path(kwargs["events_path"]),
    )


def _summarize_repo_tool(**kwargs: Any) -> Any:
    fetcher = kwargs.get("fetcher")
    args: dict[str, Any] = {
        "output_dir": Path(kwargs["output_dir"]),
        "events_path": Path(kwargs["events_path"]),
        "refresh": bool(kwargs.get("refresh", False)),
    }
    if fetcher is not None:
        args["fetcher"] = fetcher
    return summarize_github_repo(kwargs["github_url"], **args)


def default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        "papers.read",
        "Read one paper file and write a structured Markdown research note.",
        _read_paper_tool,
    )
    registry.register(
        "papers.read_folder",
        "Read supported paper files in a folder and write Markdown research notes.",
        _read_paper_folder_tool,
    )
    registry.register(
        "recipes.suggest",
        "Generate one structured recipe report from ingredients and constraints.",
        _suggest_recipe_tool,
    )
    registry.register(
        "recipes.suggest_options",
        "Generate multiple structured recipe options from ingredients and constraints.",
        _suggest_recipe_options_tool,
    )
    registry.register(
        "repos.summarize",
        "Generate a structured developer-focused report from a public GitHub repository URL.",
        _summarize_repo_tool,
    )
    return registry
