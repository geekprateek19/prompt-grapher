export type BundledCliPlatform = `${string}-${string}`;

export function getBundledCliPlatformKey(
  platform: NodeJS.Platform = process.platform,
  arch: string = process.arch,
): BundledCliPlatform | null {
  if (platform === "win32") {
    if (arch === "x64") {
      return "win32-x64";
    }
    if (arch === "arm64") {
      return "win32-arm64";
    }
    return null;
  }

  if (platform === "darwin") {
    if (arch === "arm64") {
      return "darwin-arm64";
    }
    if (arch === "x64") {
      return "darwin-x64";
    }
    return null;
  }

  if (platform === "linux") {
    if (arch === "x64") {
      return "linux-x64";
    }
    if (arch === "arm64") {
      return "linux-arm64";
    }
    return null;
  }

  return null;
}

export function getBundledCliExecutableName(platform: NodeJS.Platform = process.platform): string {
  return platform === "win32" ? "prompt-grapher.exe" : "prompt-grapher";
}

export function getBundledCliRelativePath(
  platform: NodeJS.Platform = process.platform,
  arch: string = process.arch,
): string | null {
  const platformKey = getBundledCliPlatformKey(platform, arch);
  if (!platformKey) {
    return null;
  }

  return `bin/${platformKey}/${getBundledCliExecutableName(platform)}`;
}
