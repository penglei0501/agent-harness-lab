"use client";

import { useMemo, useState } from "react";
import { Check, ClipboardList, Copy, Download, FileText, HeartPulse, Stethoscope } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardHealthReport } from "@/types/agent-data";

export interface HealthReportViewerLabels {
  safety_title: string;
  indicators_title: string;
  interpretation_title: string;
  doctor_checklist_title: string;
  lifestyle_title: string;
  source_excerpt_title: string;
  copy_markdown: string;
  copied: string;
  download_markdown: string;
  show_markdown: string;
  hide_markdown: string;
  empty_section: string;
}

interface HealthReportViewerProps {
  report: DashboardHealthReport;
  labels: HealthReportViewerLabels;
  defaultOpen?: boolean;
}

function extractSection(markdown: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const headingPattern = new RegExp(`^##\\s+\\d+\\.\\s+${escaped}\\s*$`);
  const nextHeadingPattern = /^##\s+\d+\.\s+/;
  const lines = markdown.split(/\r?\n/);
  const startIndex = lines.findIndex((line) => headingPattern.test(line.trim()));
  if (startIndex === -1) return "";

  const body: string[] = [];
  for (let i = startIndex + 1; i < lines.length; i++) {
    if (nextHeadingPattern.test(lines[i].trim())) break;
    body.push(lines[i]);
  }
  return body.join("\n").trim();
}

function listItems(markdownSection: string): string[] {
  return markdownSection
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- "))
    .map((line) => line.slice(2).trim());
}

function sourceExcerpt(markdownSection: string): string {
  const match = markdownSection.match(/```text\s*([\s\S]*?)```/);
  return (match?.[1] ?? markdownSection).trim();
}

function reportFilename(report: DashboardHealthReport): string {
  const name = report.path.split("/").pop() || `${report.title}.md`;
  return name.endsWith(".md") ? name : `${name}.md`;
}

function MiniSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-md border border-zinc-100 p-4 dark:border-zinc-800">
      <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h4>
      {children}
    </section>
  );
}

export function HealthReportViewer({
  report,
  labels,
  defaultOpen = false,
}: HealthReportViewerProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [copied, setCopied] = useState(false);
  const sections = useMemo(() => {
    const safety = extractSection(report.markdown, "Safety Notice");
    const indicators = listItems(extractSection(report.markdown, "Extracted Indicators"));
    const interpretation = listItems(extractSection(report.markdown, "General Interpretation Notes"));
    const checklist = listItems(extractSection(report.markdown, "Doctor Communication Checklist"));
    const lifestyle = listItems(extractSection(report.markdown, "Lifestyle Information"));
    const excerpt = sourceExcerpt(extractSection(report.markdown, "Source Excerpt"));
    return { safety, indicators, interpretation, checklist, lifestyle, excerpt };
  }, [report.markdown]);

  async function copyMarkdown() {
    await navigator.clipboard.writeText(report.markdown);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  function downloadMarkdown() {
    const blob = new Blob([report.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = reportFilename(report);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse size={18} className="text-emerald-500" />
              {report.title}
            </CardTitle>
            <div className="mt-2 grid gap-1 text-xs text-zinc-500 dark:text-zinc-400">
              <span>{report.path}</span>
              <span>{report.indicatorCount} indicators extracted</span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={copyMarkdown}
              className="inline-flex min-h-9 items-center gap-2 rounded-md border border-zinc-200 px-3 text-sm transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              {copied ? <Check size={15} /> : <Copy size={15} />}
              {copied ? labels.copied : labels.copy_markdown}
            </button>
            <button
              type="button"
              onClick={downloadMarkdown}
              className="inline-flex min-h-9 items-center gap-2 rounded-md border border-zinc-200 px-3 text-sm transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              <Download size={15} />
              {labels.download_markdown}
            </button>
            <button
              type="button"
              onClick={() => setOpen((value) => !value)}
              className="inline-flex min-h-9 items-center gap-2 rounded-md bg-zinc-900 px-3 text-sm text-white transition-colors hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              <FileText size={15} />
              {open ? labels.hide_markdown : labels.show_markdown}
            </button>
          </div>
        </div>
      </CardHeader>

      <div className="grid gap-4 lg:grid-cols-2">
        <MiniSection title={labels.safety_title} icon={<Stethoscope size={16} className="text-emerald-500" />}>
          <p className="text-sm leading-6 text-zinc-600 dark:text-zinc-300">
            {sections.safety || labels.empty_section}
          </p>
        </MiniSection>

        <MiniSection title={labels.indicators_title} icon={<ClipboardList size={16} className="text-blue-500" />}>
          {sections.indicators.length ? (
            <div className="flex flex-wrap gap-2">
              {sections.indicators.map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">{labels.empty_section}</p>
          )}
        </MiniSection>

        <MiniSection title={labels.interpretation_title} icon={<HeartPulse size={16} className="text-rose-500" />}>
          <ul className="list-disc space-y-2 pl-5 text-sm text-zinc-600 dark:text-zinc-300">
            {(sections.interpretation.length ? sections.interpretation : [labels.empty_section]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </MiniSection>

        <MiniSection title={labels.doctor_checklist_title} icon={<Stethoscope size={16} className="text-violet-500" />}>
          <ul className="list-disc space-y-2 pl-5 text-sm text-zinc-600 dark:text-zinc-300">
            {(sections.checklist.length ? sections.checklist : [labels.empty_section]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </MiniSection>

        <MiniSection title={labels.lifestyle_title} icon={<HeartPulse size={16} className="text-amber-500" />}>
          <ul className="list-disc space-y-2 pl-5 text-sm text-zinc-600 dark:text-zinc-300">
            {(sections.lifestyle.length ? sections.lifestyle : [labels.empty_section]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </MiniSection>

        <MiniSection title={labels.source_excerpt_title} icon={<FileText size={16} className="text-zinc-500" />}>
          <pre className="max-h-56 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-6 text-zinc-100">
            <code>{sections.excerpt || labels.empty_section}</code>
          </pre>
        </MiniSection>
      </div>

      {open && (
        <pre className="mt-5 max-h-[560px] overflow-auto rounded-md bg-zinc-950 p-4 text-xs leading-6 text-zinc-100">
          <code>{report.markdown}</code>
        </pre>
      )}
    </Card>
  );
}
