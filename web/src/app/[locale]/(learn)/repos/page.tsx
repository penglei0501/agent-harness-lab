import { FileText, Terminal } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { RepoReportViewer } from "@/components/repos/repo-report-viewer";
import { RepoInsightGenerator } from "@/components/repos/repo-insight-generator";
import { getTranslations } from "@/lib/i18n-server";
import type { RepoInsightIndex } from "@/types/agent-data";
import reposJson from "@/data/generated/repos.json";

const repos = reposJson as RepoInsightIndex;

function CommandBlock({ command }: { command: string }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 text-xs leading-6 text-zinc-100">
      <code>{command}</code>
    </pre>
  );
}

export default async function ReposPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = getTranslations(locale, "repos");
  const generatorLabels = {
    generator_title: t("generator_title"),
    generator_desc: t("generator_desc"),
    form_url: t("form_url"),
    form_placeholder: t("form_placeholder"),
    form_submit: t("form_submit"),
    form_generating: t("form_generating"),
    form_success: t("form_success"),
    form_error: t("form_error"),
    form_refresh: t("form_refresh"),
    progress_fetch: t("progress_fetch"),
    progress_analyze: t("progress_analyze"),
    progress_write: t("progress_write"),
    saved_to: t("saved_to"),
    report_title: t("report_title"),
    copy_markdown: t("copy_markdown"),
    copied: t("copied"),
    download_markdown: t("download_markdown"),
    show_report: t("show_report"),
    hide_report: t("hide_report"),
    empty_summary: t("empty_summary"),
  };
  const reportLabels = {
    report_title: t("report_title"),
    copy_markdown: t("copy_markdown"),
    copied: t("copied"),
    download_markdown: t("download_markdown"),
    show_report: t("show_report"),
    hide_report: t("hide_report"),
    empty_summary: t("empty_summary"),
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="mt-2 max-w-3xl text-[var(--color-text-secondary)]">{t("subtitle")}</p>
      </div>

      <div className="mb-6">
        <RepoInsightGenerator labels={generatorLabels} />
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
          <CommandBlock command="python -m agent_lab repos summarize https://github.com/browser-use/browser-use" />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText size={18} />
              {t("list")}
            </CardTitle>
          </CardHeader>
          <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">{t("list_desc")}</p>
          <CommandBlock command="python -m agent_lab repos list" />
        </Card>
      </div>

      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">{t("reports")}</h2>
        <span className="text-sm text-zinc-500 dark:text-zinc-400">{repos.total}</span>
      </div>

      {repos.items.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {repos.items.map((report) => (
            <RepoReportViewer
              key={report.path}
              report={report}
              labels={reportLabels}
              defaultOpen={false}
            />
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
