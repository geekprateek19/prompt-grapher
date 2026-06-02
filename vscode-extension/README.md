# PromptGrapher VS Code Extension

This extension ships a bundled PromptGrapher CLI so users do not need to install Python or run `pip install prompt-grapher` separately.

It runs PromptGrapher against the current workspace and streams logs into the VS Code Output panel.

## What it does

- Adds `PromptGrapher: Generate Rules`
- Adds `PromptGrapher: Generate Rules (Reuse Graph)`
- Adds `PromptGrapher: Generate Bug Fix Pack`
- Adds `PromptGrapher: Generate Client Handoff Pack`
- Uses the bundled CLI by default
- Stores the API key in VS Code SecretStorage
- Opens generated files after success

Optional packs are enabled through settings:

- onboarding docs via `promptGrapher.onboardingDocsDir`
- memory pack via `promptGrapher.memoryPackDir`
- feature request context via `promptGrapher.featureRequest`

## User setup

1. Install the extension from Marketplace or from a `.vsix`.
2. Open a project folder in VS Code.
3. Run `PromptGrapher: Set API Key`.
4. Run `PromptGrapher: Generate Rules`.

No Python install is required for end users.

## Optional override

If you want to use a local development build instead of the bundled CLI, set:

```json
{
  "promptGrapher.cliPath": "D:\\prompt-grapher\\.venv\\Scripts\\prompt-grapher.exe"
}
```

Leave `promptGrapher.cliPath` blank in normal use.

## Publisher build flow

Build the standalone CLI for the current platform:

```powershell
pip install -e .
pip install pyinstaller
python scripts/build_standalone_cli.py
```

Build and package the extension:

```powershell
cd vscode-extension
npm install
npm run build
npm run package
```

The VSIX will include:

```text
vscode-extension/bin/<platform>/prompt-grapher(.exe)
```

For Marketplace releases, build the standalone CLI on:

- Windows x64
- Windows arm64
- macOS arm64
- macOS x64
- Linux x64
- Linux arm64

Then assemble one VSIX per platform, or use a CI matrix that uploads platform-specific VSIX builds.

## Development

```powershell
cd vscode-extension
npm install
npm run build
```

For local F5 debugging without a bundled binary, either:

- run `python scripts/build_standalone_cli.py` once, or
- set `promptGrapher.cliPath` to your local venv executable

Press `F5` from the repo root to launch the Extension Development Host.

## Limits

- The bundled CLI makes the VSIX larger than a pure TypeScript extension.
- Marketplace packaging still needs one standalone build per target OS/architecture.
- A future TypeScript-native backend can remove the bundled Python runtime entirely.
