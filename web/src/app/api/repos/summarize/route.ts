import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const execFileAsync = promisify(execFile);
const WEB_ROOT = process.cwd();
const REPO_ROOT = path.resolve(WEB_ROOT, "..");
const REPO_REPORTS_OUTPUT_DIR = path.join(REPO_ROOT, "github_reports", "output");

function jsonError(message: string, status = 400) {
  return NextResponse.json({ ok: false, error: message }, { status });
}

async function resolvePythonExecutable() {
  const configured = process.env.AGENT_LAB_PYTHON;
  if (configured) return configured;

  const venvPython = path.join(REPO_ROOT, ".venv", "bin", "python");
  try {
    await fs.access(venvPython);
    return venvPython;
  } catch {
    return "python3";
  }
}

function cleanText(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function assertGitHubUrl(value: string) {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("A valid GitHub repository URL is required.");
  }
  if (!["github.com", "www.github.com"].includes(url.hostname)) {
    throw new Error("Only github.com repository URLs are supported.");
  }
  const parts = url.pathname.split("/").filter(Boolean);
  if (parts.length < 2) {
    throw new Error("GitHub URL must include owner and repository name.");
  }
}

function resolveReportPath(stdout: string) {
  const line = stdout
    .split(/\r?\n/)
    .find((entry) => entry.startsWith("Generated repo report:"));
  const relativePath = line?.replace("Generated repo report:", "").trim();
  if (!relativePath) {
    throw new Error("Repository report path was not returned by agent_lab.");
  }

  const reportPath = path.resolve(REPO_ROOT, relativePath);
  const relative = path.relative(REPO_REPORTS_OUTPUT_DIR, reportPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Generated report path is outside github_reports/output.");
  }
  return reportPath;
}

function extractRepo(markdown: string, fallback: string) {
  const match = markdown.match(/^#\s+(.+?)\s+仓库技术分析\s*$/m);
  return match?.[1]?.trim() || fallback;
}

function extractSummary(markdown: string) {
  const lines = markdown.split(/\r?\n/);
  const startIndex = lines.findIndex((line) => /^##\s+1\.\s+一句话总结\s*$/.test(line.trim()));
  if (startIndex === -1) return "";

  const body: string[] = [];
  for (let i = startIndex + 1; i < lines.length; i++) {
    if (/^##\s+\d+\.\s+/.test(lines[i].trim())) break;
    body.push(lines[i]);
  }

  return body.join(" ").replace(/\s+/g, " ").trim();
}

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return jsonError("Invalid JSON request body.");
  }

  const githubUrl = cleanText(body.github_url ?? body.url);
  try {
    assertGitHubUrl(githubUrl);
  } catch (error) {
    return jsonError(error instanceof Error ? error.message : "Invalid GitHub URL.");
  }

  await fs.mkdir(REPO_REPORTS_OUTPUT_DIR, { recursive: true });
  const python = await resolvePythonExecutable();

  let stdout = "";
  try {
    const result = await execFileAsync(
      python,
      ["-m", "agent_lab", "repos", "summarize", githubUrl],
      {
        cwd: REPO_ROOT,
        env: { ...process.env, PYTHONPATH: REPO_ROOT },
        timeout: 120_000,
        maxBuffer: 1024 * 1024 * 8,
      }
    );
    stdout = result.stdout;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Repository summary failed.";
    return jsonError(message, 500);
  }

  try {
    const reportPath = resolveReportPath(stdout);
    const markdown = await fs.readFile(reportPath, "utf-8");
    const repo = extractRepo(markdown, path.basename(reportPath, ".md"));
    return NextResponse.json({
      ok: true,
      report: {
        title: repo,
        repo,
        path: path.relative(REPO_ROOT, reportPath),
        summary: extractSummary(markdown),
        markdown,
        updatedAt: new Date().toISOString(),
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Repository report was not generated.";
    return jsonError(message, 500);
  }
}
