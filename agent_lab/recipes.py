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


def _contains_cjk(items: list[str]) -> bool:
    return any(re.search(r"[\u4e00-\u9fff]", item) for item in items)


def _is_zh(ingredients: list[str], taste: str, avoid: list[str], tools: list[str]) -> bool:
    return _contains_cjk([*ingredients, taste, *avoid, *tools])


def _recommend_cooking_tools(ingredients: list[str], *, zh: bool) -> list[str]:
    has_noodle = _has_any(ingredients, {"noodle", "面", "面条"})
    has_potato = _has_any(ingredients, {"potato", "土豆", "马铃薯"})
    has_beef = _has_any(ingredients, {"beef", "牛肉"})
    has_raw_rice = _has_any(ingredients, {"raw rice", "uncooked rice", "生米", "大米"})

    if zh:
        if has_raw_rice:
            return ["电饭煲"]
        if has_noodle:
            return ["汤锅"]
        if has_potato and has_beef:
            return ["炒锅"]
        return ["炒锅"]

    if has_raw_rice:
        return ["rice cooker"]
    if has_noodle:
        return ["pot"]
    return ["pan"]


def _normalize_cooking_tools(tools: list[str], ingredients: list[str], *, zh: bool) -> list[str]:
    cooking_keywords = {
        "pan",
        "skillet",
        "pot",
        "wok",
        "oven",
        "air fryer",
        "microwave",
        "rice cooker",
        "锅",
        "炒锅",
        "平底锅",
        "煎锅",
        "汤锅",
        "蒸锅",
        "砂锅",
        "烤箱",
        "空气炸锅",
        "微波炉",
        "电饭煲",
    }
    serving_keywords = {"plate", "bowl", "dish", "盘", "盘子", "碗", "碟"}

    cooking_tools: list[str] = []
    for tool in tools:
        if any(keyword in tool for keyword in serving_keywords):
            continue
        if any(keyword in tool for keyword in cooking_keywords):
            cooking_tools.append(tool)

    if cooking_tools:
        return cooking_tools
    return _recommend_cooking_tools(ingredients, zh=zh)


def _avoid_has(avoid: list[str], keywords: set[str]) -> bool:
    return any(any(keyword in item for keyword in keywords) for item in avoid)


def _pick_recipe_title(ingredients: list[str], *, zh: bool) -> str:
    has_egg = _has_any(ingredients, {"egg", "鸡蛋", "蛋"})
    has_tomato = _has_any(ingredients, {"tomato", "番茄", "西红柿"})
    has_rice = _has_any(ingredients, {"rice", "米饭", "米"})
    has_noodle = _has_any(ingredients, {"noodle", "面", "面条"})
    has_chicken = _has_any(ingredients, {"chicken", "鸡肉", "鸡胸"})
    has_beef = _has_any(ingredients, {"beef", "牛肉"})
    has_potato = _has_any(ingredients, {"potato", "土豆", "马铃薯"})

    if zh:
        if has_beef and has_potato:
            return "土豆牛肉小炒"
        if has_egg and has_tomato and has_rice:
            return "番茄鸡蛋盖饭"
        if has_egg and has_tomato and has_noodle:
            return "番茄鸡蛋面"
        if has_chicken and has_rice:
            return "鸡肉盖饭"
        if has_egg:
            return "快手鸡蛋小炒"
        if has_rice:
            return "家常米饭碗"
        return "家常食材小炒"
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


def _basic_missing_ingredients(ingredients: list[str], avoid: list[str], *, zh: bool) -> list[str]:
    if zh:
        missing = ["盐", "食用油"]
        if not _has_any(ingredients, {"garlic", "蒜", "大蒜"}):
            missing.append("蒜")
        if not _has_any(ingredients, {"soy sauce", "生抽", "酱油"}) and not _avoid_has(
            avoid, {"soy sauce", "生抽", "酱油"}
        ):
            missing.append("生抽")
        if not _has_any(ingredients, {"scallion", "葱", "葱花"}):
            missing.append("葱花")
        return missing

    missing = ["salt", "cooking oil"]
    if not _has_any(ingredients, {"garlic", "蒜", "大蒜"}):
        missing.append("garlic")
    if not _has_any(ingredients, {"soy sauce", "生抽", "酱油"}) and not _avoid_has(
        avoid, {"soy sauce", "生抽", "酱油"}
    ):
        missing.append("soy sauce")
    if not _has_any(ingredients, {"scallion", "葱", "葱花"}):
        missing.append("scallion")
    return missing


def _build_steps(title: str, time_minutes: int, tools: list[str], *, zh: bool) -> list[RecipeStep]:
    prep_time = max(3, min(8, time_minutes // 4))
    cook_time = max(6, min(15, time_minutes // 2))
    finish_time = max(2, time_minutes - prep_time - cook_time)
    primary_tool = tools[0] if tools else ("炒锅" if zh else "pan")

    if zh:
        return [
            RecipeStep(
                order=1,
                title="处理食材",
                description="清洗食材并切成适合入口的大小，肉类尽量切薄，方便在短时间内成熟。",
                time_minutes=prep_time,
            ),
            RecipeStep(
                order=2,
                title=f"用{primary_tool}烹饪",
                description=f"先热{primary_tool}并加入少量油，再按不易熟到易熟的顺序下锅翻炒，直到食材断生并出香味。",
                time_minutes=cook_time,
            ),
            RecipeStep(
                order=3,
                title="调味装盘",
                description=f"根据口味逐步调味，收汁或翻匀后装盘，确保成品符合「{title}」的风味。",
                time_minutes=finish_time,
            ),
        ]

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


def _build_summary(
    ingredients: list[str],
    *,
    servings: int,
    time_minutes: int,
    taste: str,
    zh: bool,
) -> str:
    if zh:
        return (
            f"这是一道约 {time_minutes} 分钟完成、适合 {servings} 人份的"
            f"{taste or '家常'}菜谱，主要基于{', '.join(ingredients[:5])}。"
        )
    return (
        f"A {time_minutes}-minute {taste or 'balanced'} meal for {servings} "
        f"serving(s), based on {', '.join(ingredients[:5])}."
    )


def _shopping_list(missing: list[str], *, zh: bool) -> list[str]:
    pantry_basics = {"盐", "食用油"} if zh else {"salt", "cooking oil"}
    return [item for item in missing if item not in pantry_basics]


def _substitutions(*, zh: bool) -> list[RecipeSubstitution]:
    if zh:
        return [
            RecipeSubstitution("葱花", "香菜、青蒜，或者直接省略"),
            RecipeSubstitution("生抽", "少量盐加一点点糖"),
        ]
    return [
        RecipeSubstitution("scallion", "cilantro or skip it"),
        RecipeSubstitution("soy sauce", "salt plus a small pinch of sugar"),
    ]


def _notes(*, zh: bool) -> list[str]:
    if zh:
        return [
            "这是基于食材和约束生成的烹饪建议，不构成医疗或营养处方。",
            "有忌口或健康限制时，请根据自身情况调整调味和食材。",
        ]
    return [
        "This is a planning suggestion, not medical or dietary advice.",
        "Adjust seasoning gradually, especially when cooking for dietary restrictions.",
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
    raw_tool_items = parse_list(tools)
    zh = _is_zh(ingredient_items, taste, avoid_items, raw_tool_items)
    tool_items = _normalize_cooking_tools(raw_tool_items, ingredient_items, zh=zh)
    safe_servings = max(1, servings)
    safe_time = max(5, time_minutes)
    title = _pick_recipe_title(ingredient_items, zh=zh)
    missing = _basic_missing_ingredients(ingredient_items, avoid_items, zh=zh)
    shopping_list = _shopping_list(missing, zh=zh)

    report = RecipeReport(
        title=title,
        summary=_build_summary(
            ingredient_items,
            servings=safe_servings,
            time_minutes=safe_time,
            taste=taste,
            zh=zh,
        ),
        servings=safe_servings,
        time_minutes=safe_time,
        difficulty=("简单" if zh else "easy") if safe_time <= 25 else ("中等" if zh else "medium"),
        taste=taste or ("家常" if zh else "balanced"),
        avoid=avoid_items,
        tools=tool_items,
        ingredients_used=ingredient_items,
        missing_ingredients=missing,
        steps=_build_steps(title, safe_time, tool_items, zh=zh),
        shopping_list=shopping_list,
        substitutions=_substitutions(zh=zh),
        notes=_notes(zh=zh),
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
