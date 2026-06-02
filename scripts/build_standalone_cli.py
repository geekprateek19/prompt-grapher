from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "vscode-extension" / "bin"


def platform_key() -> str:
    system = sys.platform
    machine = platform.machine().lower()

    if system == "win32":
        if machine in {"amd64", "x86_64"}:
            return "win32-x64"
        if machine in {"arm64", "aarch64"}:
            return "win32-arm64"
        raise SystemExit(f"Unsupported Windows architecture: {machine}")

    if system == "darwin":
        if machine in {"arm64", "aarch64"}:
            return "darwin-arm64"
        if machine in {"x86_64", "amd64"}:
            return "darwin-x64"
        raise SystemExit(f"Unsupported macOS architecture: {machine}")

    if system.startswith("linux"):
        if machine in {"x86_64", "amd64"}:
            return "linux-x64"
        if machine in {"arm64", "aarch64"}:
            return "linux-arm64"
        raise SystemExit(f"Unsupported Linux architecture: {machine}")

    raise SystemExit(f"Unsupported platform: {system} ({machine})")


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is required. Install it in your build environment with:\n"
            "  pip install pyinstaller"
        ) from exc


def build() -> Path:
    ensure_pyinstaller()

    key = platform_key()
    output_dir = OUTPUT_ROOT / key
    dist_dir = ROOT / "build" / "standalone-cli" / key
    work_dir = ROOT / "build" / "standalone-cli" / f"{key}-work"
    executable_name = "prompt-grapher.exe" if sys.platform == "win32" else "prompt-grapher"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if work_dir.exists():
        shutil.rmtree(work_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(ROOT / "scripts" / "prompt-grapher.spec"),
        "--noconfirm",
        "--clean",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
    ]

    print(f"[prompt-grapher] Building standalone CLI for {key}...")
    subprocess.run(command, cwd=ROOT, check=True)

    built_binary = dist_dir / executable_name
    if not built_binary.exists():
        raise SystemExit(f"Expected PyInstaller output at {built_binary}")

    target_binary = output_dir / executable_name
    shutil.copy2(built_binary, target_binary)
    if sys.platform != "win32":
        target_binary.chmod(0o755)

    print(f"[prompt-grapher] Standalone CLI ready at {target_binary}")
    return target_binary


if __name__ == "__main__":
    build()
