# PromptGrapher VS Code Extension

This folder is the legacy standalone scaffold. The new migration target now lives under `packages/vscode` inside the `pnpm` workspace, but this bridge remains useful until the TypeScript cutover is complete.

This extension is a thin VS Code bridge around the existing Python `prompt-grapher` CLI. It does not reimplement the parser or synthesizer in TypeScript. Instead, it runs your installed PromptGrapher backend against the current workspace and streams the logs into a VS Code output panel.

## What it does

- Adds `PromptGrapher: Generate Rules`
- Adds `PromptGrapher: Generate Rules (Reuse Graph)`
- Adds `PromptGrapher: Generate Bug Fix Pack`
- Adds `PromptGrapher: Generate Client Handoff Pack`
- Stores the API key in VS Code SecretStorage
- Forwards model, base URL, Graphify strategy, and output file settings to the Python CLI
- Opens the generated `.cursor/rules/project-rules.mdc` and `AGENTS.md` files after success
- Optionally generates onboarding docs when `PromptGrapher: Onboarding Docs Dir` is configured
- Optionally generates an assistant memory pack when `PromptGrapher: Memory Pack Dir` is configured
- Optionally generates a bug-fix context pack when `PromptGrapher: Bug Pack Dir` is configured
- Optionally generates a client handoff pack when `PromptGrapher: Handoff Pack Dir` is configured

## Requirements

1. Python 3.10+
2. PromptGrapher installed in an environment available from VS Code:

```powershell
pip install -e .
```

Or install the published package instead:

```powershell
pip install prompt-grapher
```

3. If the executable is not on `PATH`, set `PromptGrapher: CLI Path` to the full binary path.

Examples:

- Windows venv: `D:\prompt-grapher\.venv\Scripts\prompt-grapher.exe`
- Unix venv: `/path/to/.venv/bin/prompt-grapher`

## Recommended setup

1. Open VS Code settings.
2. Set `PromptGrapher: Model` if you do not already provide `AI_MODEL_NAME` via `.env`.
3. Run `PromptGrapher: Set API Key`.
4. Run `PromptGrapher: Generate Rules`.

The extension forwards these values as environment overrides:

- `AI_API_KEY`
- `AI_MODEL_NAME`
- `AI_BASE_URL`

Your existing local `.env` handling inside PromptGrapher still works.

## Workspace settings example

```json
{
  "promptGrapher.cliPath": "D:\\prompt-grapher\\.venv\\Scripts\\prompt-grapher.exe",
  "promptGrapher.model": "gpt-4.1-mini",
  "promptGrapher.graphifyStrategy": "code-only",
  "promptGrapher.onboardingDocsDir": "docs/onboarding",
  "promptGrapher.memoryPackDir": ".ai-memory",
  "promptGrapher.featureRequest": "Mujhe auth module modify karna hai",
  "promptGrapher.handoffPackDir": "docs/handoff",
  "promptGrapher.showMetrics": false
}
```

When `promptGrapher.onboardingDocsDir` is non-empty, the extension forwards `--onboarding-docs-dir` to the Python CLI and generates:

- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `DATABASE_FLOW.md`
- `API_MAP.md`
- `IMPORTANT_FILES.md`
- `HOW_TO_RUN.md`
- `KNOWN_RISKS.md`

When `promptGrapher.memoryPackDir` is non-empty, the extension forwards `--memory-pack-dir` and generates:

- `CLAUDE.md`
- `CURSOR_RULES.md`
- `CODING_STYLE.md`
- `PROJECT_MEMORY.md`
- `FEATURE_PROMPTS.md`

If `promptGrapher.featureRequest` is also set, PromptGrapher injects a request-specific context pack into `FEATURE_PROMPTS.md`, including relevant files and an exact prompt for the requested change.

When `promptGrapher.bugPackDir` is non-empty, the extension forwards `--bug-pack-dir` and the `Generate Bug Fix Pack` command forwards `--bug-report`, producing:

- `RELATED_FILES.md`
- `API_SUSPECTS.md`
- `DATABASE_SUSPECTS.md`
- `FRONTEND_SUSPECTS.md`
- `INVESTIGATION_PROMPT.md`
- `BACKEND_FIX_PROMPT.md`
- `REGRESSION_TEST_PROMPT.md`

When `promptGrapher.handoffPackDir` is non-empty, or when you run `Generate Client Handoff Pack`, the extension forwards `--handoff-pack-dir` and produces:

- `TECHNICAL_DOCS.md`
- `SETUP_GUIDE.md`
- `DEPLOYMENT_GUIDE.md`
- `API_DOCUMENTATION.md`
- `DATABASE_DOCUMENTATION.md`
- `FUTURE_IMPROVEMENTS.md`
- `AI_MAINTENANCE_PROMPTS.md`

## Development

```powershell
cd vscode-extension
npm install
npm run build
```

Open the `vscode-extension` folder in VS Code and press `F5` to launch an Extension Development Host.

## Packaging

From `vscode-extension/`:

```powershell
npm install -g @vscode/vsce
vsce package
```

## Limits of this scaffold

- The extension expects an installed `prompt-grapher` CLI.
- It does not bundle Python or Graphify into the VSIX.
- If you want a single-click install experience later, the next step is bundling a Python runtime or shipping a remote service backend.
