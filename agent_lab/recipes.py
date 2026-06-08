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
    recommendation_reason: str = ""
    path: Path | None = None


@dataclass(frozen=True)
class RecipeCandidate:
    title: str
    reason: str
    tools: list[str]


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


def _recipe_candidates(ingredients: list[str], *, zh: bool) -> list[RecipeCandidate]:
    has_egg = _has_any(ingredients, {"egg", "鸡蛋", "蛋"})
    has_tomato = _has_any(ingredients, {"tomato", "番茄", "西红柿"})
    has_rice = _has_any(ingredients, {"rice", "米饭", "米"})
    has_noodle = _has_any(ingredients, {"noodle", "面", "面条"})
    has_beef = _has_any(ingredients, {"beef", "牛肉"})
    has_potato = _has_any(ingredients, {"potato", "土豆", "马铃薯"})

    if zh:
        if has_egg and has_tomato and has_rice:
            return [
                RecipeCandidate("番茄鸡蛋盖饭", "最快，适合一人食或工作日晚餐。", ["炒锅"]),
                RecipeCandidate("番茄蛋炒饭", "更香更下饭，适合处理剩米饭。", ["炒锅"]),
                RecipeCandidate("番茄鸡蛋汤泡饭", "更清淡，适合想少油一点的时候。", ["汤锅"]),
            ]
        if has_egg and has_tomato and has_noodle:
            return [
                RecipeCandidate("番茄鸡蛋面", "成菜快，主食和配菜一次解决。", ["汤锅"]),
                RecipeCandidate("番茄鸡蛋拌面", "汤汁更浓，适合重口味。", ["炒锅"]),
                RecipeCandidate("番茄蛋花汤面", "更清淡，适合晚餐。", ["汤锅"]),
            ]
        if has_beef and has_potato:
            return [
                RecipeCandidate("土豆牛肉小炒", "下饭、成菜快，适合现有食材直接开火。", ["炒锅"]),
                RecipeCandidate("土豆牛肉焖饭", "主食和菜合一，适合想少洗锅的时候。", ["电饭煲"]),
                RecipeCandidate("土豆牛肉汤", "更清淡，适合想做热汤时选择。", ["汤锅"]),
            ]
        return [
            RecipeCandidate(_pick_recipe_title(ingredients, zh=True), "用现有食材最快成菜，适合日常晚餐。", ["炒锅"]),
            RecipeCandidate("清爽食材汤", "少油、口味更轻，适合晚上吃。", ["汤锅"]),
            RecipeCandidate("简易拌饭碗", "适合搭配米饭，把食材集中成一份主食碗。", ["炒锅"]),
        ]

    if has_egg and has_tomato and has_rice:
        return [
            RecipeCandidate("Tomato Egg Rice Bowl", "Fastest option for a simple one-bowl meal.", ["pan"]),
            RecipeCandidate("Tomato Egg Fried Rice", "More savory and better for leftover rice.", ["pan"]),
            RecipeCandidate("Tomato Egg Soup Rice", "Lighter option with a softer texture.", ["pot"]),
        ]
    if has_egg and has_tomato and has_noodle:
        return [
            RecipeCandidate("Tomato Egg Noodles", "Fast staple meal with minimal extra ingredients.", ["pot"]),
            RecipeCandidate("Tomato Egg Tossed Noodles", "Richer sauce and stronger flavor.", ["pan"]),
            RecipeCandidate("Tomato Egg Noodle Soup", "Lighter dinner option.", ["pot"]),
        ]
    if has_beef and has_potato:
        return [
            RecipeCandidate("Potato Beef Stir-Fry", "Fast and hearty with the ingredients already available.", ["pan"]),
            RecipeCandidate("Potato Beef Rice Cooker Bowl", "One-pot option with less cleanup.", ["rice cooker"]),
            RecipeCandidate("Potato Beef Soup", "Lighter and warmer option.", ["pot"]),
        ]
    return [
        RecipeCandidate(_pick_recipe_title(ingredients, zh=False), "Fastest practical option using the available ingredients.", ["pan"]),
        RecipeCandidate("Light Pantry Soup", "Lighter option with less oil.", ["pot"]),
        RecipeCandidate("Simple Pantry Rice Bowl", "Best if you want a filling one-bowl meal.", ["pan"]),
    ]


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


def _step_times(total_minutes: int, weights: list[int]) -> list[int]:
    total = max(len(weights), total_minutes)
    weight_sum = sum(weights)
    times = [max(1, round(total * weight / weight_sum)) for weight in weights]
    delta = total - sum(times)
    index = len(times) - 1
    while delta != 0:
        if delta > 0:
            times[index] += 1
            delta -= 1
        elif times[index] > 1:
            times[index] -= 1
            delta += 1
        index = (index - 1) % len(times)
    return times


def _make_steps(specs: list[tuple[str, str, int]], total_minutes: int) -> list[RecipeStep]:
    times = _step_times(total_minutes, [spec[2] for spec in specs])
    return [
        RecipeStep(
            order=index + 1,
            title=title,
            description=description,
            time_minutes=times[index],
        )
        for index, (title, description, _) in enumerate(specs)
    ]


def _build_steps(title: str, time_minutes: int, tools: list[str], *, zh: bool) -> list[RecipeStep]:
    primary_tool = tools[0] if tools else ("炒锅" if zh else "pan")

    if zh:
        zh_specs: dict[str, list[tuple[str, str, int]]] = {
            "番茄鸡蛋盖饭": [
                ("处理食材", "番茄切块，鸡蛋打散，米饭提前盛好；如果有葱花，可以留到最后点缀。", 4),
                ("先炒鸡蛋", f"热{primary_tool}加少量油，倒入蛋液，炒到刚凝固就盛出，保留嫩度。", 4),
                ("炒番茄出汁", "锅中补一点油，加入番茄和少量盐，中火翻炒到番茄变软并出汁。", 5),
                ("回锅调味", "倒回鸡蛋，加少量生抽或盐调味，快速翻匀，让鸡蛋裹上番茄汁。", 4),
                ("盖饭装盘", "把番茄鸡蛋浇在米饭上，撒葱花或香菜，趁热食用。", 3),
            ],
            "番茄蛋炒饭": [
                ("处理食材", "番茄切小丁，鸡蛋打散，米饭提前打散，避免下锅后结块。", 4),
                ("炒鸡蛋", f"热{primary_tool}加油，倒入蛋液炒散，鸡蛋刚定型后盛出备用。", 4),
                ("炒番茄", "用锅中余油炒番茄丁，加入少量盐，炒到番茄出汁但仍保留颗粒感。", 5),
                ("下米饭", "加入米饭压散翻炒，让米饭均匀吸收番茄汁。", 5),
                ("回蛋调味", "倒回鸡蛋，加入生抽或盐调味，翻炒到米饭粒粒分明后出锅。", 4),
            ],
            "番茄鸡蛋汤泡饭": [
                ("处理食材", "番茄切块，鸡蛋打散，米饭盛入碗中备用。", 3),
                ("炒番茄底味", f"热{primary_tool}加少量油，炒番茄到变软出汁，这一步决定汤底酸甜味。", 5),
                ("煮汤打蛋花", "加入热水煮开，转小火淋入蛋液，形成蛋花后用盐调味。", 6),
                ("浇入米饭", "把番茄蛋花汤浇到米饭上，撒葱花，按口味加一点香油。", 3),
            ],
            "番茄鸡蛋面": [
                ("处理食材", "番茄切块，鸡蛋打散，面条提前准备好。", 3),
                ("炒番茄鸡蛋浇头", f"用{primary_tool}先炒鸡蛋盛出，再炒番茄出汁，最后倒回鸡蛋调味。", 7),
                ("煮面", "另加水煮面，煮到面条刚熟后捞出，保留少量面汤。", 6),
                ("组合装碗", "把番茄鸡蛋浇头盖到面上，加入少量面汤调整浓稠度。", 3),
            ],
            "番茄鸡蛋拌面": [
                ("处理食材", "番茄切丁，鸡蛋打散，面条煮前先准备一碗调味汁。", 4),
                ("炒浓番茄蛋酱", f"用{primary_tool}炒蛋盛出，再把番茄炒到浓稠，倒回鸡蛋并调味。", 8),
                ("煮面过水", "面条煮熟后捞出，想更爽口可以快速过凉水。", 5),
                ("拌匀装盘", "把番茄蛋酱倒在面上拌匀，最后撒葱花或香菜。", 3),
            ],
            "番茄蛋花汤面": [
                ("处理食材", "番茄切块，鸡蛋打散，面条准备好。", 3),
                ("煮番茄汤底", f"用{primary_tool}炒软番茄后加水煮开，让汤底有明显番茄味。", 6),
                ("下面条", "放入面条煮到刚熟，期间用筷子拨散防止粘连。", 6),
                ("淋蛋调味", "转小火淋入蛋液形成蛋花，加盐或生抽调味后出锅。", 4),
            ],
            "土豆牛肉小炒": [
                ("处理食材", "土豆切薄片或细条，牛肉逆纹切薄片，辣椒切段；土豆切好后冲掉表面淀粉。", 5),
                ("腌牛肉", "牛肉加少量生抽、油和一点淀粉抓匀，静置几分钟，让口感更嫩。", 4),
                ("快炒牛肉", f"热{primary_tool}加油，大火快炒牛肉到刚变色，马上盛出避免变老。", 4),
                ("炒土豆辣椒", "锅中补油，下土豆翻炒到边缘微透明，再加入辣椒炒出香味。", 6),
                ("回锅合炒", "倒回牛肉，加盐或生抽调味，快速翻匀后出锅。", 3),
            ],
            "土豆牛肉焖饭": [
                ("处理食材", "土豆切小块，牛肉切片或小丁，大米淘洗后沥干。", 5),
                ("炒香牛肉土豆", f"用{primary_tool}或炒锅先把牛肉炒变色，再加入土豆和生抽炒出香味。", 6),
                ("加入米和水", "把米、牛肉和土豆放入电饭煲，水量比平时煮饭略少一点。", 4),
                ("焖煮", "启动煮饭程序，焖到米饭成熟；完成后再保温几分钟。", 12),
                ("拌匀出锅", "开盖后把土豆牛肉和米饭拌匀，按口味补盐或葱花。", 3),
            ],
            "土豆牛肉汤": [
                ("处理食材", "土豆切块，牛肉切薄片或小块，辣椒按口味决定是否加入。", 5),
                ("煎炒牛肉", f"用{primary_tool}少油把牛肉炒到变色，加入土豆略炒。", 5),
                ("加水炖煮", "加入热水，煮到土豆变软，汤底变得浓一些。", 12),
                ("调味收尾", "用盐、生抽或胡椒调味，最后撒葱花或香菜。", 3),
            ],
        }
        if title in zh_specs:
            return _make_steps(zh_specs[title], time_minutes)

        return _make_steps(
            [
                ("处理食材", "清洗食材并切成适合入口的大小，肉类尽量切薄，方便在短时间内成熟。", 4),
                ("建立底味", f"先热{primary_tool}并加入少量油，放入更耐熟的食材翻炒出香味。", 5),
                ("合并主料", "加入剩余食材，按不易熟到易熟的顺序翻炒或焖煮到断生。", 6),
                ("调味装盘", f"根据口味逐步调味，收汁或翻匀后装盘，确保成品符合「{title}」的风味。", 3),
            ],
            time_minutes,
        )

    en_specs: dict[str, list[tuple[str, str, int]]] = {
        "Tomato Egg Rice Bowl": [
            ("Prep ingredients", "Cut the tomato into chunks, beat the eggs, and portion the rice into a bowl.", 4),
            ("Scramble eggs", f"Heat the {primary_tool} with oil, cook the eggs until just set, then remove them.", 4),
            ("Cook tomato sauce", "Cook the tomato with a pinch of salt until softened and juicy.", 5),
            ("Combine and season", "Return the eggs, season with soy sauce or salt, and fold gently.", 4),
            ("Top the rice", "Spoon the tomato eggs over rice and finish with scallion if available.", 3),
        ],
        "Tomato Egg Fried Rice": [
            ("Prep ingredients", "Dice the tomato, beat the eggs, and break up the rice before cooking.", 4),
            ("Scramble eggs", f"Cook the eggs in the {primary_tool} until just set, then remove them.", 4),
            ("Cook tomato", "Cook tomato until juicy but not fully dissolved.", 5),
            ("Fry rice", "Add rice and stir-fry until evenly coated with tomato juices.", 5),
            ("Finish", "Return eggs, season, and stir-fry until the grains separate.", 4),
        ],
        "Potato Beef Stir-Fry": [
            ("Prep ingredients", "Slice potato thinly, cut beef across the grain, and cut any peppers into strips.", 5),
            ("Marinate beef", "Toss beef with soy sauce, oil, and a little starch for a few minutes.", 4),
            ("Sear beef", f"Use the hot {primary_tool} to sear beef until just browned, then remove it.", 4),
            ("Cook potato", "Stir-fry potato until the edges turn slightly translucent, then add peppers.", 6),
            ("Combine", "Return beef, season quickly, and toss everything together before serving.", 3),
        ],
    }
    if title in en_specs:
        return _make_steps(en_specs[title], time_minutes)

    return _make_steps(
        [
            ("Prepare ingredients", "Wash, cut, and portion the available ingredients before heating the pan.", 4),
            ("Build flavor", f"Heat the {primary_tool}, add oil, and cook the slower-cooking ingredients first.", 5),
            ("Cook together", "Add the remaining ingredients and cook until everything is fully heated and tender.", 6),
            ("Season and serve", f"Adjust seasoning, plate the dish, and check that the final flavor matches {title}.", 3),
        ],
        time_minutes,
    )


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
    report = _build_recipe_report(
        ingredients,
        servings=servings,
        time_minutes=time_minutes,
        taste=taste,
        avoid=avoid,
        tools=tools,
    )
    report_with_path = _persist_recipe_report(report, output_dir)

    append_event(
        "recipe_requested",
        {
            "title": report.title,
            "ingredients": report.ingredients_used,
            "servings": report.servings,
            "time_minutes": report.time_minutes,
        },
        events_path=events_path,
    )
    append_event(
        "recipe_generated",
        {
            "title": report.title,
            "recipe_path": str(report_with_path.path),
            "servings": report.servings,
            "time_minutes": report.time_minutes,
        },
        events_path=events_path,
    )
    if report.shopping_list:
        append_event(
            "shopping_list_generated",
            {
                "title": report.title,
                "items": report.shopping_list,
            },
            events_path=events_path,
        )

    return report_with_path


def suggest_recipe_options(
    ingredients: str | list[str],
    *,
    servings: int = 1,
    time_minutes: int = 20,
    taste: str = "balanced",
    avoid: str | list[str] | None = None,
    tools: str | list[str] | None = None,
    limit: int = 3,
    output_dir: Path = RECIPES_OUTPUT_DIR,
    events_path: Path = EVENTS_PATH,
) -> list[RecipeReport]:
    """Generate multiple structured recipe options and persist each as JSON."""
    ingredient_items = parse_list(ingredients)
    if not ingredient_items:
        raise ValueError("At least one ingredient is required.")

    avoid_items = parse_list(avoid)
    raw_tool_items = parse_list(tools)
    zh = _is_zh(ingredient_items, taste, avoid_items, raw_tool_items)
    candidates = _recipe_candidates(ingredient_items, zh=zh)[: max(1, limit)]
    reports = [
        _build_recipe_report(
            ingredient_items,
            servings=servings,
            time_minutes=time_minutes,
            taste=taste,
            avoid=avoid_items,
            tools=raw_tool_items,
            candidate=candidate,
        )
        for candidate in candidates
    ]
    persisted = [_persist_recipe_report(report, output_dir) for report in reports]

    append_event(
        "recipe_options_requested",
        {
            "ingredients": ingredient_items,
            "servings": persisted[0].servings,
            "time_minutes": persisted[0].time_minutes,
            "count": len(persisted),
        },
        events_path=events_path,
    )
    append_event(
        "recipe_options_generated",
        {
            "title": persisted[0].title,
            "count": len(persisted),
            "recipe_paths": [str(report.path) for report in persisted],
        },
        events_path=events_path,
    )

    return persisted


def _build_recipe_report(
    ingredients: str | list[str],
    *,
    servings: int,
    time_minutes: int,
    taste: str,
    avoid: str | list[str] | None,
    tools: str | list[str] | None,
    candidate: RecipeCandidate | None = None,
) -> RecipeReport:
    ingredient_items = parse_list(ingredients)
    if not ingredient_items:
        raise ValueError("At least one ingredient is required.")

    avoid_items = parse_list(avoid)
    raw_tool_items = parse_list(tools)
    zh = _is_zh(ingredient_items, taste, avoid_items, raw_tool_items)
    if raw_tool_items:
        tool_source = raw_tool_items
    elif candidate:
        tool_source = candidate.tools
    else:
        tool_source = []
    tool_items = _normalize_cooking_tools(tool_source, ingredient_items, zh=zh)
    safe_servings = max(1, servings)
    safe_time = max(5, time_minutes)
    title = candidate.title if candidate else _pick_recipe_title(ingredient_items, zh=zh)
    missing = _basic_missing_ingredients(ingredient_items, avoid_items, zh=zh)
    shopping_list = _shopping_list(missing, zh=zh)

    return RecipeReport(
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
        recommendation_reason=candidate.reason if candidate else "",
    )


def _persist_recipe_report(report: RecipeReport, output_dir: Path) -> RecipeReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{_slug(report.title)}.json"
    report_with_path = replace(report, path=output_path)
    output_path.write_text(
        json.dumps(_to_json_dict(report_with_path), ensure_ascii=False, indent=2),
        encoding="utf-8",
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
