import { FileText, FolderInput, ListChecks, Terminal } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { EventTimeline } from "@/components/dashboard/event-timeline";
import { PaperUpload } from "@/components/papers/paper-upload";
import { getTranslations } from "@/lib/i18n-server";
import type { DashboardData, DashboardPaperNote } from "@/types/agent-data";
import dashboardJson from "@/data/generated/dashboard.json";

const data = dashboardJson as DashboardData;

function CommandBlock({ command }: { command: string }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 text-xs leading-6 text-zinc-100">
      <code>{command}</code>
    </pre>
  );
}

function NoteRow({ note }: { note: DashboardPaperNote }) {
  return (
    <div className="border-b border-zinc-100 py-3 last:border-b-0 dark:border-zinc-800">
      <div className="flex flex-wrap items-center gap-2">
        <FileText size={16} className="text-blue-500" />
        <p className="text-sm font-medium">{note.title}</p>
      </div>
      <div className="mt-2 grid gap-1 text-xs text-zinc-500 dark:text-zinc-400">
        <span>{note.path}</span>
        <span>{note.wordCount.toLocaleString()} words</span>
      </div>
    </div>
  );
}

export default async function PapersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslations(locale, "papers");
  const notes = data.papers?.notes ?? [];
  const paperEvents = data.events.recent.filter((event) => event.type.startsWith("paper_"));

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="mt-2 max-w-3xl text-[var(--color-text-secondary)]">{t("subtitle")}</p>
      </div>

      <div className="mb-6">
        <PaperUpload
          labels={{
            title: t("upload_title"),
            description: t("upload_desc"),
            choose: t("upload_choose"),
            uploading: t("uploading"),
            success: t("upload_success"),
            error: t("upload_error"),
            markdown: t("generated_markdown"),
          }}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FolderInput size={18} />
              {t("input")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("input_desc")}</p>
          <CommandBlock command="mkdir -p papers/input papers/output" />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal size={18} />
              {t("run")}
            </CardTitle>
          </CardHeader>
          <div className="space-y-3">
            <CommandBlock command="python -m agent_lab papers read papers/input/example.pdf" />
            <CommandBlock command="python -m agent_lab papers read-folder papers/input" />
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks size={18} />
              {t("output")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("output_desc")}</p>
          <CommandBlock command="python -m agent_lab papers list" />
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("notes")}</CardTitle>
          </CardHeader>
          {notes.length ? (
            <div>
              {notes.map((note) => (
                <NoteRow key={note.path} note={note} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("empty_notes")}</p>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("events")}</CardTitle>
          </CardHeader>
          <EventTimeline events={paperEvents} emptyLabel={t("empty_events")} />
        </Card>
      </div>
    </div>
  );
}
