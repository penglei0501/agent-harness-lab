"""Small task planner for Agent Harness Lab runtime actions."""

from __future__ import annotations


ACTION_PLANS: dict[str, list[str]] = {
    "papers.read": [
        "Read paper text",
        "Extract coarse research sections",
        "Write structured Markdown note",
        "Record paper reading events",
    ],
    "papers.read_folder": [
        "Scan folder for supported paper files",
        "Generate one structured note per paper",
        "Record paper reading events",
    ],
    "health.analyze": [
        "Read health record text",
        "Extract common health indicators",
        "Write safety-bounded Markdown health summary",
        "Record health assistant events",
    ],
    "recipes.suggest": [
        "Parse available ingredients and constraints",
        "Select a practical recipe pattern",
        "Render structured recipe JSON",
        "Record recipe generation events",
    ],
    "recipes.suggest_options": [
        "Parse available ingredients and constraints",
        "Generate multiple candidate recipes",
        "Persist structured recipe JSON files",
        "Record recipe option events",
    ],
    "repos.summarize": [
        "Parse GitHub repository URL",
        "Fetch repository metadata, README, languages, and tree",
        "Infer technology stack and important paths",
        "Write structured Markdown repository report",
        "Record repository insight events",
    ],
}


def plan_for_action(action: str) -> list[str]:
    """Return the runtime plan for a known action."""
    return ACTION_PLANS.get(action, ["Run registered harness tool"])
