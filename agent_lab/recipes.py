"""Smart recipe assistant with structured JSON output."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .events import append_event
from .paths import EVENTS_PATH, RECIPES_OUTPUT_DIR


@dataclass(frozen=True)
class RecipeStep:
    order: int
    title: str
    description: str
    time_minutes: int


@dataclass(frozen=True)
class RecipeSubstitution:
    original: str
    alternative: str


@dataclass(frozen=True)
class RecipeReport:
    title: str
    summary: str
    servings: int
    time_minutes: int
    difficulty: str
    taste: str
    avoid: list[str]
    tools: list[str]
    ingredients_used: list[str]
    missing_ingredients: list[str]
    steps: list[RecipeStep]
    shopping_list: list[str]
    substitutions: list[RecipeSubstitution]
    notes: list[str]
    path: Path | None = None


def parse_list(value: str | list[str] | None) -> list[str]:
    """Parse comma/Chinese-comma separated user input into normalized items."""
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[,，、\n]+", value)
    return [item.strip().lower() for item in items if item.strip()]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.lower()).strip("-")
    return slug[:80] or "recipe"


def _has_any(ingredients: list[str], keywords: set[str]) -> bool:
    return any(any(keyword in item for keyword in keywords) for item in ingredients)


def _pick_recipe_title(ingredients: list[str]) -> str:
    has_egg = _has_any(ingredients, {"egg", "鸡蛋", "蛋"})
    has_tomato = _has_any(ingredients, {"tomato", "番茄", "西红柿"})
    has_rice = _has_any(ingredients, {"rice", "米饭", "米"})
    has_noodle = _has_any(ingredients, {"noodle", "面", "面条"})
    has_chicken = _has_any(ingredients, {"chicken", "鸡肉", "鸡胸"})

    if has_egg and has_tomato and has_rice:
        return "Tomato Egg Rice Bowl"
    if has_egg and has_tomato and has_noodle:
        return "Tomato Egg Noodles"
    if has_chicken and has_rice:
        return "Simple Chicken Rice Bowl"
    if has_egg:
        return "Quick Egg Skillet"
    if has_rice:
        return "Simple Rice Bowl"
    return "Flexible Pantry Meal"


def _basic_missing_ingredients(ingredients: list[str], avoid: list[str]) -> list[str]:
    missing = ["salt", "cooking oil"]
    if not _has_any(ingredients, {"garlic", "蒜"}):
        missing.append("garlic")
    if not _has_any(ingredients, {"soy sauce", "生抽", "酱油"}) and "soy sauce" not in avoid:
        missing.append("soy sauce")
    if not _has_any(ingredients, {"scallion", "葱"}):
        missing.append("scallion")
    return missing


def _build_steps(title: str, time_minutes: int, tools: list[str]) -> list[RecipeStep]:
    prep_time = max(3, min(8, time_minutes // 4))
    cook_time = max(6, min(15, time_minutes // 2))
    finish_time = max(2, time_minutes - prep_time - cook_time)
    primary_tool = tools[0] if tools else "pan"

    return [
        RecipeStep(
            order=1,
            title="Prepare ingredients",
            description="Wash, cut, and portion the available ingredients before heating the pan.",
            time_minutes=prep_time,
        ),
        RecipeStep(
            order=2,
            title=f"Cook with {primary_tool}",
            description=f"Use the {primary_tool} to cook the main ingredients until fragrant and fully heated.",
            time_minutes=cook_time,
        ),
        RecipeStep(
            order=3,
            title="Season and plate",
            description=f"Adjust seasoning, plate the dish, and check that the final flavor matches {title}.",
            time_minutes=finish_time,
        ),
    ]


def suggest_recipe(
    ingredients: str | list[str],
    *,
    servings: int = 1,
    time_minutes: int = 20,
    taste: str = "balanced",
    avoid: str | list[str] | None = None,
    tools: str | list[str] | None = None,
    output_dir: Path = RECIPES_OUTPUT_DIR,
    events_path: Path = EVENTS_PATH,
) -> RecipeReport:
    """Generate one structured recipe report and persist it as JSON."""
    ingredient_items = parse_list(ingredients)
    if not ingredient_items:
        raise ValueError("At least one ingredient is required.")

    avoid_items = parse_list(avoid)
    tool_items = parse_list(tools) or ["pan"]
    safe_servings = max(1, servings)
    safe_time = max(5, time_minutes)
    title = _pick_recipe_title(ingredient_items)
    missing = _basic_missing_ingredients(ingredient_items, avoid_items)
    shopping_list = [item for item in missing if item not in {"salt", "cooking oil"}]

    report = RecipeReport(
        title=title,
        summary=(
            f"A {safe_time}-minute {taste or 'balanced'} meal for {safe_servings} "
            f"serving(s), based on {', '.join(ingredient_items[:5])}."
        ),
        servings=safe_servings,
        time_minutes=safe_time,
        difficulty="easy" if safe_time <= 25 else "medium",
        taste=taste or "balanced",
        avoid=avoid_items,
        tools=tool_items,
        ingredients_used=ingredient_items,
        missing_ingredients=missing,
        steps=_build_steps(title, safe_time, tool_items),
        shopping_list=shopping_list,
        substitutions=[
            RecipeSubstitution("scallion", "cilantro or skip it"),
            RecipeSubstitution("soy sauce", "salt plus a small pinch of sugar"),
        ],
        notes=[
            "This is a planning suggestion, not medical or dietary advice.",
            "Adjust seasoning gradually, especially when cooking for dietary restrictions.",
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{_slug(title)}.json"
    report_with_path = replace(report, path=output_path)
    output_path.write_text(
        json.dumps(_to_json_dict(report_with_path), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    append_event(
        "recipe_requested",
        {
            "title": title,
            "ingredients": ingredient_items,
            "servings": safe_servings,
            "time_minutes": safe_time,
        },
        events_path=events_path,
    )
    append_event(
        "recipe_generated",
        {
            "title": title,
            "recipe_path": str(output_path),
            "servings": safe_servings,
            "time_minutes": safe_time,
        },
        events_path=events_path,
    )
    if shopping_list:
        append_event(
            "shopping_list_generated",
            {
                "title": title,
                "items": shopping_list,
            },
            events_path=events_path,
        )

    return report_with_path


def _to_json_dict(report: RecipeReport) -> dict[str, object]:
    data = asdict(report)
    data["path"] = str(report.path) if report.path else ""
    return data


def list_recipe_reports(output_dir: Path = RECIPES_OUTPUT_DIR) -> list[Path]:
    """Return generated recipe JSON reports."""
    if not output_dir.exists():
        return []
    return sorted(output_dir.glob("*.json"))
