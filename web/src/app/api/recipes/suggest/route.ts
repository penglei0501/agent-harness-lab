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
const RECIPES_OUTPUT_DIR = path.join(REPO_ROOT, "recipes", "output");

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

function cleanText(value: unknown, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

function cleanPositiveInt(value: unknown, fallback: number, min: number, max: number) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return Math.min(max, Math.max(min, Math.floor(numeric)));
}

function resolveRecipePath(stdout: string) {
  const match = stdout.match(/Generated recipe report:\s+(.+)\s*$/m);
  if (!match) {
    throw new Error("Recipe report path was not returned by agent_lab.");
  }

  const outputPath = path.resolve(REPO_ROOT, match[1].trim());
  const relative = path.relative(RECIPES_OUTPUT_DIR, outputPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Generated recipe path is outside recipes/output.");
  }
  return outputPath;
}

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return jsonError("Invalid JSON request body.");
  }

  const ingredients = cleanText(body.ingredients);
  if (!ingredients) {
    return jsonError("Ingredients are required.");
  }

  const servings = cleanPositiveInt(body.servings, 1, 1, 12);
  const time = cleanPositiveInt(body.time_minutes ?? body.time, 20, 5, 240);
  const taste = cleanText(body.taste, "balanced") || "balanced";
  const avoid = cleanText(body.avoid);
  const tools = cleanText(body.tools);

  await fs.mkdir(RECIPES_OUTPUT_DIR, { recursive: true });

  const python = await resolvePythonExecutable();
  const args = [
    "-m",
    "agent_lab",
    "recipes",
    "suggest",
    "--ingredients",
    ingredients,
    "--servings",
    String(servings),
    "--time",
    String(time),
    "--taste",
    taste,
  ];
  if (avoid) args.push("--avoid", avoid);
  if (tools) args.push("--tools", tools);

  let stdout = "";
  try {
    const result = await execFileAsync(python, args, {
      cwd: REPO_ROOT,
      env: { ...process.env, PYTHONPATH: REPO_ROOT },
      timeout: 60_000,
      maxBuffer: 1024 * 1024 * 4,
    });
    stdout = result.stdout;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Recipe generation failed.";
    return jsonError(message, 500);
  }

  try {
    const recipePath = resolveRecipePath(stdout);
    const recipe = JSON.parse(await fs.readFile(recipePath, "utf-8"));
    return NextResponse.json({
      ok: true,
      recipe,
      path: path.relative(REPO_ROOT, recipePath),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Recipe report was not generated.";
    return jsonError(message, 500);
  }
}
