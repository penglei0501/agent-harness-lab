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

function assertRecipePath(outputPath: string) {
  const relative = path.relative(RECIPES_OUTPUT_DIR, outputPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Generated recipe path is outside recipes/output.");
  }
}

function resolveRecipePaths(stdout: string) {
  const paths = stdout
    .split(/\r?\n/)
    .map((line) => line.match(/^-\s+(.+?)(?:\s+-\s+.*)?$/)?.[1]?.trim())
    .filter((value): value is string => Boolean(value))
    .map((value) => path.resolve(REPO_ROOT, value));

  if (!paths.length) {
    throw new Error("Recipe option paths were not returned by agent_lab.");
  }

  for (const outputPath of paths) {
    assertRecipePath(outputPath);
  }
  return paths;
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

  await fs.mkdir(RECIPES_OUTPUT_DIR, { recursive: true });

  const python = await resolvePythonExecutable();
  const args = [
    "-m",
    "agent_lab",
    "recipes",
    "suggest-options",
    "--ingredients",
    ingredients,
    "--servings",
    String(servings),
    "--time",
    String(time),
    "--taste",
    taste,
    "--limit",
    "3",
  ];
  if (avoid) args.push("--avoid", avoid);

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
    const recipePaths = resolveRecipePaths(stdout);
    const options = await Promise.all(
      recipePaths.map(async (recipePath) => {
        const recipe = JSON.parse(await fs.readFile(recipePath, "utf-8"));
        return {
          ...recipe,
          path: path.relative(REPO_ROOT, recipePath),
        };
      })
    );
    return NextResponse.json({
      ok: true,
      options,
      recipe: options[0],
      path: options[0]?.path,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Recipe report was not generated.";
    return jsonError(message, 500);
  }
}
