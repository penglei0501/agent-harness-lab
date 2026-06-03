import type { DashboardTaskDependency } from "@/types/agent-data";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  in_progress: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  completed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  missing: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
};

function statusClass(status: string) {
  return STATUS_STYLES[status] ?? "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
}

function TaskNode({
  id,
  subject,
  status,
}: {
  id: string;
  subject: string;
  status: string;
}) {
  return (
    <div className="min-w-0 rounded border border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs text-zinc-500">#{id}</span>
        <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${statusClass(status)}`}>
          {status}
        </span>
      </div>
      <p className="mt-1 truncate text-sm font-medium">{subject}</p>
    </div>
  );
}

export function TaskDependencyGraph({
  dependencies,
  emptyLabel,
}: {
  dependencies: DashboardTaskDependency[];
  emptyLabel: string;
}) {
  if (!dependencies.length) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">{emptyLabel}</p>;
  }

  return (
    <div className="space-y-3">
      {dependencies.map((dependency, index) => (
        <div
          key={`${dependency.fromId}-${dependency.toId}-${index}`}
          className="grid items-center gap-3 md:grid-cols-[minmax(0,1fr)_40px_minmax(0,1fr)]"
        >
          <TaskNode
            id={dependency.fromId}
            subject={dependency.fromSubject}
            status={dependency.fromStatus}
          />
          <div className="hidden text-center text-zinc-400 md:block">→</div>
          <div className="text-center text-zinc-400 md:hidden">↓</div>
          <TaskNode
            id={dependency.toId}
            subject={dependency.toSubject}
            status={dependency.toStatus}
          />
        </div>
      ))}
    </div>
  );
}
