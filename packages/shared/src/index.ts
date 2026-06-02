export {
  getBundledCliExecutableName,
  getBundledCliPlatformKey,
  getBundledCliRelativePath,
} from "./bundledCli";
export type { BundledCliPlatform } from "./bundledCli";
export const DEFAULT_CURSOR_RULES_FILE = ".cursor/rules/project-rules.mdc";
export const DEFAULT_AGENTS_FILE = "AGENTS.md";
export const DEFAULT_ONBOARDING_DOCS_DIR = "docs/onboarding";
export const DEFAULT_MEMORY_PACK_DIR = ".ai-memory";
export const DEFAULT_FEATURE_PACK_DIR = ".prompt-grapher/features";
export const DEFAULT_BUG_PACK_DIR = ".prompt-grapher/bugs";
export const DEFAULT_HANDOFF_PACK_DIR = "docs/handoff";

export const ONBOARDING_DOC_FILENAMES = [
  "PROJECT_OVERVIEW.md",
  "ARCHITECTURE.md",
  "DATABASE_FLOW.md",
  "API_MAP.md",
  "IMPORTANT_FILES.md",
  "HOW_TO_RUN.md",
  "KNOWN_RISKS.md",
] as const;

export const MEMORY_PACK_FILENAMES = [
  "CLAUDE.md",
  "CURSOR_RULES.md",
  "CODING_STYLE.md",
  "PROJECT_MEMORY.md",
  "FEATURE_PROMPTS.md",
] as const;

export const FEATURE_PACK_FILENAMES = [
  "RELEVANT_FILES.md",
  "API_CONTEXT.md",
  "DATABASE_CHANGES.md",
  "FRONTEND_UPDATES.md",
  "BACKEND_PROMPT.md",
  "FRONTEND_PROMPT.md",
  "TEST_CASES_PROMPT.md",
  "MIGRATION_PROMPT.md",
] as const;

export const BUG_PACK_FILENAMES = [
  "RELATED_FILES.md",
  "API_SUSPECTS.md",
  "DATABASE_SUSPECTS.md",
  "FRONTEND_SUSPECTS.md",
  "INVESTIGATION_PROMPT.md",
  "BACKEND_FIX_PROMPT.md",
  "REGRESSION_TEST_PROMPT.md",
] as const;

export const HANDOFF_PACK_FILENAMES = [
  "TECHNICAL_DOCS.md",
  "SETUP_GUIDE.md",
  "DEPLOYMENT_GUIDE.md",
  "API_DOCUMENTATION.md",
  "DATABASE_DOCUMENTATION.md",
  "FUTURE_IMPROVEMENTS.md",
  "AI_MAINTENANCE_PROMPTS.md",
] as const;

export function slugifyFeatureRequest(request: string): string {
  const slug = request
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);

  return slug || "feature-request";
}

export function defaultFeaturePackDirForRequest(request: string): string {
  return `${DEFAULT_FEATURE_PACK_DIR}/${slugifyFeatureRequest(request)}`;
}

export function defaultBugPackDirForReport(report: string): string {
  return `${DEFAULT_BUG_PACK_DIR}/${slugifyFeatureRequest(report)}`;
}

export function defaultHandoffPackDir(): string {
  return DEFAULT_HANDOFF_PACK_DIR;
}

export type GraphifyStrategy = "code-only" | "semantic";

export interface PromptGrapherAnalyzeOptions {
  path: string;
  graphInput?: string;
  bootstrapGraph?: boolean;
  refreshGraph?: boolean;
  graphifyStrategy?: GraphifyStrategy;
  graphifyBin?: string;
  graphifyArgs?: string[];
  graphifyBackend?: string;
  graphifyModel?: string;
  model?: string;
  baseUrl?: string;
  apiKey?: string;
  outputFile?: string;
  agentsFile?: string;
  legacyCursorRulesFile?: string;
  onboardingDocsDir?: string;
  memoryPackDir?: string;
  featurePackDir?: string;
  featureRequest?: string;
  bugPackDir?: string;
  bugReport?: string;
  handoffPackDir?: string;
  quietMetrics?: boolean;
}

export interface PromptGrapherBridgeRuntimeOptions {
  cwd?: string;
  cliCommand?: string;
  extensionPath?: string;
  bundledCliPath?: string;
  pythonBin?: string;
  pythonEntry?: string;
}

export interface PromptGrapherBridgeInvocation {
  command: string;
  args: string[];
  cwd: string;
  shell: boolean;
  displayCommand: string;
}
