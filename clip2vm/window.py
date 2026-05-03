"""Query the currently focused window via xdotool."""

import subprocess
from dataclasses import dataclass


@dataclass
class Window:
    wid: str
    title: str


def get_active_window() -> Window | None:
    """Return the currently focused window, or None."""
    try:
        wid = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=1,
        ).stdout.strip()
        if not wid:
            return None
        title = subprocess.run(
            ["xdotool", "getwindowname", wid],
            capture_output=True, text=True, timeout=1,
        ).stdout.strip()
        return Window(wid=wid, title=title)
    except Exception:
        return None


def get_all_visible_windows() -> list[Window]:
    """Return all visible windows."""
    try:
        ids = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "."],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip().split()
        if not ids:
            return []
    except Exception:
        return []

    windows: list[Window] = []
    for wid in ids:
        try:
            title = subprocess.run(
                ["xdotool", "getwindowname", wid],
                capture_output=True, text=True, timeout=1,
            ).stdout.strip()
            windows.append(Window(wid=wid, title=title))
        except Exception:
            pass
    return windows
