import * as fs from "fs";
import * as path from "path";
import type {
  AgentVersion,
  VersionDiff,
  DocContent,
  VersionIndex,
  DashboardData,
  DashboardEvent,
  DashboardSkill,
  DashboardTask,
  DashboardTaskDependency,
  DashboardPaperNote,
  RepoInsightIndex,
  RepoInsightReport,
  RecipeIndex,
  RecipeReport,
} from "../src/types/agent-data";
import { VERSION_META, VERSION_ORDER, LEARNING_PATH } from "../src/lib/constants";

// Resolve paths relative to this script's location (web/scripts/)
const WEB_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(WEB_DIR, "..");
const AGENTS_DIR = path.join(REPO_ROOT, "agents");
const DOCS_DIR = path.join(REPO_ROOT, "docs");
const TASKS_DIR = path.join(REPO_ROOT, ".tasks");
const SKILLS_DIR = path.join(REPO_ROOT, "skills");
const EVENTS_PATH = path.join(REPO_ROOT, ".agent_lab", "events.jsonl");
const PAPERS_OUTPUT_DIR = path.join(REPO_ROOT, "papers", "output");
const RECIPES_OUTPUT_DIR = path.join(REPO_ROOT, "recipes", "output");
const GITHUB_REPORTS_OUTPUT_DIR = path.join(REPO_ROOT, "github_reports", "output");
const OUT_DIR = path.join(WEB_DIR, "src", "data", "generated");

// Map python filenames to version IDs
// s01_agent_loop.py -> s01
// s02_tools.py -> s02
// s_full.py -> s_full (reference agent, typically skipped)
function filenameToVersionId(filename: string): string | null {
  const base = path.basename(filename, ".py");
  if (base === "s_full") return null;
  if (base === "__init__") return null;

  const match = base.match(/^(s\d+[a-c]?)_/);
  if (!match) return null;
  return match[1];
}

// Extract classes from Python source
function extractClasses(
  lines: string[]
): { name: string; startLine: number; endLine: number }[] {
  const classes: { name: string; startLine: number; endLine: number }[] = [];
  const classPattern = /^class\s+(\w+)/;

  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(classPattern);
    if (m) {
      const name = m[1];
      const startLine = i + 1;
      // Find end of class: next class/function at indent 0, or EOF
      let endLine = lines.length;
      for (let j = i + 1; j < lines.length; j++) {
        if (
          lines[j].match(/^class\s/) ||
          lines[j].match(/^def\s/) ||
          (lines[j].match(/^\S/) && lines[j].trim() !== "" && !lines[j].startsWith("#") && !lines[j].startsWith("@"))
        ) {
          endLine = j;
          break;
        }
      }
      classes.push({ name, startLine, endLine });
    }
  }
  return classes;
}

// Extract top-level functions from Python source
function extractFunctions(
  lines: string[]
): { name: string; signature: string; startLine: number }[] {
  const functions: { name: string; signature: string; startLine: number }[] = [];
  const funcPattern = /^def\s+(\w+)\((.*?)\)/;

  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(funcPattern);
    if (m) {
      functions.push({
        name: m[1],
        signature: `def ${m[1]}(${m[2]})`,
        startLine: i + 1,
      });
    }
  }
  return functions;
}

// Extract tool names from Python source
// Looks for "name": "tool_name" patterns in dict literals
function extractTools(source: string): string[] {
  const toolPattern = /"name"\s*:\s*"(\w+)"/g;
  const tools = new Set<string>();
  let m;
  while ((m = toolPattern.exec(source)) !== null) {
    tools.add(m[1]);
  }
  return Array.from(tools);
}

// Count non-blank, non-comment lines
function countLoc(lines: string[]): number {
  return lines.filter((line) => {
    const trimmed = line.trim();
    return trimmed !== "" && !trimmed.startsWith("#");
  }).length;
}

// Extract version from doc filename (e.g., "s01-the-agent-loop.md" -> "s01")
function extractDocVersion(filename: string): string | null {
  const m = filename.match(/^(s\d+[a-c]?)-/);
  return m ? m[1] : null;
}

function readJsonFile(filePath: string): any | null {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8"));
  } catch {
    return null;
  }
}

function repoRelative(filePath: string): string {
  return path.relative(REPO_ROOT, filePath).replaceAll(path.sep, "/");
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}

function asRecipeSteps(value: unknown): RecipeReport["steps"] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === "object")
    .map((item, index) => {
      const step = item as Record<string, unknown>;
      return {
        order: Number(step.order ?? index + 1),
        title: String(step.title ?? `Step ${index + 1}`),
        description: String(step.description ?? ""),
        time_minutes: Number(step.time_minutes ?? 0),
      };
    });
}

function asRecipeSubstitutions(value: unknown): RecipeReport["substitutions"] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === "object")
    .map((item) => {
      const substitution = item as Record<string, unknown>;
      return {
        original: String(substitution.original ?? ""),
        alternative: String(substitution.alternative ?? ""),
      };
    })
    .filter((item) => item.original || item.alternative);
}

function extractRepoNameFromReport(content: string, fallback: string): string {
  const match = content.match(/^#\s+(.+?)\s+仓库技术分析\s*$/m);
  return match?.[1]?.trim() || fallback;
}

function extractSection(content: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const headingPattern = new RegExp(`^##\\s+\\d+\\.\\s+${escaped}\\s*$`);
  const nextHeadingPattern = /^##\s+\d+\.\s+/;
  const lines = content.split(/\r?\n/);
  const startIndex = lines.findIndex((line) => headingPattern.test(line.trim()));
  if (startIndex === -1) return "";

  const body: string[] = [];
  for (let i = startIndex + 1; i < lines.length; i++) {
    if (nextHeadingPattern.test(lines[i].trim())) break;
    body.push(lines[i]);
  }
  return body.join("\n").trim();
}

function buildRepoInsightIndex(): RepoInsightIndex {
  const reportItems: RepoInsightReport[] = [];
  if (!fs.existsSync(GITHUB_REPORTS_OUTPUT_DIR)) {
    return { total: 0, items: [] };
  }

  const reportFiles = fs
    .readdirSync(GITHUB_REPORTS_OUTPUT_DIR)
    .filter((file) => file.endsWith(".md"))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

  for (const file of reportFiles) {
    const filePath = path.join(GITHUB_REPORTS_OUTPUT_DIR, file);
    const content = fs.readFileSync(filePath, "utf-8");
    const repo = extractRepoNameFromReport(content, path.basename(file, ".md").replace("-", "/"));
    const summary = extractSection(content, "一句话总结")
      .replace(/\s+/g, " ")
      .trim();
    const stat = fs.statSync(filePath);

    reportItems.push({
      title: repo,
      repo,
      path: repoRelative(filePath),
      summary,
      markdown: content,
      updatedAt: stat.mtime.toISOString(),
    });
  }

  return {
    total: reportItems.length,
    items: reportItems.reverse(),
  };
}

function extractSkillMeta(content: string): { name?: string; description?: string } {
  if (!content.startsWith("---")) return {};
  const end = content.indexOf("\n---", 3);
  if (end === -1) return {};

  const meta = content.slice(3, end).trim().split(/\r?\n/);
  const result: { name?: string; description?: string } = {};
  let currentKey: "name" | "description" | null = null;
  let currentLines: string[] = [];

  function flushBlock() {
    if (currentKey === "description") {
      result.description = currentLines.join(" ").trim();
    }
    currentKey = null;
    currentLines = [];
  }

  for (const line of meta) {
    if (/^\s+/.test(line) && currentKey === "description") {
      currentLines.push(line.trim());
      continue;
    }
    flushBlock();

    const [rawKey, ...rest] = line.split(":");
    if (!rawKey || rest.length === 0) continue;
    const key = rawKey.trim();
    const value = rest.join(":").trim();
    if (key === "name") {
      result.name = value;
    } else if (key === "description") {
      if (value === "|") {
        currentKey = "description";
      } else {
        result.description = value;
      }
    }
  }
  flushBlock();
  return result;
}

function buildDashboardData(docs: DocContent[]): DashboardData {
  const taskItems: DashboardTask[] = [];
  if (fs.existsSync(TASKS_DIR)) {
    const taskFiles = fs
      .readdirSync(TASKS_DIR)
      .filter((file) => file.endsWith(".json"))
      .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

    for (const file of taskFiles) {
      const data = readJsonFile(path.join(TASKS_DIR, file));
      if (!data || typeof data !== "object") continue;
      taskItems.push({
        id: String(data.id ?? path.basename(file, ".json")),
        subject: String(data.subject ?? data.title ?? "(untitled)"),
        status: String(data.status ?? "unknown"),
        owner: String(data.owner || "-"),
        blockedBy: Array.isArray(data.blockedBy) ? data.blockedBy.map(String) : [],
      });
    }
  }

  const statusCount = (status: string) =>
    taskItems.filter((task) => task.status === status).length;

  const taskById = new Map(taskItems.map((task) => [task.id, task]));
  const dependencyItems: DashboardTaskDependency[] = [];
  for (const task of taskItems) {
    for (const dependencyId of task.blockedBy) {
      const dependency = taskById.get(dependencyId);
      dependencyItems.push({
        fromId: dependencyId,
        fromSubject: dependency?.subject ?? "(missing task)",
        fromStatus: dependency?.status ?? "missing",
        toId: task.id,
        toSubject: task.subject,
        toStatus: task.status,
      });
    }
  }

  const skillItems: DashboardSkill[] = [];
  if (fs.existsSync(SKILLS_DIR)) {
    const skillDirs = fs
      .readdirSync(SKILLS_DIR)
      .map((dir) => path.join(SKILLS_DIR, dir, "SKILL.md"))
      .filter((filePath) => fs.existsSync(filePath))
      .sort();

    for (const filePath of skillDirs) {
      const content = fs.readFileSync(filePath, "utf-8");
      const meta = extractSkillMeta(content);
      skillItems.push({
        name: meta.name ?? path.basename(path.dirname(filePath)),
        description: meta.description ?? "(no description)",
        path: repoRelative(filePath),
      });
    }
  }

  const docsByLocale: Record<string, number> = {};
  for (const doc of docs) {
    docsByLocale[doc.locale] = (docsByLocale[doc.locale] ?? 0) + 1;
  }

  const eventItems: DashboardEvent[] = [];
  if (fs.existsSync(EVENTS_PATH)) {
    const lines = fs.readFileSync(EVENTS_PATH, "utf-8").split(/\r?\n/);
    for (const line of lines) {
      if (!line.trim()) continue;
      const data = readJsonLine(line);
      if (!data) continue;
      eventItems.push({
        timestamp: String(data.timestamp ?? ""),
        type: String(data.type ?? "unknown"),
        taskId: String(data.task_id ?? "-"),
        owner: String(data.owner || "-"),
        subject: String(data.subject ?? data.title ?? data.paper ?? data.note_path ?? "-"),
      });
    }
  }

  const paperItems: DashboardPaperNote[] = [];
  if (fs.existsSync(PAPERS_OUTPUT_DIR)) {
    const noteFiles = fs
      .readdirSync(PAPERS_OUTPUT_DIR)
      .filter((file) => file.endsWith(".md"))
      .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

    for (const file of noteFiles) {
      const filePath = path.join(PAPERS_OUTPUT_DIR, file);
      const content = fs.readFileSync(filePath, "utf-8");
      const titleMatch = content.match(/^#\s+Paper Note:\s+(.+)$/m);
      const sourceMatch = content.match(/^- Source:\s+`(.+)`$/m);
      const wordCountMatch = content.match(/^- Approx\. word count:\s+(\d+)$/m);
      const stat = fs.statSync(filePath);
      paperItems.push({
        title: titleMatch?.[1] ?? path.basename(file, ".md"),
        path: repoRelative(filePath),
        source: sourceMatch?.[1] ?? "-",
        wordCount: Number(wordCountMatch?.[1] ?? 0),
        updatedAt: stat.mtime.toISOString(),
      });
    }
  }

  const repoReports = buildRepoInsightIndex();

  return {
    tasks: {
      total: taskItems.length,
      pending: statusCount("pending"),
      in_progress: statusCount("in_progress"),
      completed: statusCount("completed"),
      items: taskItems,
      dependencies: dependencyItems,
    },
    skills: {
      total: skillItems.length,
      items: skillItems,
    },
    docs: {
      total: docs.length,
      byLocale: docsByLocale,
    },
    events: {
      total: eventItems.length,
      recent: eventItems.slice(-10).reverse(),
    },
    papers: {
      total: paperItems.length,
      notes: paperItems.slice(-12).reverse(),
    },
    repos: {
      total: repoReports.total,
      reports: repoReports.items.slice(0, 8),
    },
  };
}

function buildRecipeIndex(): RecipeIndex {
  const recipeItems: RecipeReport[] = [];
  if (!fs.existsSync(RECIPES_OUTPUT_DIR)) {
    return { total: 0, items: [] };
  }

  const recipeFiles = fs
    .readdirSync(RECIPES_OUTPUT_DIR)
    .filter((file) => file.endsWith(".json"))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

  for (const file of recipeFiles) {
    const filePath = path.join(RECIPES_OUTPUT_DIR, file);
    const data = readJsonFile(filePath);
    if (!data || typeof data !== "object") continue;
    const recipe = data as Record<string, unknown>;

    recipeItems.push({
      title: String(recipe.title ?? path.basename(file, ".json")),
      summary: String(recipe.summary ?? ""),
      servings: Number(recipe.servings ?? 1),
      time_minutes: Number(recipe.time_minutes ?? 0),
      difficulty: String(recipe.difficulty ?? "-"),
      taste: String(recipe.taste ?? "-"),
      avoid: asStringList(recipe.avoid),
      tools: asStringList(recipe.tools),
      ingredients_used: asStringList(recipe.ingredients_used),
      missing_ingredients: asStringList(recipe.missing_ingredients),
      steps: asRecipeSteps(recipe.steps),
      shopping_list: asStringList(recipe.shopping_list),
      substitutions: asRecipeSubstitutions(recipe.substitutions),
      notes: asStringList(recipe.notes),
      recommendation_reason: String(recipe.recommendation_reason ?? ""),
      path: repoRelative(filePath),
    });
  }

  return {
    total: recipeItems.length,
    items: recipeItems.reverse(),
  };
}

function readJsonLine(line: string): any | null {
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}

// Main extraction
function main() {
  console.log("Extracting content from agents and docs...");
  console.log(`  Repo root: ${REPO_ROOT}`);
  console.log(`  Agents dir: ${AGENTS_DIR}`);
  console.log(`  Docs dir: ${DOCS_DIR}`);

  // Skip extraction if source directories don't exist (e.g. Vercel build).
  // Pre-committed generated data will be used instead.
  if (!fs.existsSync(AGENTS_DIR)) {
    console.log("  Agents directory not found, skipping extraction.");
    console.log("  Using pre-committed generated data.");
    return;
  }

  // 1. Read all agent files
  const agentFiles = fs
    .readdirSync(AGENTS_DIR)
    .filter((f) => f.startsWith("s") && f.endsWith(".py"));

  console.log(`  Found ${agentFiles.length} agent files`);

  const versions: AgentVersion[] = [];

  for (const filename of agentFiles) {
    const versionId = filenameToVersionId(filename);
    if (!versionId) {
      console.warn(`  Skipping ${filename}: could not determine version ID`);
      continue;
    }

    const filePath = path.join(AGENTS_DIR, filename);
    const source = fs.readFileSync(filePath, "utf-8");
    const lines = source.split("\n");

    const meta = VERSION_META[versionId];
    const classes = extractClasses(lines);
    const functions = extractFunctions(lines);
    const tools = extractTools(source);
    const loc = countLoc(lines);

    versions.push({
      id: versionId,
      filename,
      title: meta?.title ?? versionId,
      subtitle: meta?.subtitle ?? "",
      loc,
      tools,
      newTools: [], // computed after all versions are loaded
      coreAddition: meta?.coreAddition ?? "",
      keyInsight: meta?.keyInsight ?? "",
      classes,
      functions,
      layer: meta?.layer ?? "tools",
      source,
    });
  }

  // Sort versions according to VERSION_ORDER
  const orderMap = new Map(VERSION_ORDER.map((v, i) => [v, i]));
  versions.sort(
    (a, b) => (orderMap.get(a.id as any) ?? 99) - (orderMap.get(b.id as any) ?? 99)
  );

  // 2. Compute newTools for each version
  for (let i = 0; i < versions.length; i++) {
    const prev = i > 0 ? new Set(versions[i - 1].tools) : new Set<string>();
    versions[i].newTools = versions[i].tools.filter((t) => !prev.has(t));
  }

  // 3. Compute diffs between adjacent versions in LEARNING_PATH
  const diffs: VersionDiff[] = [];
  const versionMap = new Map(versions.map((v) => [v.id, v]));

  for (let i = 1; i < LEARNING_PATH.length; i++) {
    const fromId = LEARNING_PATH[i - 1];
    const toId = LEARNING_PATH[i];
    const fromVer = versionMap.get(fromId);
    const toVer = versionMap.get(toId);

    if (!fromVer || !toVer) continue;

    const fromClassNames = new Set(fromVer.classes.map((c) => c.name));
    const fromFuncNames = new Set(fromVer.functions.map((f) => f.name));
    const fromToolNames = new Set(fromVer.tools);

    diffs.push({
      from: fromId,
      to: toId,
      newClasses: toVer.classes
        .map((c) => c.name)
        .filter((n) => !fromClassNames.has(n)),
      newFunctions: toVer.functions
        .map((f) => f.name)
        .filter((n) => !fromFuncNames.has(n)),
      newTools: toVer.tools.filter((t) => !fromToolNames.has(t)),
      locDelta: toVer.loc - fromVer.loc,
    });
  }

  // 4. Read doc files from locale subdirectories (en/, zh/)
  const docs: DocContent[] = [];

  if (fs.existsSync(DOCS_DIR)) {
    const localeDirs = ["en", "zh"] as const;
    let totalDocFiles = 0;

    for (const locale of localeDirs) {
      const localeDir = path.join(DOCS_DIR, locale);
      if (!fs.existsSync(localeDir)) continue;

      const docFiles = fs
        .readdirSync(localeDir)
        .filter((f) => f.endsWith(".md"));

      totalDocFiles += docFiles.length;

      for (const filename of docFiles) {
        const version = extractDocVersion(filename);
        if (!version) {
          console.warn(`  Skipping doc ${locale}/${filename}: could not determine version`);
          continue;
        }

        const filePath = path.join(localeDir, filename);
        const content = fs.readFileSync(filePath, "utf-8");

        const titleMatch = content.match(/^#\s+(.+)$/m);
        const title = titleMatch ? titleMatch[1] : filename;

        docs.push({ version, locale, title, content });
      }
    }

    console.log(`  Found ${totalDocFiles} doc files across ${localeDirs.length} locales`);
  } else {
    console.warn(`  Docs directory not found: ${DOCS_DIR}`);
  }

  // 5. Write output
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const index: VersionIndex = { versions, diffs };
  const indexPath = path.join(OUT_DIR, "versions.json");
  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2));
  console.log(`  Wrote ${indexPath}`);

  const docsPath = path.join(OUT_DIR, "docs.json");
  fs.writeFileSync(docsPath, JSON.stringify(docs, null, 2));
  console.log(`  Wrote ${docsPath}`);

  const dashboard = buildDashboardData(docs);
  const dashboardPath = path.join(OUT_DIR, "dashboard.json");
  fs.writeFileSync(dashboardPath, JSON.stringify(dashboard, null, 2));
  console.log(`  Wrote ${dashboardPath}`);

  const recipes = buildRecipeIndex();
  const recipesPath = path.join(OUT_DIR, "recipes.json");
  fs.writeFileSync(recipesPath, JSON.stringify(recipes, null, 2));
  console.log(`  Wrote ${recipesPath}`);

  const repos = buildRepoInsightIndex();
  const reposPath = path.join(OUT_DIR, "repos.json");
  fs.writeFileSync(reposPath, JSON.stringify(repos, null, 2));
  console.log(`  Wrote ${reposPath}`);

  // Summary
  console.log("\nExtraction complete:");
  console.log(`  ${versions.length} versions`);
  console.log(`  ${diffs.length} diffs`);
  console.log(`  ${docs.length} docs`);
  console.log(`  ${dashboard.tasks.total} tasks`);
  console.log(`  ${dashboard.skills.total} skills`);
  console.log(`  ${dashboard.events.total} events`);
  console.log(`  ${dashboard.papers?.total ?? 0} paper notes`);
  console.log(`  ${recipes.total} recipe reports`);
  console.log(`  ${repos.total} repository reports`);
  for (const v of versions) {
    console.log(
      `    ${v.id}: ${v.loc} LOC, ${v.tools.length} tools, ${v.classes.length} classes, ${v.functions.length} functions`
    );
  }
}

main();
