import { FileJson, Terminal } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { RecipeCard } from "@/components/recipes/recipe-card";
import { RecipeGenerator } from "@/components/recipes/recipe-generator";
import { getTranslations } from "@/lib/i18n-server";
import type { RecipeIndex } from "@/types/agent-data";
import recipesJson from "@/data/generated/recipes.json";

const recipes = recipesJson as RecipeIndex;

function CommandBlock({ command }: { command: string }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 text-xs leading-6 text-zinc-100">
      <code>{command}</code>
    </pre>
  );
}

export default async function RecipesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslations(locale, "recipes");
  const labels = {
    servings: t("servings"),
    minutes: t("minutes"),
    difficulty: t("difficulty"),
    taste: t("taste"),
    ingredients: t("ingredients"),
    missing: t("missing"),
    steps: t("steps"),
    shopping: t("shopping"),
    substitutions: t("substitutions"),
    notes: t("notes"),
    path: t("path"),
  };
  const generatorLabels = {
    title: t("generator_title"),
    description: t("generator_desc"),
    ingredients: t("form_ingredients"),
    servings: t("form_servings"),
    time: t("form_time"),
    taste: t("form_taste"),
    avoid: t("form_avoid"),
    submit: t("form_submit"),
    generating: t("form_generating"),
    success: t("form_success"),
    error: t("form_error"),
    saved_to: t("saved_to"),
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="mt-2 max-w-3xl text-[var(--color-text-secondary)]">{t("subtitle")}</p>
      </div>

      <div className="mb-6">
        <RecipeGenerator labels={generatorLabels} cardLabels={labels} />
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal size={18} />
              {t("create")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("create_desc")}</p>
          <CommandBlock command={'python -m agent_lab recipes suggest --ingredients "egg,tomato,rice" --servings 1 --time 20'} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileJson size={18} />
              {t("list")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("list_desc")}</p>
          <CommandBlock command="python -m agent_lab recipes list" />
        </Card>
      </div>

      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">{t("reports")}</h2>
        <span className="text-sm text-zinc-500 dark:text-zinc-400">{recipes.total}</span>
      </div>

      {recipes.items.length ? (
        <div className="space-y-5">
          {recipes.items.map((recipe) => (
            <RecipeCard key={recipe.path} recipe={recipe} labels={labels} />
          ))}
        </div>
      ) : (
        <Card>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("empty_reports")}</p>
        </Card>
      )}
    </div>
  );
}
