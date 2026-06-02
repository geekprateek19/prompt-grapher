import * as path from "node:path";
import { spawn } from "node:child_process";
import * as vscode from "vscode";

import { missingBundledCliMessage, resolvePromptGrapherCliPath, shouldSpawnWithShell } from "./resolveCliPath";

const API_KEY_SECRET = "promptGrapher.apiKey";
const OUTPUT_CHANNEL_NAME = "PromptGrapher";
const ONBOARDING_DOC_FILENAMES = [
  "PROJECT_OVERVIEW.md",
  "ARCHITECTURE.md",
  "DATABASE_FLOW.md",
  "API_MAP.md",
  "IMPORTANT_FILES.md",
  "HOW_TO_RUN.md",
  "KNOWN_RISKS.md",
] as const;
const MEMORY_PACK_FILENAMES = [
  "CLAUDE.md",
  "CURSOR_RULES.md",
  "CODING_STYLE.md",
  "PROJECT_MEMORY.md",
  "FEATURE_PROMPTS.md",
] as const;
const BUG_PACK_FILENAMES = [
  "RELATED_FILES.md",
  "API_SUSPECTS.md",
  "DATABASE_SUSPECTS.md",
  "FRONTEND_SUSPECTS.md",
  "INVESTIGATION_PROMPT.md",
  "BACKEND_FIX_PROMPT.md",
  "REGRESSION_TEST_PROMPT.md",
] as const;
const HANDOFF_PACK_FILENAMES = [
  "TECHNICAL_DOCS.md",
  "SETUP_GUIDE.md",
  "DEPLOYMENT_GUIDE.md",
  "API_DOCUMENTATION.md",
  "DATABASE_DOCUMENTATION.md",
  "FUTURE_IMPROVEMENTS.md",
  "AI_MAINTENANCE_PROMPTS.md",
] as const;

type GenerateOptions = {
  reuseGraph: boolean;
  bugReport?: string;
  forceBugPack?: boolean;
  forceHandoffPack?: boolean;
};

type PromptGrapherConfig = {
  cliPath: string;
  cliSource: "bundled" | "configured" | "path";
  model: string;
  baseUrl: string;
  graphifyStrategy: string;
  graphifyBackend: string;
  graphifyModel: string;
  graphifyArgs: string[];
  outputFile: string;
  agentsFile: string;
  legacyCursorRulesFile: string;
  onboardingDocsDir: string;
  memoryPackDir: string;
  featureRequest: string;
  bugPackDir: string;
  handoffPackDir: string;
  showMetrics: boolean;
};

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
  context.subscriptions.push(output);

  context.subscriptions.push(
    vscode.commands.registerCommand("promptGrapher.generateRules", async (resource?: vscode.Uri) => {
      await runGenerateRules(context, output, { reuseGraph: false }, resource);
    }),
    vscode.commands.registerCommand("promptGrapher.generateRulesReuseGraph", async (resource?: vscode.Uri) => {
      await runGenerateRules(context, output, { reuseGraph: true }, resource);
    }),
    vscode.commands.registerCommand("promptGrapher.generateBugFixPack", async (resource?: vscode.Uri) => {
      const bugReport = await vscode.window.showInputBox({
        title: "PromptGrapher Bug Report",
        prompt: "Example: Payment status is not updating after UPI success",
        ignoreFocusOut: true,
        validateInput: (value) => (value.trim() ? undefined : "Bug report cannot be empty."),
      });

      if (!bugReport) {
        return;
      }

      await runGenerateRules(
        context,
        output,
        {
          reuseGraph: false,
          bugReport: bugReport.trim(),
          forceBugPack: true,
        },
        resource,
      );
    }),
    vscode.commands.registerCommand("promptGrapher.generateClientHandoff", async (resource?: vscode.Uri) => {
      await runGenerateRules(
        context,
        output,
        {
          reuseGraph: false,
          forceHandoffPack: true,
        },
        resource,
      );
    }),
    vscode.commands.registerCommand("promptGrapher.setApiKey", async () => {
      await setApiKey(context);
    }),
    vscode.commands.registerCommand("promptGrapher.clearApiKey", async () => {
      await clearApiKey(context);
    }),
  );
}

export function deactivate(): void {}

async function runGenerateRules(
  context: vscode.ExtensionContext,
  output: vscode.OutputChannel,
  options: GenerateOptions,
  resource?: vscode.Uri,
): Promise<void> {
  const folder = await resolveWorkspaceFolder(resource);
  if (!folder) {
    vscode.window.showErrorMessage("PromptGrapher needs an open workspace folder.");
    return;
  }

  const config = loadConfig(context.extensionUri.fsPath, folder);

  const apiKey = await context.secrets.get(API_KEY_SECRET);
  const args = buildAnalyzeArgs(folder, config, options);
  const env = {
    ...process.env,
    ...(apiKey ? { AI_API_KEY: apiKey } : {}),
    ...(config.model ? { AI_MODEL_NAME: config.model } : {}),
    ...(config.baseUrl ? { AI_BASE_URL: config.baseUrl } : {}),
  };

  output.clear();
  output.show(true);
  output.appendLine(`[PromptGrapher] Workspace: ${folder.uri.fsPath}`);
  output.appendLine(`[PromptGrapher] CLI source: ${config.cliSource}`);
  output.appendLine(`[PromptGrapher] Command: ${config.cliPath} ${quoteArgs(args).join(" ")}`);

  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `PromptGrapher: analyzing ${folder.name}`,
        cancellable: true,
      },
      (_progress, token) =>
        new Promise<void>((resolve, reject) => {
          const child = spawn(config.cliPath, args, {
            cwd: folder.uri.fsPath,
            env,
            shell: shouldSpawnWithShell(config.cliPath),
          });

          let cancellationRequested = false;
          let settled = false;

          child.stdout.on("data", (chunk: Buffer | string) => {
            output.append(chunk.toString());
          });

          child.stderr.on("data", (chunk: Buffer | string) => {
            output.append(chunk.toString());
          });

          token.onCancellationRequested(() => {
            if (settled || cancellationRequested) {
              return;
            }

            cancellationRequested = true;
            output.appendLine("[PromptGrapher] Cancellation requested.");
            child.kill();
          });

          child.on("error", (error) => {
            if (settled) {
              return;
            }

            settled = true;
            const typedError = error as NodeJS.ErrnoException;
            const message =
              typedError.code === "ENOENT"
                ? config.cliSource === "path"
                  ? `${missingBundledCliMessage()} Current lookup: '${config.cliPath}'.`
                  : `Unable to run '${config.cliPath}'. Set PromptGrapher: CLI Path if you want to override the bundled CLI.`
                : `PromptGrapher failed to start: ${error.message}`;
            output.appendLine(`[PromptGrapher] ${message}`);
            vscode.window.showErrorMessage(message);
            reject(error);
          });

          child.on("close", async (code, signal) => {
            if (settled) {
              return;
            }

            settled = true;

            if (cancellationRequested) {
              output.appendLine("[PromptGrapher] Generation cancelled.");
              resolve();
              return;
            }

            if (code === 0) {
              output.appendLine("[PromptGrapher] Generation completed.");
              await openGeneratedFiles(folder, config, options);
              vscode.window.showInformationMessage("PromptGrapher generation completed.");
              resolve();
              return;
            }

            const details = signal ? `signal ${signal}` : `exit code ${code ?? "unknown"}`;
            const message = `PromptGrapher analyze failed with ${details}.`;
            output.appendLine(`[PromptGrapher] ${message}`);
            vscode.window.showErrorMessage(message);
            reject(new Error(message));
          });
        }),
    );
  } catch {
    // Errors are already surfaced through the output channel and VS Code notifications.
  }
}

async function setApiKey(context: vscode.ExtensionContext): Promise<void> {
  const value = await vscode.window.showInputBox({
    title: "PromptGrapher API Key",
    prompt: "Stored in VS Code SecretStorage and forwarded as AI_API_KEY.",
    password: true,
    ignoreFocusOut: true,
    validateInput: (input) => (input.trim() ? undefined : "API key cannot be empty."),
  });

  if (!value) {
    return;
  }

  await context.secrets.store(API_KEY_SECRET, value.trim());
  vscode.window.showInformationMessage("PromptGrapher API key stored.");
}

async function clearApiKey(context: vscode.ExtensionContext): Promise<void> {
  await context.secrets.delete(API_KEY_SECRET);
  vscode.window.showInformationMessage("PromptGrapher API key cleared.");
}

function loadConfig(extensionPath: string, folder?: vscode.WorkspaceFolder): PromptGrapherConfig {
  const config = vscode.workspace.getConfiguration("promptGrapher", folder?.uri);

  const configuredCliPath = config.get<string>("cliPath", "").trim();
  const resolvedCli = resolvePromptGrapherCliPath(extensionPath, configuredCliPath || undefined);

  return {
    cliPath: resolvedCli.cliPath,
    cliSource: resolvedCli.source,
    model: config.get<string>("model", "").trim(),
    baseUrl: config.get<string>("baseUrl", "").trim(),
    graphifyStrategy: config.get<string>("graphifyStrategy", "code-only").trim() || "code-only",
    graphifyBackend: config.get<string>("graphifyBackend", "").trim(),
    graphifyModel: config.get<string>("graphifyModel", "").trim(),
    graphifyArgs: config.get<string[]>("graphifyArgs", []),
    outputFile: config.get<string>("outputFile", ".cursor/rules/project-rules.mdc").trim(),
    agentsFile: config.get<string>("agentsFile", "AGENTS.md").trim(),
    legacyCursorRulesFile: config.get<string>("legacyCursorRulesFile", "").trim(),
    onboardingDocsDir: config.get<string>("onboardingDocsDir", "").trim(),
    memoryPackDir: config.get<string>("memoryPackDir", "").trim(),
    featureRequest: config.get<string>("featureRequest", "").trim(),
    bugPackDir: config.get<string>("bugPackDir", "").trim(),
    handoffPackDir: config.get<string>("handoffPackDir", "").trim(),
    showMetrics: config.get<boolean>("showMetrics", false),
  };
}

function slugifyRequest(value: string): string {
  const slug = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);

  return slug || "bug-report";
}

function resolveBugPackDir(config: PromptGrapherConfig, options: GenerateOptions): string {
  if (options.forceBugPack && options.bugReport && !config.bugPackDir) {
    return `.prompt-grapher/bugs/${slugifyRequest(options.bugReport)}`;
  }

  return config.bugPackDir;
}

function resolveHandoffPackDir(config: PromptGrapherConfig, options: GenerateOptions): string {
  if (options.forceHandoffPack && !config.handoffPackDir) {
    return "docs/handoff";
  }

  return config.handoffPackDir;
}

function buildAnalyzeArgs(
  folder: vscode.WorkspaceFolder,
  config: PromptGrapherConfig,
  options: GenerateOptions,
): string[] {
  const args = ["analyze", folder.uri.fsPath];
  const bugPackDir = resolveBugPackDir(config, options);
  const handoffPackDir = resolveHandoffPackDir(config, options);

  args.push(options.reuseGraph ? "--reuse-graph" : "--refresh-graph");
  args.push(config.showMetrics ? "--show-metrics" : "--quiet-metrics");
  args.push("--graphify-strategy", config.graphifyStrategy);

  if (config.graphifyBackend) {
    args.push("--graphify-backend", config.graphifyBackend);
  }

  if (config.graphifyModel) {
    args.push("--graphify-model", config.graphifyModel);
  }

  if (config.model) {
    args.push("--model", config.model);
  }

  if (config.baseUrl) {
    args.push("--base-url", config.baseUrl);
  }

  if (config.outputFile) {
    args.push("--output-file", config.outputFile);
  }

  if (config.agentsFile) {
    args.push("--agents-file", config.agentsFile);
  }

  if (config.legacyCursorRulesFile) {
    args.push("--legacy-cursorrules-file", config.legacyCursorRulesFile);
  }

  if (config.onboardingDocsDir) {
    args.push("--onboarding-docs-dir", config.onboardingDocsDir);
  }

  if (config.memoryPackDir) {
    args.push("--memory-pack-dir", config.memoryPackDir);
  }

  if (config.featureRequest) {
    args.push("--feature-request", config.featureRequest);
  }

  if (bugPackDir) {
    args.push("--bug-pack-dir", bugPackDir);
  }

  if (options.bugReport) {
    args.push("--bug-report", options.bugReport);
  }

  if (handoffPackDir) {
    args.push("--handoff-pack-dir", handoffPackDir);
  }

  for (const graphifyArg of config.graphifyArgs) {
    if (graphifyArg.trim()) {
      args.push("--graphify-arg", graphifyArg);
    }
  }

  return args;
}

async function openGeneratedFiles(
  folder: vscode.WorkspaceFolder,
  config: PromptGrapherConfig,
  options: GenerateOptions,
): Promise<void> {
  await openIfPresent(folder, config.outputFile);
  await openIfPresent(folder, config.agentsFile);
  await openIfPresent(folder, config.legacyCursorRulesFile);

  if (config.onboardingDocsDir) {
    await openIfPresent(folder, path.join(config.onboardingDocsDir, ONBOARDING_DOC_FILENAMES[0]));
  }

  if (config.memoryPackDir) {
    await openIfPresent(folder, path.join(config.memoryPackDir, MEMORY_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(config.memoryPackDir, MEMORY_PACK_FILENAMES[4]));
  }

  const bugPackDir = resolveBugPackDir(config, options);
  if (bugPackDir) {
    await openIfPresent(folder, path.join(bugPackDir, BUG_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(bugPackDir, BUG_PACK_FILENAMES[4]));
  }

  const handoffPackDir = resolveHandoffPackDir(config, options);
  if (handoffPackDir) {
    await openIfPresent(folder, path.join(handoffPackDir, HANDOFF_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(handoffPackDir, HANDOFF_PACK_FILENAMES[6]));
  }
}

async function openIfPresent(folder: vscode.WorkspaceFolder, relativePath: string): Promise<void> {
  if (!relativePath) {
    return;
  }

  const filePath = path.join(folder.uri.fsPath, relativePath);
  const uri = vscode.Uri.file(filePath);

  try {
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document, { preview: false, preserveFocus: true });
  } catch {
    // Skip auto-open when the file was intentionally not generated.
  }
}

async function resolveWorkspaceFolder(resource?: vscode.Uri): Promise<vscode.WorkspaceFolder | undefined> {
  if (resource) {
    const directMatch = vscode.workspace.getWorkspaceFolder(resource);
    if (directMatch) {
      return directMatch;
    }
  }

  const folders = vscode.workspace.workspaceFolders ?? [];
  if (folders.length === 0) {
    return undefined;
  }

  if (folders.length === 1) {
    return folders[0];
  }

  return vscode.window.showWorkspaceFolderPick({
    placeHolder: "Choose a workspace folder for PromptGrapher",
  });
}

function quoteArgs(args: string[]): string[] {
  return args.map((arg) => {
    if (!/[ \t"]/.test(arg)) {
      return arg;
    }

    return `"${arg.replace(/"/g, '\\"')}"`;
  });
}
