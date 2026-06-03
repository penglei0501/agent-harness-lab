import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { getTranslations } from "@/lib/i18n-server";
import type { DashboardData, DashboardTask } from "@/types/agent-data";
import dashboardJson from "@/data/generated/dashboard.json";

const data = dashboardJson as DashboardData;

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  in_progress: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  completed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
};

function statusClass(status: string) {
  return STATUS_STYLES[status] ?? "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-normal">{value}</p>
    </Card>
  );
}

function TaskRow({ task, t }: { task: DashboardTask; t: (key: string) => string }) {
  return (
    <div className="border-b border-zinc-100 py-3 last:border-b-0 dark:border-zinc-800">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs text-zinc-500">#{task.id}</span>
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${statusClass(task.status)}`}>
          {task.status}
        </span>
        <span className="text-sm font-medium">{task.subject}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-zinc-500 dark:text-zinc-400">
        <span>{t("owner")}: {task.owner || "-"}</span>
        <span>{t("blocked_by")}: {task.blockedBy.length ? task.blockedBy.join(", ") : "-"}</span>
      </div>
    </div>
  );
}

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslations(locale, "dashboard");
  const recentTasks = data.tasks.items.slice(-6).reverse();
  const localeLabels = Object.entries(data.docs.byLocale)
    .map(([key, value]) => `${key}: ${value}`)
    .join(" / ");

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">{t("subtitle")}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label={t("tasks")} value={data.tasks.total} />
        <StatCard label={t("pending")} value={data.tasks.pending} />
        <StatCard label={t("completed")} value={data.tasks.completed} />
        <StatCard label={t("events")} value={data.events.total} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("recent_tasks")}</CardTitle>
          </CardHeader>
          {recentTasks.length ? (
            <div>
              {recentTasks.map((task) => (
                <TaskRow key={task.id} task={task} t={t} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">(none)</p>
          )}
        </Card>

        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{t("skill_index")}</CardTitle>
            </CardHeader>
            <div className="space-y-3">
              {data.skills.items.map((skill) => (
                <div key={skill.path}>
                  <p className="text-sm font-medium">{skill.name}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
                    {skill.description}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("doc_coverage")}</CardTitle>
            </CardHeader>
            <p className="text-3xl font-semibold">{data.docs.total}</p>
            <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">{localeLabels}</p>
          </Card>
        </div>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{t("recent_events")}</CardTitle>
        </CardHeader>
        {data.events.recent.length ? (
          <div className="space-y-3">
            {data.events.recent.map((event, index) => (
              <div
                key={`${event.timestamp}-${event.type}-${index}`}
                className="grid gap-1 border-b border-zinc-100 pb-3 text-sm last:border-b-0 last:pb-0 dark:border-zinc-800 md:grid-cols-[180px_150px_1fr]"
              >
                <span className="font-mono text-xs text-zinc-500">{event.timestamp || "-"}</span>
                <span className="font-medium">{event.type}</span>
                <span className="text-zinc-600 dark:text-zinc-300">
                  #{event.taskId} {event.subject}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("empty_events")}</p>
        )}
      </Card>
    </div>
  );
}
