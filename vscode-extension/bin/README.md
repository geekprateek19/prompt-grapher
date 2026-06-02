# Bundled PromptGrapher CLI

Marketplace VSIX builds ship a standalone `prompt-grapher` binary here so users do not need to install Python separately.

Layout:

```text
bin/
  win32-x64/prompt-grapher.exe
  win32-arm64/prompt-grapher.exe
  darwin-arm64/prompt-grapher
  darwin-x64/prompt-grapher
  linux-x64/prompt-grapher
  linux-arm64/prompt-grapher
```

Build the binary for the current machine from the repo root:

```powershell
pip install -e .
pip install pyinstaller
python scripts/build_standalone_cli.py
```

Then package the extension:

```powershell
cd vscode-extension
npm run build
npm run package
```

The binaries are build artifacts. They are gitignored because they are large and platform-specific. CI should build all target platforms before publishing.
