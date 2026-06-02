import { existsSync } from "node:fs";
import * as path from "node:path";

const DEFAULT_CLI_COMMAND = "prompt-grapher";

function getBundledCliPlatformKey(): string | null {
  const { platform, arch } = process;

  if (platform === "win32") {
    return arch === "arm64" ? "win32-arm64" : arch === "x64" ? "win32-x64" : null;
  }

  if (platform === "darwin") {
    return arch === "arm64" ? "darwin-arm64" : arch === "x64" ? "darwin-x64" : null;
  }

  if (platform === "linux") {
    return arch === "arm64" ? "linux-arm64" : arch === "x64" ? "linux-x64" : null;
  }

  return null;
}

function getBundledCliPath(extensionPath: string): string | undefined {
  const platformKey = getBundledCliPlatformKey();
  if (!platformKey) {
    return undefined;
  }

  const executableName = process.platform === "win32" ? "prompt-grapher.exe" : "prompt-grapher";
  const candidate = path.join(extensionPath, "bin", platformKey, executableName);
  return existsSync(candidate) ? candidate : undefined;
}

export function resolvePromptGrapherCliPath(
  extensionPath: string,
  configuredCliPath: string | undefined,
): { cliPath: string; source: "bundled" | "configured" | "path" } {
  const configured = configuredCliPath?.trim();
  if (configured) {
    return { cliPath: configured, source: "configured" };
  }

  const bundled = getBundledCliPath(extensionPath);
  if (bundled) {
    return { cliPath: bundled, source: "bundled" };
  }

  return { cliPath: DEFAULT_CLI_COMMAND, source: "path" };
}

export function shouldSpawnWithShell(cliPath: string): boolean {
  if (process.platform !== "win32") {
    return false;
  }

  return !path.isAbsolute(cliPath) && !cliPath.toLowerCase().endsWith(".exe");
}

export function missingBundledCliMessage(): string {
  const platformKey = getBundledCliPlatformKey() ?? `${process.platform}-${process.arch}`;
  return (
    `PromptGrapher could not find a bundled CLI for ${platformKey}. ` +
    "Install the published VSIX build or set PromptGrapher: CLI Path."
  );
}
