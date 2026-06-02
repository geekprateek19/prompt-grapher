import * as path from "node:path";
import { spawn } from "node:child_process";

import * as vscode from "vscode";

import { createAnalyzeBridgeInvocation } from "@prompt-grapher/core";
import {
  BUG_PACK_FILENAMES,
  DEFAULT_AGENTS_FILE,
  DEFAULT_CURSOR_RULES_FILE,
  DEFAULT_HANDOFF_PACK_DIR,
  defaultBugPackDirForReport,
  defaultFeaturePackDirForRequest,
  FEATURE_PACK_FILENAMES,
  HANDOFF_PACK_FILENAMES,
  MEMORY_PACK_FILENAMES,
  ONBOARDING_DOC_FILENAMES,
  PromptGrapherAnalyzeOptions,
} from "@prompt-grapher/shared";

const API_KEY_SECRET = "promptGrapher.apiKey";
const OUTPUT_CHANNEL_NAME = "PromptGrapher";

type GenerateOptions = {
  reuseGraph: boolean;
  featureRequest?: string;
  forceFeaturePack?: boolean;
  bugReport?: string;
  forceBugPack?: boolean;
  forceHandoffPack?: boolean;
};

type PromptGrapherConfig = {
  bridgeCommand: string;
  pythonBin: string;
  pythonEntry: string;
  model: string;
  baseUrl: string;
  graphifyStrategy: "code-only" | "semantic";
  graphifyBackend: string;
  graphifyModel: string;
  graphifyArgs: string[];
  outputFile: string;
  agentsFile: string;
  legacyCursorRulesFile: string;
  onboardingDocsDir: string;
  memoryPackDir: string;
  featurePackDir: string;
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
    vscode.commands.registerCommand("promptGrapher.generateFeaturePack", async (resource?: vscode.Uri) => {
      const featureRequest = await vscode.window.showInputBox({
        title: "PromptGrapher Feature Request",
        prompt: "Example: Add payment gateway or Mujhe auth module modify karna hai",
        ignoreFocusOut: true,
        validateInput: (value) => (value.trim() ? undefined : "Feature request cannot be empty."),
      });

      if (!featureRequest) {
        return;
      }

      await runGenerateRules(
        context,
        output,
        {
          reuseGraph: false,
          featureRequest: featureRequest.trim(),
          forceFeaturePack: true,
        },
        resource,
      );
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

  const config = loadConfig(folder);
  const apiKey = await context.secrets.get(API_KEY_SECRET);
  const analyzeOptions = buildAnalyzeOptions(folder, config, options);
  const invocation = createAnalyzeBridgeInvocation(analyzeOptions, {
    cwd: folder.uri.fsPath,
    extensionPath: context.extensionUri.fsPath,
    cliCommand: config.bridgeCommand || undefined,
    pythonBin: config.pythonBin || undefined,
    pythonEntry: config.pythonEntry || undefined,
  });

  const env = {
    ...process.env,
    ...(apiKey ? { AI_API_KEY: apiKey } : {}),
    ...(config.model ? { AI_MODEL_NAME: config.model } : {}),
    ...(config.baseUrl ? { AI_BASE_URL: config.baseUrl } : {}),
  };

  output.clear();
  output.show(true);
  output.appendLine(`[PromptGrapher] Workspace: ${folder.uri.fsPath}`);
  output.appendLine(`[PromptGrapher] Bridge: ${invocation.displayCommand}`);

  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `PromptGrapher: analyzing ${folder.name}`,
        cancellable: true,
      },
      (_progress, token) =>
        new Promise<void>((resolve, reject) => {
          const child = spawn(invocation.command, invocation.args, {
            cwd: folder.uri.fsPath,
            env,
            shell: invocation.shell,
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
                ? `Unable to start '${invocation.command}'. Check PromptGrapher bridge settings.`
                : `PromptGrapher bridge failed to start: ${error.message}`;
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
              await openGeneratedFiles(folder, config, analyzeOptions);
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

function loadConfig(folder: vscode.WorkspaceFolder): PromptGrapherConfig {
  const config = vscode.workspace.getConfiguration("promptGrapher", folder.uri);

  return {
    bridgeCommand: config.get<string>("bridgeCommand", "prompt-grapher").trim(),
    pythonBin: config.get<string>("pythonBin", "").trim(),
    pythonEntry: config.get<string>("pythonEntry", "").trim(),
    model: config.get<string>("model", "").trim(),
    baseUrl: config.get<string>("baseUrl", "").trim(),
    graphifyStrategy: config.get<"code-only" | "semantic">("graphifyStrategy", "code-only"),
    graphifyBackend: config.get<string>("graphifyBackend", "").trim(),
    graphifyModel: config.get<string>("graphifyModel", "").trim(),
    graphifyArgs: config.get<string[]>("graphifyArgs", []),
    outputFile: config.get<string>("outputFile", DEFAULT_CURSOR_RULES_FILE).trim(),
    agentsFile: config.get<string>("agentsFile", DEFAULT_AGENTS_FILE).trim(),
    legacyCursorRulesFile: config.get<string>("legacyCursorRulesFile", "").trim(),
    onboardingDocsDir: config.get<string>("onboardingDocsDir", "").trim(),
    memoryPackDir: config.get<string>("memoryPackDir", "").trim(),
    featurePackDir: config.get<string>("featurePackDir", "").trim(),
    featureRequest: config.get<string>("featureRequest", "").trim(),
    bugPackDir: config.get<string>("bugPackDir", "").trim(),
    handoffPackDir: config.get<string>("handoffPackDir", "").trim(),
    showMetrics: config.get<boolean>("showMetrics", false),
  };
}

function buildAnalyzeOptions(
  folder: vscode.WorkspaceFolder,
  config: PromptGrapherConfig,
  options: GenerateOptions,
): PromptGrapherAnalyzeOptions {
  const featureRequest = options.featureRequest ?? config.featureRequest;
  const bugReport = options.bugReport;
  const featurePackDir =
    options.forceFeaturePack && featureRequest && !config.featurePackDir
      ? defaultFeaturePackDirForRequest(featureRequest)
      : config.featurePackDir;
  const bugPackDir =
    options.forceBugPack && bugReport && !config.bugPackDir
      ? defaultBugPackDirForReport(bugReport)
      : config.bugPackDir;
  const handoffPackDir = options.forceHandoffPack
    ? config.handoffPackDir || DEFAULT_HANDOFF_PACK_DIR
    : config.handoffPackDir;

  return {
    path: folder.uri.fsPath,
    bootstrapGraph: true,
    refreshGraph: !options.reuseGraph,
    graphifyStrategy: config.graphifyStrategy,
    graphifyBackend: config.graphifyBackend || undefined,
    graphifyModel: config.graphifyModel || undefined,
    graphifyArgs: config.graphifyArgs.filter((value) => value.trim().length > 0),
    model: config.model || undefined,
    baseUrl: config.baseUrl || undefined,
    outputFile: config.outputFile || undefined,
    agentsFile: config.agentsFile || undefined,
    legacyCursorRulesFile: config.legacyCursorRulesFile || undefined,
    onboardingDocsDir: config.onboardingDocsDir || undefined,
    memoryPackDir: config.memoryPackDir || undefined,
    featurePackDir: featurePackDir || undefined,
    featureRequest: featureRequest || undefined,
    bugPackDir: bugPackDir || undefined,
    bugReport: bugReport || undefined,
    handoffPackDir: handoffPackDir || undefined,
    quietMetrics: !config.showMetrics,
  };
}

async function openGeneratedFiles(
  folder: vscode.WorkspaceFolder,
  config: PromptGrapherConfig,
  analyzeOptions: PromptGrapherAnalyzeOptions,
): Promise<void> {
  await openIfPresent(folder, config.outputFile);
  await openIfPresent(folder, config.agentsFile);
  await openIfPresent(folder, config.legacyCursorRulesFile);

  if (analyzeOptions.onboardingDocsDir) {
    await openIfPresent(folder, path.join(analyzeOptions.onboardingDocsDir, ONBOARDING_DOC_FILENAMES[0]));
  }

  if (analyzeOptions.memoryPackDir) {
    await openIfPresent(folder, path.join(analyzeOptions.memoryPackDir, MEMORY_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(analyzeOptions.memoryPackDir, MEMORY_PACK_FILENAMES[4]));
  }

  if (analyzeOptions.featurePackDir) {
    await openIfPresent(folder, path.join(analyzeOptions.featurePackDir, FEATURE_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(analyzeOptions.featurePackDir, FEATURE_PACK_FILENAMES[4]));
  }

  if (analyzeOptions.bugPackDir) {
    await openIfPresent(folder, path.join(analyzeOptions.bugPackDir, BUG_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(analyzeOptions.bugPackDir, BUG_PACK_FILENAMES[4]));
  }

  if (analyzeOptions.handoffPackDir) {
    await openIfPresent(folder, path.join(analyzeOptions.handoffPackDir, HANDOFF_PACK_FILENAMES[0]));
    await openIfPresent(folder, path.join(analyzeOptions.handoffPackDir, HANDOFF_PACK_FILENAMES[6]));
  }
}

async function openIfPresent(folder: vscode.WorkspaceFolder, relativePath: string | undefined): Promise<void> {
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
