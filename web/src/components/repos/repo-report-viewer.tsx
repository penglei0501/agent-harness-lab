"use client";

import { useMemo, useState } from "react";
import { Check, Copy, Download, FileText, Github } from "lucide-react";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import rehypeStringify from "rehype-stringify";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import type { RepoInsightReport } from "@/types/agent-data";

export interface RepoReportViewerLabels {
  report_title: string;
  copy_markdown: string;
  copied: string;
  download_markdown: string;
  show_report: string;
  hide_report: string;
  empty_summary: string;
}

interface RepoReportViewerProps {
  report: RepoInsightReport;
  labels: RepoReportViewerLabels;
  defaultOpen?: boolean;
}

function renderMarkdown(markdown: string): string {
  const result = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeHighlight, { detect: false, ignoreMissing: true })
    .use(rehypeStringify)
    .processSync(markdown);
  return String(result).replace(
    /<pre><code class="hljs language-(\w+)">/g,
    '<pre class="code-block" data-language="$1"><code class="hljs language-$1">'
  );
}

function reportFilename(report: RepoInsightReport): string {
  const fallback = report.repo.replace(/[^A-Za-z0-9_.-]+/g, "-");
  const name = report.path.split("/").pop() || `${fallback}.md`;
  return name.endsWith(".md") ? name : `${name}.md`;
}

export function RepoReportViewer({
  report,
  labels,
  defaultOpen = true,
}: RepoReportViewerProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [copied, setCopied] = useState(false);
  const reportHtml = useMemo(() => renderMarkdown(report.markdown), [report.markdown]);

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
              <Github size={18} className="text-blue-500" />
              {report.repo || labels.report_title}
            </CardTitle>
            <p className="mt-2 line-clamp-2 text-sm text-zinc-500 dark:text-zinc-400">
              {report.summary || labels.empty_summary}
            </p>
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
              {open ? labels.hide_report : labels.show_report}
            </button>
          </div>
        </div>
      </CardHeader>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-100 pt-4 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
        <span>{report.path}</span>
        <span>{new Date(report.updatedAt).toLocaleString()}</span>
      </div>

      {open && (
        <div
          className="prose-custom mt-5"
          dangerouslySetInnerHTML={{ __html: reportHtml }}
        />
      )}
    </Card>
  );
}
