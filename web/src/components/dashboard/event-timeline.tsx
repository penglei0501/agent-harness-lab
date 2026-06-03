import type { DashboardEvent } from "@/types/agent-data";

const EVENT_STYLES: Record<string, string> = {
  task_created: "bg-blue-500",
  task_claimed: "bg-amber-500",
  task_completed: "bg-emerald-500",
};

function eventDotClass(type: string) {
  return EVENT_STYLES[type] ?? "bg-zinc-400";
}

export function EventTimeline({
  events,
  emptyLabel,
}: {
  events: DashboardEvent[];
  emptyLabel: string;
}) {
  if (!events.length) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">{emptyLabel}</p>;
  }

  return (
    <div className="space-y-0">
      {events.map((event, index) => (
        <div
          key={`${event.timestamp}-${event.type}-${index}`}
          className="grid grid-cols-[18px_1fr] gap-3"
        >
          <div className="relative flex justify-center">
            <span className={`mt-1.5 h-2.5 w-2.5 rounded-full ${eventDotClass(event.type)}`} />
            {index < events.length - 1 && (
              <span className="absolute top-5 h-full w-px bg-zinc-200 dark:bg-zinc-800" />
            )}
          </div>
          <div className="pb-5">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="font-medium">{event.type}</span>
              <span className="font-mono text-xs text-zinc-500">{event.timestamp || "-"}</span>
            </div>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
              #{event.taskId} {event.subject}
            </p>
            {event.owner !== "-" && (
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">owner: {event.owner}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
