import Link from "next/link";
import * as fs from "fs";
import * as path from "path";
import {
  BookOpen,
  ChefHat,
  FileText,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  Sparkles,
  Terminal,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { getTranslations } from "@/lib/i18n-server";

const WEB_ROOT = process.cwd();
const DEMO_IMAGE_DIR = path.join(WEB_ROOT, "public", "demo");

function demoImageExists(filename: string) {
  return fs.existsSync(path.join(DEMO_IMAGE_DIR, filename));
}

function CommandBlock({ command }: { command: string }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 text-xs leading-6 text-zinc-100">
      <code>{command}</code>
    </pre>
  );
}

function StepNumber({ value }: { value: number }) {
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white dark:bg-white dark:text-zinc-900">
      {value}
    </span>
  );
}

export default async function DemoPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslations(locale, "demo");

  const modules = [
    {
      icon: <LayoutDashboard size={20} className="text-blue-500" />,
      title: t("dashboard_title"),
      description: t("dashboard_desc"),
      href: `/${locale}/dashboard`,
    },
    {
      icon: <FileText size={20} className="text-emerald-500" />,
      title: t("papers_title"),
      description: t("papers_desc"),
      href: `/${locale}/papers`,
    },
    {
      icon: <ChefHat size={20} className="text-amber-500" />,
      title: t("recipes_title"),
      description: t("recipes_desc"),
      href: `/${locale}/recipes`,
    },
    {
      icon: <BookOpen size={20} className="text-purple-500" />,
      title: t("learning_title"),
      description: t("learning_desc"),
      href: `/${locale}/timeline`,
    },
    {
      icon: <GitBranch size={20} className="text-rose-500" />,
      title: t("layers_title"),
      description: t("layers_desc"),
      href: `/${locale}/layers`,
    },
    {
      icon: <Terminal size={20} className="text-zinc-500" />,
      title: t("cli_title"),
      description: t("cli_desc"),
      href: `/${locale}/dashboard`,
    },
  ];

  const flow = [
    {
      title: t("flow_seed_title"),
      description: t("flow_seed_desc"),
      command: "python -m agent_lab demo seed",
    },
    {
      title: t("flow_paper_title"),
      description: t("flow_paper_desc"),
      command: "python -m agent_lab papers read papers/input/example.pdf",
    },
    {
      title: t("flow_recipe_title"),
      description: t("flow_recipe_desc"),
      command: 'python -m agent_lab recipes suggest-options --ingredients "egg,tomato,rice" --servings 1 --time 20',
    },
    {
      title: t("flow_web_title"),
      description: t("flow_web_desc"),
      command: "cd web\nnpm run dev",
    },
  ];
  const screenshots = [
    {
      title: t("screenshot_dashboard_title"),
      description: t("screenshot_dashboard_desc"),
      filename: "dashboard.png",
    },
    {
      title: t("screenshot_papers_title"),
      description: t("screenshot_papers_desc"),
      filename: "papers.png",
    },
    {
      title: t("screenshot_recipes_title"),
      description: t("screenshot_recipes_desc"),
      filename: "recipes.png",
    },
  ];

  return (
    <div>
      <section className="mb-8">
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
          <Sparkles size={14} />
          {t("eyebrow")}
        </div>
        <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">{t("title")}</h1>
        <p className="mt-3 max-w-3xl text-[var(--color-text-secondary)]">{t("subtitle")}</p>
      </section>

      <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {modules.map((module) => (
          <Link key={module.title} href={module.href} className="group">
            <Card className="h-full transition-colors group-hover:border-zinc-400 dark:group-hover:border-zinc-600">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {module.icon}
                  {module.title}
                </CardTitle>
              </CardHeader>
              <p className="text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                {module.description}
              </p>
              <p className="mt-4 text-sm font-medium text-zinc-900 dark:text-zinc-100">
                {t("open")} -&gt;
              </p>
            </Card>
          </Link>
        ))}
      </section>

      <section className="mb-8">
        <div className="mb-4">
          <h2 className="text-2xl font-bold">{t("screenshots_title")}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500 dark:text-zinc-400">
            {t("screenshots_desc")}
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {screenshots.map((screenshot) => {
            const exists = demoImageExists(screenshot.filename);
            return (
              <Card key={screenshot.filename} className="overflow-hidden p-0">
                <div className="aspect-[16/10] border-b border-zinc-100 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950">
                  {exists ? (
                    <img
                      src={`/demo/${screenshot.filename}`}
                      alt={screenshot.title}
                      className="h-full w-full object-cover object-left-top"
                    />
                  ) : (
                    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
                      <FileText size={28} className="mb-3 text-zinc-400" />
                      <p className="text-sm font-medium">{t("screenshot_missing")}</p>
                      <p className="mt-1 font-mono text-xs text-zinc-500 dark:text-zinc-400">
                        web/public/demo/{screenshot.filename}
                      </p>
                    </div>
                  )}
                </div>
                <div className="p-5">
                  <h3 className="text-sm font-semibold">{screenshot.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                    {screenshot.description}
                  </p>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="mb-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks size={20} className="text-emerald-500" />
              {t("workflow_title")}
            </CardTitle>
          </CardHeader>
          <div className="space-y-5">
            {flow.map((item, index) => (
              <div key={item.title} className="flex gap-3">
                <StepNumber value={index + 1} />
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-semibold">{item.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                    {item.description}
                  </p>
                  <div className="mt-3">
                    <CommandBlock command={item.command} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("showcase_title")}</CardTitle>
          </CardHeader>
          <div className="grid gap-3">
            <div className="rounded-lg border border-zinc-100 p-4 dark:border-zinc-800">
              <p className="text-sm font-semibold">{t("showcase_dashboard_title")}</p>
              <p className="mt-1 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                {t("showcase_dashboard_desc")}
              </p>
            </div>
            <div className="rounded-lg border border-zinc-100 p-4 dark:border-zinc-800">
              <p className="text-sm font-semibold">{t("showcase_paper_title")}</p>
              <p className="mt-1 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                {t("showcase_paper_desc")}
              </p>
            </div>
            <div className="rounded-lg border border-zinc-100 p-4 dark:border-zinc-800">
              <p className="text-sm font-semibold">{t("showcase_recipe_title")}</p>
              <p className="mt-1 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                {t("showcase_recipe_desc")}
              </p>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
