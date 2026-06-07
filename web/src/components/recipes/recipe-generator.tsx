"use client";

import { FormEvent, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { RecipeCard } from "@/components/recipes/recipe-card";
import type { RecipeReport } from "@/types/agent-data";

interface RecipeGeneratorLabels {
  title: string;
  description: string;
  ingredients: string;
  servings: string;
  time: string;
  taste: string;
  avoid: string;
  tools: string;
  submit: string;
  generating: string;
  success: string;
  error: string;
  saved_to: string;
}

interface RecipeCardLabels {
  servings: string;
  minutes: string;
  difficulty: string;
  taste: string;
  ingredients: string;
  missing: string;
  steps: string;
  shopping: string;
  substitutions: string;
  notes: string;
  path: string;
}

interface RecipeGeneratorProps {
  labels: RecipeGeneratorLabels;
  cardLabels: RecipeCardLabels;
}

interface RecipeResponse {
  ok: boolean;
  recipe?: RecipeReport;
  path?: string;
  error?: string;
}

const inputClass =
  "min-h-10 rounded-md border border-zinc-200 bg-white px-3 text-sm outline-none transition-colors focus:border-emerald-500 dark:border-zinc-700 dark:bg-zinc-950";

export function RecipeGenerator({ labels, cardLabels }: RecipeGeneratorProps) {
  const [ingredients, setIngredients] = useState("egg,tomato,rice");
  const [servings, setServings] = useState(1);
  const [timeMinutes, setTimeMinutes] = useState(20);
  const [taste, setTaste] = useState("light");
  const [avoid, setAvoid] = useState("spicy");
  const [tools, setTools] = useState("pan");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<RecipeReport | null>(null);
  const [resultPath, setResultPath] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setResultPath("");

    try {
      const response = await fetch("/api/recipes/suggest/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ingredients,
          servings,
          time_minutes: timeMinutes,
          taste,
          avoid,
          tools,
        }),
      });
      const payload = (await response.json()) as RecipeResponse;
      if (!response.ok || !payload.ok || !payload.recipe) {
        throw new Error(payload.error || labels.error);
      }
      setResult({ ...payload.recipe, path: payload.path ?? payload.recipe.path });
      setResultPath(payload.path ?? payload.recipe.path);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : labels.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles size={19} className="text-emerald-500" />
            {labels.title}
          </CardTitle>
        </CardHeader>
        <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">{labels.description}</p>

        <form onSubmit={handleSubmit} className="grid gap-4">
          <label className="grid gap-2 text-sm font-medium">
            {labels.ingredients}
            <input
              className={inputClass}
              value={ingredients}
              onChange={(event) => setIngredients(event.target.value)}
              required
            />
          </label>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-medium">
              {labels.servings}
              <input
                className={inputClass}
                type="number"
                min={1}
                max={12}
                value={servings}
                onChange={(event) => setServings(Number(event.target.value))}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              {labels.time}
              <input
                className={inputClass}
                type="number"
                min={5}
                max={240}
                value={timeMinutes}
                onChange={(event) => setTimeMinutes(Number(event.target.value))}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              {labels.taste}
              <input
                className={inputClass}
                value={taste}
                onChange={(event) => setTaste(event.target.value)}
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-medium">
              {labels.avoid}
              <input
                className={inputClass}
                value={avoid}
                onChange={(event) => setAvoid(event.target.value)}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              {labels.tools}
              <input
                className={inputClass}
                value={tools}
                onChange={(event) => setTools(event.target.value)}
              />
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex min-h-10 items-center gap-2 rounded-md bg-zinc-900 px-4 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-wait disabled:opacity-70 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              {loading ? labels.generating : labels.submit}
            </button>
            {resultPath && (
              <span className="text-sm text-emerald-700 dark:text-emerald-300">
                {labels.success}: {labels.saved_to} {resultPath}
              </span>
            )}
          </div>
        </form>

        {error && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </p>
        )}
      </Card>

      {result && <RecipeCard recipe={result} labels={cardLabels} />}
    </section>
  );
}
