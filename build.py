#!/usr/bin/env python3
"""Build Clip2VM into a standalone binary via PyInstaller.

Usage:
  python3 build.py              # build for current platform
  python3 build.py --clean      # clean + rebuild
  python3 build.py --install    # build + install to ~/.local/bin

Output: dist/clip2vm  (single-file executable, ~15-25 MB)

Runtime deps (NOT bundled — install on target machine):
  X11:  sudo apt install xdotool xclip
  Wayland: sudo apt install ydotool wl-clipboard
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
DIST = PROJECT / "dist"
NAME = "clip2vm"
ENTRY = PROJECT / "clip2vm-daemon.py"


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installing pyinstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean() -> None:
    for d in (DIST, PROJECT / "build"):
        if d.exists():
            shutil.rmtree(d)
    for f in PROJECT.glob("*.spec"):
        f.unlink()
    print("Cleaned.")


def build() -> Path:
    ensure_pyinstaller()

    print(f"Building {NAME} from {ENTRY} ...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", NAME,
        "--paths", str(PROJECT),
        "--collect-all", "pynput",
        "--hidden-import", "clip2vm.backends",
        "--hidden-import", "clip2vm.window",
        "--hidden-import", "clip2vm.client",
        "--clean",
        "--noconfirm",
        str(ENTRY),
    ]

    env = {**__import__("os").environ, "PYTHONPYCACHEPREFIX": str(PROJECT / "build" / "pycache")}

    subprocess.check_call(cmd, cwd=str(PROJECT), env=env)

    binary = DIST / NAME
    if not binary.exists():
        sys.exit(f"Build failed — {binary} not found.")

    size_mb = binary.stat().st_size / (1024 * 1024)
    print(f"\nDone: {binary}  ({size_mb:.1f} MB)")
    return binary


def install(binary: Path) -> None:
    target = Path.home() / ".local" / "bin" / NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary, target)
    print(f"Installed to {target}")
    if str(target.parent) not in __import__("os").environ.get("PATH", ""):
        print(f"  (ensure {target.parent} is on your PATH)")


def main() -> None:
    args = sys.argv[1:]

    if "--clean" in args:
        clean()
        if args == ["--clean"]:
            return

    binary = build()

    if "--install" in args:
        install(binary)

    print("\nRuntime deps required on target machine:")
    print("  X11:      sudo apt install xdotool xclip")
    print("  Wayland:  sudo apt install ydotool wl-clipboard")
    print(f"\nUsage:  {NAME}")


if __name__ == "__main__":
    main()
