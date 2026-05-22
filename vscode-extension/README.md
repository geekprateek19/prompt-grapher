# PromptGrapher VS Code Extension

This extension is a thin VS Code bridge around the existing Python `prompt-grapher` CLI. It does not reimplement the parser or synthesizer in TypeScript. Instead, it runs your installed PromptGrapher backend against the current workspace and streams the logs into a VS Code output panel.

## What it does

- Adds `PromptGrapher: Generate Rules`
- Adds `PromptGrapher: Generate Rules (Reuse Graph)`
- Stores the API key in VS Code SecretStorage
- Forwards model, base URL, Graphify strategy, and output file settings to the Python CLI
- Opens the generated `.cursor/rules/project-rules.mdc` and `AGENTS.md` files after success

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
  "promptGrapher.showMetrics": false
}
```

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
