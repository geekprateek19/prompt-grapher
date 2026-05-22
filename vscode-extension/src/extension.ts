import * as path from "node:path";
import { spawn } from "node:child_process";
import * as vscode from "vscode";

const API_KEY_SECRET = "promptGrapher.apiKey";
const OUTPUT_CHANNEL_NAME = "PromptGrapher";

type GenerateOptions = {
  reuseGraph: boolean;
};

type PromptGrapherConfig = {
  cliPath: string;
  model: string;
  baseUrl: string;
  graphifyStrategy: string;
  graphifyBackend: string;
  graphifyModel: string;
  graphifyArgs: string[];
  outputFile: string;
  agentsFile: string;
  legacyCursorRulesFile: string;
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
  if (!config.cliPath) {
    vscode.window.showErrorMessage("Set PromptGrapher: CLI Path before running the extension.");
    return;
  }

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
  output.appendLine(`[PromptGrapher] Command: ${config.cliPath} ${quoteArgs(args).join(" ")}`);

  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `PromptGrapher: generating rules for ${folder.name}`,
        cancellable: true,
      },
      (_progress, token) =>
        new Promise<void>((resolve, reject) => {
          const child = spawn(config.cliPath, args, {
            cwd: folder.uri.fsPath,
            env,
            shell: process.platform === "win32",
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
                ? `Unable to find '${config.cliPath}'. Install PromptGrapher first or set PromptGrapher: CLI Path.`
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
              await openGeneratedFiles(folder, config);
              vscode.window.showInformationMessage("PromptGrapher rules generated.");
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
    cliPath: config.get<string>("cliPath", "prompt-grapher").trim(),
    model: config.get<string>("model", "").trim(),
    baseUrl: config.get<string>("baseUrl", "").trim(),
    graphifyStrategy: config.get<string>("graphifyStrategy", "code-only").trim() || "code-only",
    graphifyBackend: config.get<string>("graphifyBackend", "").trim(),
    graphifyModel: config.get<string>("graphifyModel", "").trim(),
    graphifyArgs: config.get<string[]>("graphifyArgs", []),
    outputFile: config.get<string>("outputFile", ".cursor/rules/project-rules.mdc").trim(),
    agentsFile: config.get<string>("agentsFile", "AGENTS.md").trim(),
    legacyCursorRulesFile: config.get<string>("legacyCursorRulesFile", "").trim(),
    showMetrics: config.get<boolean>("showMetrics", false),
  };
}

function buildAnalyzeArgs(
  folder: vscode.WorkspaceFolder,
  config: PromptGrapherConfig,
  options: GenerateOptions,
): string[] {
  const args = ["analyze", folder.uri.fsPath];

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

  for (const graphifyArg of config.graphifyArgs) {
    if (graphifyArg.trim()) {
      args.push("--graphify-arg", graphifyArg);
    }
  }

  return args;
}

async function openGeneratedFiles(folder: vscode.WorkspaceFolder, config: PromptGrapherConfig): Promise<void> {
  await openIfPresent(folder, config.outputFile);
  await openIfPresent(folder, config.agentsFile);
  await openIfPresent(folder, config.legacyCursorRulesFile);
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
