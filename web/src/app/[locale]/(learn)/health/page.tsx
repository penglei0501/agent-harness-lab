import { FileHeart, ListChecks, Terminal } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { EventTimeline } from "@/components/dashboard/event-timeline";
import { HealthReportViewer } from "@/components/health/health-report-viewer";
import { HealthUpload } from "@/components/health/health-upload";
import { getTranslations } from "@/lib/i18n-server";
import type { DashboardData } from "@/types/agent-data";
import dashboardJson from "@/data/generated/dashboard.json";

const data = dashboardJson as DashboardData;

function CommandBlock({ command }: { command: string }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 text-xs leading-6 text-zinc-100">
      <code>{command}</code>
    </pre>
  );
}

export default async function HealthPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslations(locale, "health");
  const reports = data.health?.reports ?? [];
  const healthEvents = data.events.recent.filter((event) => event.type.startsWith("health_"));
  const reportLabels = {
    safety_title: t("safety_title"),
    indicators_title: t("indicators_title"),
    interpretation_title: t("interpretation_title"),
    doctor_checklist_title: t("doctor_checklist_title"),
    lifestyle_title: t("lifestyle_title"),
    source_excerpt_title: t("source_excerpt_title"),
    copy_markdown: t("copy_markdown"),
    copied: t("copied"),
    download_markdown: t("download_markdown"),
    show_markdown: t("show_markdown"),
    hide_markdown: t("hide_markdown"),
    empty_section: t("empty_section"),
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="mt-2 max-w-3xl text-[var(--color-text-secondary)]">{t("subtitle")}</p>
      </div>

      <Card className="mb-6 border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileHeart size={18} className="text-emerald-600" />
            {t("safety_title")}
          </CardTitle>
        </CardHeader>
        <p className="text-sm text-emerald-900 dark:text-emerald-100">{t("safety_desc")}</p>
      </Card>

      <div className="mb-6">
        <HealthUpload
          labels={{
            title: t("upload_title"),
            description: t("upload_desc"),
            choose: t("upload_choose"),
            uploading: t("uploading"),
            success: t("upload_success"),
            error: t("upload_error"),
            markdown: t("generated_markdown"),
            ...reportLabels,
          }}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal size={18} />
              {t("run")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("run_desc")}</p>
          <CommandBlock command="python -m agent_lab health analyze health_records/input/checkup.txt" />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks size={18} />
              {t("output")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("output_desc")}</p>
          <CommandBlock command="python -m agent_lab health list" />
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("reports")}</CardTitle>
          </CardHeader>
          {reports.length ? (
            <div className="space-y-4">
              {reports.map((report) => (
                <HealthReportViewer
                  key={report.path}
                  report={report}
                  labels={reportLabels}
                  defaultOpen={false}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">{t("empty_reports")}</p>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("events")}</CardTitle>
          </CardHeader>
          <EventTimeline events={healthEvents} emptyLabel={t("empty_events")} />
        </Card>
      </div>
    </div>
  );
}
