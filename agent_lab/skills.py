"""Discover local SKILL.md files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .paths import SKILLS_DIR


@dataclass(frozen=True)
class SkillItem:
    name: str
    description: str
    path: Path


def _extract_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}

    end = text.find("\n---", 3)
    if end == -1:
        return {}

    metadata: dict[str, str] = {}
    lines = text[3:end].strip().splitlines()
    current_key: str | None = None
    current_lines: list[str] = []

    for line in lines:
        if line.startswith(" ") and current_key:
            current_lines.append(line.strip())
            continue

        if current_key:
            metadata[current_key] = " ".join(current_lines).strip()
            current_key = None
            current_lines = []

        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value == "|":
            current_key = key.strip()
            current_lines = []
        else:
            metadata[key.strip()] = value

    if current_key:
        metadata[current_key] = " ".join(current_lines).strip()

    return metadata


def load_skills(skills_dir: Path = SKILLS_DIR) -> list[SkillItem]:
    """Return available skills sorted by name."""
    if not skills_dir.exists():
        return []

    skills: list[SkillItem] = []
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        metadata = _extract_frontmatter(text)
        name = metadata.get("name") or path.parent.name
        description = metadata.get("description") or "(no description)"
        skills.append(SkillItem(name=name, description=description, path=path))

    return sorted(skills, key=lambda item: item.name)
