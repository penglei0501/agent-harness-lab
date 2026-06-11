"use client";

import { FormEvent, useMemo, useState } from "react";
import { GitBranch, Loader2, SearchCode } from "lucide-react";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkRehype from "remark-rehype";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import rehypeStringify from "rehype-stringify";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import type { RepoInsightReport } from "@/types/agent-data";

interface RepoInsightLabels {
  generator_title: string;
  generator_desc: string;
  form_url: string;
  form_placeholder: string;
  form_submit: string;
  form_generating: string;
  form_success: string;
  form_error: string;
  saved_to: string;
  report_title: string;
}

interface RepoInsightGeneratorProps {
  labels: RepoInsightLabels;
}

interface RepoInsightResponse {
  ok: boolean;
  report?: RepoInsightReport;
  error?: string;
}

const inputClass =
  "min-h-10 rounded-md border border-zinc-200 bg-white px-3 text-sm outline-none transition-colors focus:border-blue-500 dark:border-zinc-700 dark:bg-zinc-950";

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

export function RepoInsightGenerator({ labels }: RepoInsightGeneratorProps) {
  const [githubUrl, setGithubUrl] = useState("https://github.com/penglei0501/agent-harness-lab");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<RepoInsightReport | null>(null);

  const reportHtml = useMemo(
    () => (report ? renderMarkdown(report.markdown) : ""),
    [report]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);

    try {
      const response = await fetch("/api/repos/summarize/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_url: githubUrl }),
      });
      const payload = (await response.json()) as RepoInsightResponse;
      if (!response.ok || !payload.ok || !payload.report) {
        throw new Error(payload.error || labels.form_error);
      }
      setReport(payload.report);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : labels.form_error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SearchCode size={19} className="text-blue-500" />
            {labels.generator_title}
          </CardTitle>
        </CardHeader>
        <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">{labels.generator_desc}</p>

        <form onSubmit={handleSubmit} className="grid gap-4">
          <label className="grid gap-2 text-sm font-medium">
            {labels.form_url}
            <input
              className={inputClass}
              value={githubUrl}
              placeholder={labels.form_placeholder}
              onChange={(event) => setGithubUrl(event.target.value)}
              required
            />
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex min-h-10 items-center gap-2 rounded-md bg-zinc-900 px-4 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-wait disabled:opacity-70 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <GitBranch size={16} />}
              {loading ? labels.form_generating : labels.form_submit}
            </button>
            {report?.path && (
              <span className="text-sm text-blue-700 dark:text-blue-300">
                {labels.form_success}: {labels.saved_to} {report.path}
              </span>
            )}
          </div>
        </form>

        {error && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </p>
        )}
      </Card>

      {report && (
        <Card>
          <CardHeader>
            <CardTitle>{labels.report_title}</CardTitle>
          </CardHeader>
          <div
            className="prose-custom"
            dangerouslySetInnerHTML={{ __html: reportHtml }}
          />
        </Card>
      )}
    </section>
  );
}
