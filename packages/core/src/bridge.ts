import { existsSync } from "node:fs";
import * as path from "node:path";
import { spawn } from "node:child_process";

import {
  DEFAULT_BUG_PACK_DIR,
  DEFAULT_FEATURE_PACK_DIR,
  DEFAULT_HANDOFF_PACK_DIR,
  getBundledCliRelativePath,
  PromptGrapherAnalyzeOptions,
  PromptGrapherBridgeInvocation,
  PromptGrapherBridgeRuntimeOptions,
} from "@prompt-grapher/shared";

function appendFlag(args: string[], flag: string, enabled: boolean | undefined, inverseFlag: string): void {
  if (enabled === undefined) {
    return;
  }

  args.push(enabled ? flag : inverseFlag);
}

function appendValue(args: string[], flag: string, value: string | undefined): void {
  if (!value) {
    return;
  }

  args.push(flag, value);
}

function quoteArg(arg: string): string {
  if (!/[ \t"]/.test(arg)) {
    return arg;
  }

  return `"${arg.replace(/"/g, '\\"')}"`;
}

function resolveExistingEntry(candidate: string, cwd: string): string | undefined {
  const resolvedCandidate = path.isAbsolute(candidate) ? candidate : path.resolve(cwd, candidate);
  return existsSync(resolvedCandidate) ? resolvedCandidate : undefined;
}

export function buildAnalyzeArgs(options: PromptGrapherAnalyzeOptions): string[] {
  const args = ["analyze", options.path];

  appendValue(args, "--graph-input", options.graphInput);
  appendFlag(args, "--bootstrap-graph", options.bootstrapGraph, "--no-bootstrap-graph");
  appendFlag(args, "--refresh-graph", options.refreshGraph, "--reuse-graph");
  appendValue(args, "--graphify-strategy", options.graphifyStrategy);
  appendValue(args, "--graphify-bin", options.graphifyBin);

  for (const graphifyArg of options.graphifyArgs ?? []) {
    if (graphifyArg.trim()) {
      args.push("--graphify-arg", graphifyArg);
    }
  }

  appendValue(args, "--graphify-backend", options.graphifyBackend);
  appendValue(args, "--graphify-model", options.graphifyModel);
  appendValue(args, "--model", options.model);
  appendValue(args, "--base-url", options.baseUrl);
  appendValue(args, "--api-key", options.apiKey);
  appendValue(args, "--output-file", options.outputFile);
  appendValue(args, "--agents-file", options.agentsFile);
  appendValue(args, "--legacy-cursorrules-file", options.legacyCursorRulesFile);
  appendValue(args, "--onboarding-docs-dir", options.onboardingDocsDir);
  appendValue(args, "--memory-pack-dir", options.memoryPackDir);
  appendValue(args, "--feature-pack-dir", options.featurePackDir);
  appendValue(args, "--feature-request", options.featureRequest);
  appendValue(args, "--bug-pack-dir", options.bugPackDir);
  appendValue(args, "--bug-report", options.bugReport);
  appendValue(args, "--handoff-pack-dir", options.handoffPackDir);
  appendFlag(args, "--quiet-metrics", options.quietMetrics, "--show-metrics");

  return args;
}

export function buildFeatureAnalyzeOptions(
  request: string,
  options: Omit<PromptGrapherAnalyzeOptions, "featureRequest">,
): PromptGrapherAnalyzeOptions {
  return {
    ...options,
    featureRequest: request,
    featurePackDir: options.featurePackDir ?? DEFAULT_FEATURE_PACK_DIR,
  };
}

export function buildBugAnalyzeOptions(
  report: string,
  options: Omit<PromptGrapherAnalyzeOptions, "bugReport">,
): PromptGrapherAnalyzeOptions {
  return {
    ...options,
    bugReport: report,
    bugPackDir: options.bugPackDir ?? DEFAULT_BUG_PACK_DIR,
  };
}

export function buildHandoffAnalyzeOptions(
  options: PromptGrapherAnalyzeOptions,
): PromptGrapherAnalyzeOptions {
  return {
    ...options,
    handoffPackDir: options.handoffPackDir ?? DEFAULT_HANDOFF_PACK_DIR,
  };
}

function resolveBundledCliPath(extensionPath: string | undefined): string | undefined {
  if (!extensionPath) {
    return undefined;
  }

  const relativePath = getBundledCliRelativePath();
  if (!relativePath) {
    return undefined;
  }

  const candidate = path.resolve(extensionPath, relativePath);
  return existsSync(candidate) ? candidate : undefined;
}

function shouldUseShell(command: string, usesPythonEntry: boolean): boolean {
  if (process.platform !== "win32") {
    return false;
  }

  if (usesPythonEntry) {
    return true;
  }

  return !path.isAbsolute(command) && !command.toLowerCase().endsWith(".exe");
}

export function createAnalyzeBridgeInvocation(
  options: PromptGrapherAnalyzeOptions,
  runtimeOptions: PromptGrapherBridgeRuntimeOptions = {},
): PromptGrapherBridgeInvocation {
  const cwd = path.resolve(runtimeOptions.cwd ?? process.cwd());
  const bundledCliPath = runtimeOptions.bundledCliPath?.trim() || resolveBundledCliPath(runtimeOptions.extensionPath);
  const explicitCommand =
    runtimeOptions.cliCommand?.trim() || process.env.PROMPT_GRAPHER_BRIDGE_COMMAND?.trim();

  let command = explicitCommand || "prompt-grapher";
  let commandArgs: string[] = [];
  let usesPythonEntry = false;

  if (bundledCliPath && !explicitCommand) {
    command = bundledCliPath;
    commandArgs = [];
  } else if (!explicitCommand) {
    const pythonBin = runtimeOptions.pythonBin?.trim() || process.env.PROMPT_GRAPHER_PYTHON_BIN?.trim() || "python";
    const explicitEntry = runtimeOptions.pythonEntry?.trim() || process.env.PROMPT_GRAPHER_PYTHON_ENTRY?.trim();
    const localEntry = explicitEntry
      ? resolveExistingEntry(explicitEntry, cwd)
      : resolveExistingEntry("cli.py", cwd);

    if (localEntry) {
      command = pythonBin;
      commandArgs = [localEntry];
      usesPythonEntry = true;
    }
  }

  const args = [...commandArgs, ...buildAnalyzeArgs(options)];
  return {
    command,
    args,
    cwd,
    shell: shouldUseShell(command, usesPythonEntry),
    displayCommand: [command, ...args].map(quoteArg).join(" "),
  };
}

export async function runAnalyzeBridge(
  options: PromptGrapherAnalyzeOptions,
  runtimeOptions: PromptGrapherBridgeRuntimeOptions = {},
): Promise<number> {
  const invocation = createAnalyzeBridgeInvocation(options, runtimeOptions);

  return await new Promise<number>((resolve, reject) => {
    const child = spawn(invocation.command, invocation.args, {
      cwd: invocation.cwd,
      stdio: "inherit",
      shell: invocation.shell,
    });

    child.on("error", reject);
    child.on("close", (code) => {
      resolve(code ?? 1);
    });
  });
}
