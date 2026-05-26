#!/usr/bin/env node

import { Command } from "commander";

import {
  buildFeatureAnalyzeOptions,
  buildBugAnalyzeOptions,
  buildHandoffAnalyzeOptions,
  createAnalyzeBridgeInvocation,
  runAnalyzeBridge,
} from "@prompt-grapher/core";
import {
  DEFAULT_AGENTS_FILE,
  DEFAULT_HANDOFF_PACK_DIR,
  DEFAULT_CURSOR_RULES_FILE,
  defaultBugPackDirForReport,
  defaultFeaturePackDirForRequest,
  PromptGrapherAnalyzeOptions,
  PromptGrapherBridgeRuntimeOptions,
} from "@prompt-grapher/shared";

type AnalyzeCommandFlags = {
  graphInput?: string;
  bootstrapGraph: boolean;
  reuseGraph?: boolean;
  graphifyStrategy?: "code-only" | "semantic";
  graphifyBin?: string;
  graphifyArg?: string[];
  graphifyBackend?: string;
  graphifyModel?: string;
  model?: string;
  baseUrl?: string;
  apiKey?: string;
  outputFile?: string;
  agentsFile?: string;
  legacyCursorrulesFile?: string;
  onboardingDocsDir?: string;
  memoryPackDir?: string;
  featurePackDir?: string;
  featureRequest?: string;
  bugPackDir?: string;
  bugReport?: string;
  handoffPackDir?: string;
  showMetrics?: boolean;
  bridgeCommand?: string;
  pythonBin?: string;
  pythonEntry?: string;
};

function collectRepeatedValue(value: string, previous: string[]): string[] {
  previous.push(value);
  return previous;
}

function toAnalyzeOptions(pathArg: string, flags: AnalyzeCommandFlags): PromptGrapherAnalyzeOptions {
  return {
    path: pathArg,
    graphInput: flags.graphInput,
    bootstrapGraph: flags.bootstrapGraph,
    refreshGraph: flags.reuseGraph ? false : true,
    graphifyStrategy: flags.graphifyStrategy,
    graphifyBin: flags.graphifyBin,
    graphifyArgs: flags.graphifyArg,
    graphifyBackend: flags.graphifyBackend,
    graphifyModel: flags.graphifyModel,
    model: flags.model,
    baseUrl: flags.baseUrl,
    apiKey: flags.apiKey,
    outputFile: flags.outputFile || DEFAULT_CURSOR_RULES_FILE,
    agentsFile: flags.agentsFile || DEFAULT_AGENTS_FILE,
    legacyCursorRulesFile: flags.legacyCursorrulesFile,
    onboardingDocsDir: flags.onboardingDocsDir,
    memoryPackDir: flags.memoryPackDir,
    featurePackDir: flags.featurePackDir,
    featureRequest: flags.featureRequest,
    bugPackDir: flags.bugPackDir,
    bugReport: flags.bugReport,
    handoffPackDir: flags.handoffPackDir,
    quietMetrics: flags.showMetrics ? false : true,
  };
}

function toRuntimeOptions(flags: AnalyzeCommandFlags): PromptGrapherBridgeRuntimeOptions {
  return {
    cliCommand: flags.bridgeCommand,
    pythonBin: flags.pythonBin,
    pythonEntry: flags.pythonEntry,
  };
}

async function executeAnalyze(options: PromptGrapherAnalyzeOptions, runtime: PromptGrapherBridgeRuntimeOptions): Promise<void> {
  const invocation = createAnalyzeBridgeInvocation(options, runtime);
  process.stderr.write(`[prompt-grapher bridge] ${invocation.displayCommand}\n`);

  const exitCode = await runAnalyzeBridge(options, runtime);
  if (exitCode !== 0) {
    process.exitCode = exitCode;
  }
}

const program = new Command();
program
  .name("prompt-grapher")
  .description("TypeScript workspace CLI that temporarily bridges to the existing Python PromptGrapher backend.")
  .showHelpAfterError();

program
  .command("analyze")
  .argument("[path]", "Project path to analyze.", ".")
  .option("--graph-input <path>", "Existing Graphify artifact path.")
  .option("--no-bootstrap-graph", "Disable Graphify auto-bootstrap when no artifact exists.")
  .option("--reuse-graph", "Reuse the current graphify-out artifact instead of refreshing it.")
  .option("--graphify-strategy <strategy>", "Graph bootstrap strategy.", "code-only")
  .option("--graphify-bin <path>", "Override the Graphify executable path.")
  .option("--graphify-arg <value>", "Additional Graphify arg. Repeat the flag for multiple values.", collectRepeatedValue, [])
  .option("--graphify-backend <backend>", "Graphify semantic backend override.")
  .option("--graphify-model <model>", "Graphify model override.")
  .option("--model <model>", "PromptGrapher model override.")
  .option("--base-url <url>", "PromptGrapher AI base URL override.")
  .option("--api-key <key>", "PromptGrapher AI API key override.")
  .option("--output-file <path>", "Cursor rules output path.", DEFAULT_CURSOR_RULES_FILE)
  .option("--agents-file <path>", "AGENTS.md output path.", DEFAULT_AGENTS_FILE)
  .option("--legacy-cursorrules-file <path>", "Legacy .cursorrules output path.")
  .option("--onboarding-docs-dir <path>", "Optional onboarding docs output directory.")
  .option("--memory-pack-dir <path>", "Optional assistant memory-pack output directory.")
  .option("--feature-pack-dir <path>", "Optional feature implementation prompt-pack output directory.")
  .option("--feature-request <request>", "Optional natural-language request for prompt-pack generation.")
  .option("--bug-pack-dir <path>", "Optional bug-fix context-pack output directory.")
  .option("--bug-report <report>", "Optional bug report used for debugging-context generation.")
  .option("--handoff-pack-dir <path>", "Optional client handoff pack output directory.")
  .option("--show-metrics", "Stream the Python heuristics payload to stdout.")
  .option("--bridge-command <command>", "Temporary bridge command. Defaults to the installed Python prompt-grapher CLI.")
  .option("--python-bin <path>", "Python executable used when bridging via a local cli.py script.")
  .option("--python-entry <path>", "Path to the Python cli.py entrypoint used for local migration work.")
  .action(async (pathArg: string, flags: AnalyzeCommandFlags) => {
    await executeAnalyze(toAnalyzeOptions(pathArg, flags), toRuntimeOptions(flags));
  });

program
  .command("feature")
  .argument("<request>", "Feature or change request.")
  .argument("[path]", "Project path to analyze.", ".")
  .option("--graph-input <path>", "Existing Graphify artifact path.")
  .option("--no-bootstrap-graph", "Disable Graphify auto-bootstrap when no artifact exists.")
  .option("--reuse-graph", "Reuse the current graphify-out artifact instead of refreshing it.")
  .option("--graphify-strategy <strategy>", "Graph bootstrap strategy.", "code-only")
  .option("--graphify-bin <path>", "Override the Graphify executable path.")
  .option("--graphify-arg <value>", "Additional Graphify arg. Repeat the flag for multiple values.", collectRepeatedValue, [])
  .option("--graphify-backend <backend>", "Graphify semantic backend override.")
  .option("--graphify-model <model>", "Graphify model override.")
  .option("--model <model>", "PromptGrapher model override.")
  .option("--base-url <url>", "PromptGrapher AI base URL override.")
  .option("--api-key <key>", "PromptGrapher AI API key override.")
  .option("--output-file <path>", "Cursor rules output path.", DEFAULT_CURSOR_RULES_FILE)
  .option("--agents-file <path>", "AGENTS.md output path.", DEFAULT_AGENTS_FILE)
  .option("--legacy-cursorrules-file <path>", "Legacy .cursorrules output path.")
  .option("--onboarding-docs-dir <path>", "Optional onboarding docs output directory.")
  .option("--memory-pack-dir <path>", "Optional assistant memory-pack output directory.")
  .option("--feature-pack-dir <path>", "Feature implementation prompt-pack output directory.")
  .option("--show-metrics", "Stream the Python heuristics payload to stdout.")
  .option("--bridge-command <command>", "Temporary bridge command. Defaults to the installed Python prompt-grapher CLI.")
  .option("--python-bin <path>", "Python executable used when bridging via a local cli.py script.")
  .option("--python-entry <path>", "Path to the Python cli.py entrypoint used for local migration work.")
  .action(async (request: string, pathArg: string, flags: AnalyzeCommandFlags) => {
    const analyzeOptions = buildFeatureAnalyzeOptions(request, {
      ...toAnalyzeOptions(pathArg, flags),
      featurePackDir: flags.featurePackDir || defaultFeaturePackDirForRequest(request),
    });
    await executeAnalyze(analyzeOptions, toRuntimeOptions(flags));
  });

program
  .command("bug")
  .argument("<report>", "Bug report or symptom statement.")
  .argument("[path]", "Project path to analyze.", ".")
  .option("--graph-input <path>", "Existing Graphify artifact path.")
  .option("--no-bootstrap-graph", "Disable Graphify auto-bootstrap when no artifact exists.")
  .option("--reuse-graph", "Reuse the current graphify-out artifact instead of refreshing it.")
  .option("--graphify-strategy <strategy>", "Graph bootstrap strategy.", "code-only")
  .option("--graphify-bin <path>", "Override the Graphify executable path.")
  .option("--graphify-arg <value>", "Additional Graphify arg. Repeat the flag for multiple values.", collectRepeatedValue, [])
  .option("--graphify-backend <backend>", "Graphify semantic backend override.")
  .option("--graphify-model <model>", "Graphify model override.")
  .option("--model <model>", "PromptGrapher model override.")
  .option("--base-url <url>", "PromptGrapher AI base URL override.")
  .option("--api-key <key>", "PromptGrapher AI API key override.")
  .option("--output-file <path>", "Cursor rules output path.", DEFAULT_CURSOR_RULES_FILE)
  .option("--agents-file <path>", "AGENTS.md output path.", DEFAULT_AGENTS_FILE)
  .option("--legacy-cursorrules-file <path>", "Legacy .cursorrules output path.")
  .option("--onboarding-docs-dir <path>", "Optional onboarding docs output directory.")
  .option("--memory-pack-dir <path>", "Optional assistant memory-pack output directory.")
  .option("--bug-pack-dir <path>", "Bug-fix context-pack output directory.")
  .option("--handoff-pack-dir <path>", "Optional client handoff pack output directory.")
  .option("--show-metrics", "Stream the Python heuristics payload to stdout.")
  .option("--bridge-command <command>", "Temporary bridge command. Defaults to the installed Python prompt-grapher CLI.")
  .option("--python-bin <path>", "Python executable used when bridging via a local cli.py script.")
  .option("--python-entry <path>", "Path to the Python cli.py entrypoint used for local migration work.")
  .action(async (report: string, pathArg: string, flags: AnalyzeCommandFlags) => {
    const analyzeOptions = buildBugAnalyzeOptions(report, {
      ...toAnalyzeOptions(pathArg, flags),
      bugPackDir: flags.bugPackDir || defaultBugPackDirForReport(report),
    });
    await executeAnalyze(analyzeOptions, toRuntimeOptions(flags));
  });

program
  .command("handoff")
  .argument("[path]", "Project path to analyze.", ".")
  .option("--graph-input <path>", "Existing Graphify artifact path.")
  .option("--no-bootstrap-graph", "Disable Graphify auto-bootstrap when no artifact exists.")
  .option("--reuse-graph", "Reuse the current graphify-out artifact instead of refreshing it.")
  .option("--graphify-strategy <strategy>", "Graph bootstrap strategy.", "code-only")
  .option("--graphify-bin <path>", "Override the Graphify executable path.")
  .option("--graphify-arg <value>", "Additional Graphify arg. Repeat the flag for multiple values.", collectRepeatedValue, [])
  .option("--graphify-backend <backend>", "Graphify semantic backend override.")
  .option("--graphify-model <model>", "Graphify model override.")
  .option("--model <model>", "PromptGrapher model override.")
  .option("--base-url <url>", "PromptGrapher AI base URL override.")
  .option("--api-key <key>", "PromptGrapher AI API key override.")
  .option("--output-file <path>", "Cursor rules output path.", DEFAULT_CURSOR_RULES_FILE)
  .option("--agents-file <path>", "AGENTS.md output path.", DEFAULT_AGENTS_FILE)
  .option("--legacy-cursorrules-file <path>", "Legacy .cursorrules output path.")
  .option("--onboarding-docs-dir <path>", "Optional onboarding docs output directory.")
  .option("--memory-pack-dir <path>", "Optional assistant memory-pack output directory.")
  .option("--handoff-pack-dir <path>", "Client handoff pack output directory.", DEFAULT_HANDOFF_PACK_DIR)
  .option("--show-metrics", "Stream the Python heuristics payload to stdout.")
  .option("--bridge-command <command>", "Temporary bridge command. Defaults to the installed Python prompt-grapher CLI.")
  .option("--python-bin <path>", "Python executable used when bridging via a local cli.py script.")
  .option("--python-entry <path>", "Path to the Python cli.py entrypoint used for local migration work.")
  .action(async (pathArg: string, flags: AnalyzeCommandFlags) => {
    const analyzeOptions = buildHandoffAnalyzeOptions({
      ...toAnalyzeOptions(pathArg, flags),
      handoffPackDir: flags.handoffPackDir || DEFAULT_HANDOFF_PACK_DIR,
    });
    await executeAnalyze(analyzeOptions, toRuntimeOptions(flags));
  });

program.parseAsync(process.argv).catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});
