import {
  AlertTriangle,
  ChefHat,
  Clock,
  ListChecks,
  ShoppingBasket,
  Sparkles,
  Users,
  Utensils,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import type { RecipeReport } from "@/types/agent-data";

interface RecipeLabels {
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

interface RecipeCardProps {
  recipe: RecipeReport;
  labels: RecipeLabels;
}

function Tag({ children, tone = "zinc" }: { children: React.ReactNode; tone?: "zinc" | "green" | "amber" }) {
  const tones = {
    zinc: "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200",
    green:
      "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300",
    amber:
      "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300",
  } as const;

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs ${tones[tone]}`}>
      {children}
    </span>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h4>
      {children}
    </section>
  );
}

export function RecipeCard({ recipe, labels }: RecipeCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ChefHat size={20} className="text-emerald-500" />
              {recipe.title}
            </CardTitle>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500 dark:text-zinc-400">
              {recipe.summary}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
            <Tag>
              <Users size={13} className="mr-1" />
              {recipe.servings} {labels.servings}
            </Tag>
            <Tag>
              <Clock size={13} className="mr-1" />
              {recipe.time_minutes} {labels.minutes}
            </Tag>
            <Tag>
              {labels.difficulty}: {recipe.difficulty}
            </Tag>
            <Tag>
              {labels.taste}: {recipe.taste}
            </Tag>
          </div>
        </div>
      </CardHeader>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-5">
          <Section icon={<Utensils size={16} className="text-emerald-500" />} title={labels.ingredients}>
            <div className="flex flex-wrap gap-2">
              {recipe.ingredients_used.map((item) => (
                <Tag key={item} tone="green">
                  {item}
                </Tag>
              ))}
            </div>
          </Section>

          {recipe.missing_ingredients.length > 0 && (
            <Section icon={<AlertTriangle size={16} className="text-amber-500" />} title={labels.missing}>
              <div className="flex flex-wrap gap-2">
                {recipe.missing_ingredients.map((item) => (
                  <Tag key={item} tone="amber">
                    {item}
                  </Tag>
                ))}
              </div>
            </Section>
          )}

          {recipe.shopping_list.length > 0 && (
            <Section icon={<ShoppingBasket size={16} className="text-blue-500" />} title={labels.shopping}>
              <ul className="space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
                {recipe.shopping_list.map((item) => (
                  <li key={item} className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </div>

        <div className="space-y-5">
          <Section icon={<ListChecks size={16} className="text-purple-500" />} title={labels.steps}>
            <ol className="space-y-3">
              {recipe.steps.map((step) => (
                <li key={`${step.order}-${step.title}`} className="rounded-lg border border-zinc-100 p-3 dark:border-zinc-800">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium">
                      {step.order}. {step.title}
                    </p>
                    <span className="shrink-0 text-xs text-zinc-500 dark:text-zinc-400">
                      {step.time_minutes} {labels.minutes}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-zinc-500 dark:text-zinc-400">{step.description}</p>
                </li>
              ))}
            </ol>
          </Section>

          {recipe.substitutions.length > 0 && (
            <Section icon={<Sparkles size={16} className="text-rose-500" />} title={labels.substitutions}>
              <div className="grid gap-2">
                {recipe.substitutions.map((item) => (
                  <div
                    key={`${item.original}-${item.alternative}`}
                    className="rounded-lg bg-zinc-50 px-3 py-2 text-sm dark:bg-zinc-800"
                  >
                    <span className="font-medium">{item.original}</span>
                    <span className="px-2 text-zinc-400">-&gt;</span>
                    <span className="text-zinc-600 dark:text-zinc-300">{item.alternative}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      </div>

      <div className="mt-5 border-t border-zinc-100 pt-4 dark:border-zinc-800">
        <div className="grid gap-3 text-xs text-zinc-500 dark:text-zinc-400 lg:grid-cols-[1fr_auto]">
          <div>
            <span className="font-medium">{labels.notes}: </span>
            {recipe.notes.join(" ")}
          </div>
          <div>
            <span className="font-medium">{labels.path}: </span>
            {recipe.path}
          </div>
        </div>
      </div>
    </Card>
  );
}
