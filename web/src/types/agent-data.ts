export interface AgentVersion {
  id: string;
  filename: string;
  title: string;
  subtitle: string;
  loc: number;
  tools: string[];
  newTools: string[];
  coreAddition: string;
  keyInsight: string;
  classes: { name: string; startLine: number; endLine: number }[];
  functions: { name: string; signature: string; startLine: number }[];
  layer: "tools" | "planning" | "memory" | "concurrency" | "collaboration";
  source: string;
}

export interface VersionDiff {
  from: string;
  to: string;
  newClasses: string[];
  newFunctions: string[];
  newTools: string[];
  locDelta: number;
}

export interface DocContent {
  version: string;
  locale: "en" | "zh";
  title: string;
  content: string; // raw markdown
}

export interface VersionIndex {
  versions: AgentVersion[];
  diffs: VersionDiff[];
}

export interface DashboardTask {
  id: string;
  subject: string;
  status: string;
  owner: string;
  blockedBy: string[];
}

export interface DashboardTaskDependency {
  fromId: string;
  fromSubject: string;
  fromStatus: string;
  toId: string;
  toSubject: string;
  toStatus: string;
}

export interface DashboardSkill {
  name: string;
  description: string;
  path: string;
}

export interface DashboardEvent {
  timestamp: string;
  type: string;
  taskId: string;
  owner: string;
  subject: string;
}

export interface DashboardPaperNote {
  title: string;
  path: string;
  source: string;
  wordCount: number;
  updatedAt: string;
}

export interface DashboardData {
  tasks: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    items: DashboardTask[];
    dependencies: DashboardTaskDependency[];
  };
  skills: {
    total: number;
    items: DashboardSkill[];
  };
  docs: {
    total: number;
    byLocale: Record<string, number>;
  };
  events: {
    total: number;
    recent: DashboardEvent[];
  };
  papers?: {
    total: number;
    notes: DashboardPaperNote[];
  };
}

export type SimStepType =
  | "user_message"
  | "assistant_text"
  | "tool_call"
  | "tool_result"
  | "system_event";

export interface SimStep {
  type: SimStepType;
  content: string;
  annotation: string;
  toolName?: string;
  toolInput?: string;
}

export interface Scenario {
  version: string;
  title: string;
  description: string;
  steps: SimStep[];
}

export interface FlowNode {
  id: string;
  label: string;
  type: "start" | "process" | "decision" | "subprocess" | "end";
  x: number;
  y: number;
}

export interface FlowEdge {
  from: string;
  to: string;
  label?: string;
}
