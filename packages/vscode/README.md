# PromptGrapher Workspace VS Code Package

This package is the TypeScript-side VS Code shell for PromptGrapher's migration path.

It does not replace the Python backend yet. Instead it builds a new extension package inside the `pnpm` workspace and forwards generation requests to the existing Python CLI through a temporary bridge command.

## What it does

- Lives under `packages/vscode` so the extension is part of the TypeScript workspace
- Reuses `@prompt-grapher/core` to build analyze arguments consistently with the new Node CLI
- Still calls the Python `prompt-grapher analyze` implementation while the analyzer is being ported
- Adds a `Generate Feature Prompt Pack` command that injects a feature request and opens the generated feature-pack files
- Adds a `Generate Bug Fix Pack` command that turns a pasted symptom into related-file and investigation prompts
- Adds a `Generate Client Handoff Pack` command that emits technical, setup, deployment, API, database, roadmap, and maintenance docs
- Can also generate a dedicated feature implementation pack under `featurePackDir`

## Bridge settings

- `promptGrapher.bridgeCommand`
- `promptGrapher.pythonBin`
- `promptGrapher.pythonEntry`
- `promptGrapher.featurePackDir`
- `promptGrapher.bugPackDir`
- `promptGrapher.handoffPackDir`

Use `bridgeCommand` for a normal installed Python CLI such as `prompt-grapher`.

Use `pythonBin` plus `pythonEntry` when you want to run the local repo's `cli.py` directly during migration work.

## Development

From the repo root:

```powershell
corepack pnpm install
corepack pnpm --filter prompt-grapher-vscode build
```

Open `packages/vscode` in VS Code and press `F5` to start an Extension Development Host.
