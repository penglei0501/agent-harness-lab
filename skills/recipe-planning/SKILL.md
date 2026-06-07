---
name: recipe-planning
description: Plan practical recipes from available ingredients, servings, time limits, taste preferences, and avoid lists.
---

# Recipe Planning Skill

Use this skill when turning a user's available ingredients and constraints into a practical recipe plan.

## Workflow

1. Parse available ingredients, servings, time limit, taste preference, avoid list, and kitchen tools.
2. Prefer recipes that use ingredients the user already has.
3. Keep missing ingredients small and mark them clearly.
4. Choose a difficulty level that fits the time limit and tools.
5. Include substitutions when an ingredient is optional or commonly replaceable.
6. Keep the output structured so a UI can render recipe cards, tags, steps, and shopping lists.
7. Avoid medical claims; treat nutrition notes as general information only.

## Output Shape

Prefer structured JSON-compatible fields:

- title
- summary
- servings
- timeMinutes
- difficulty
- ingredientsUsed
- missingIngredients
- steps
- shoppingList
- substitutions
- notes
