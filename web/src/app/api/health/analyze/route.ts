import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const execFileAsync = promisify(execFile);
const MAX_FILE_SIZE = 20 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set([".pdf", ".md", ".txt"]);

const WEB_ROOT = process.cwd();
const REPO_ROOT = path.resolve(WEB_ROOT, "..");
const INPUT_DIR = path.join(REPO_ROOT, "health_records", "input");
const OUTPUT_DIR = path.join(REPO_ROOT, "health_records", "output");

function jsonError(message: string, status = 400) {
  return NextResponse.json({ ok: false, error: message }, { status });
}

function sanitizeFilename(filename: string) {
  const parsed = path.parse(path.basename(filename));
  const ext = parsed.ext.toLowerCase();
  const base = parsed.name
    .normalize("NFKD")
    .replace(/[^\w.-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);

  if (!ALLOWED_EXTENSIONS.has(ext)) {
    throw new Error("Only .pdf, .md, and .txt files are supported.");
  }
  return `${base || "health-record"}-${Date.now()}${ext}`;
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

export async function POST(request: Request) {
  const formData = await request.formData();
  const file = formData.get("file");

  if (!(file instanceof File)) {
    return jsonError("Missing upload field: file");
  }
  if (file.size <= 0) {
    return jsonError("Uploaded file is empty.");
  }
  if (file.size > MAX_FILE_SIZE) {
    return jsonError("File is too large. Maximum size is 20MB.", 413);
  }

  let safeFilename: string;
  try {
    safeFilename = sanitizeFilename(file.name);
  } catch (error) {
    return jsonError(error instanceof Error ? error.message : "Invalid filename.");
  }

  await fs.mkdir(INPUT_DIR, { recursive: true });
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const inputPath = path.join(INPUT_DIR, safeFilename);
  const bytes = Buffer.from(await file.arrayBuffer());
  await fs.writeFile(inputPath, bytes);

  const python = await resolvePythonExecutable();
  try {
    await execFileAsync(
      python,
      ["-m", "agent_lab", "health", "analyze", inputPath],
      {
        cwd: REPO_ROOT,
        env: { ...process.env, PYTHONPATH: REPO_ROOT },
        timeout: 120_000,
        maxBuffer: 1024 * 1024 * 8,
      }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Health record processing failed.";
    return jsonError(message, 500);
  }

  const reportPath = path.join(OUTPUT_DIR, `${path.parse(safeFilename).name}.md`);
  try {
    const markdown = await fs.readFile(reportPath, "utf-8");
    return NextResponse.json({
      ok: true,
      filename: safeFilename,
      inputPath: path.relative(REPO_ROOT, inputPath),
      reportPath: path.relative(REPO_ROOT, reportPath),
      markdown,
    });
  } catch {
    return jsonError("Health report was not generated.", 500);
  }
}
