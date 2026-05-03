"""Clip2VM — keyboard-injection clipboard delivery to VM windows.

Ctrl+Shift+Q reads the system clipboard and types it into the currently
focused window.  Nothing is installed on the VM.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime

from .backends import PasteBackend, XdotoolBackend, detect_backend
from .window import get_active_window


def read_clipboard() -> str:
    try:
        import pyperclip
        return pyperclip.paste()
    except ImportError:
        sys.exit("Install pyperclip: pip install pyperclip")


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def inject(backend: PasteBackend, text: str, wid: str | None = None) -> tuple[bool, str]:
    """Inject *text* into the given window (or focused window if *wid* is None).

    ASCII  → typed character-by-character (works on any VM).
    Non-ASCII (Chinese, etc.) → clipboard paste (requires VM guest additions).

    For non-Xdotool backends with a *wid*, focus-switches to the target
    window temporarily.

    Returns (success, method_name).
    """
    backend.set_clipboard(text)

    # Focus-switching fallback for backends that can't target windows directly
    prev_wid: str | None = None
    if wid is not None and not isinstance(backend, XdotoolBackend):
        try:
            prev = get_active_window()
            if prev is not None:
                prev_wid = prev.wid
            subprocess.run(
                ["xdotool", "windowactivate", wid],
                timeout=1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(0.05)
        except Exception:
            pass

    backend.release_modifiers()
    time.sleep(0.03)

    if text.isascii():
        ok = backend.type_text(text, wid=wid)
        method = "keyboard-type"
    else:
        ok = backend.paste(wid=wid)
        method = "ctrl+shift+v"
        if not ok and backend.type_text(text, wid=wid):
            ok = True
            method = "ctrl+shift+v→keyboard"

    # Restore focus
    if prev_wid is not None:
        try:
            subprocess.run(
                ["xdotool", "windowactivate", prev_wid],
                timeout=1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    if not ok:
        if not text.isascii():
            print("Note: Chinese/non-ASCII requires clipboard sharing in the VM"
                  " (VirtualBox Guest Additions / SPICE agent / VMware Tools).",
                  file=sys.stderr)
        return False, method

    return True, method


# ---------------------------------------------------------------------------
# Multi-window mode (python3 clip2vm-daemon.py m)
# ---------------------------------------------------------------------------

def run_multi() -> None:
    """Interactive multi-window clipboard injection.

    Reads clipboard, asks for window title keywords, and injects into
    all matching windows.
    """
    from .window import get_all_visible_windows

    backend = detect_backend()
    text = read_clipboard()
    if not text.strip():
        print("Clipboard is empty.")
        return

    preview = text[:80].replace("\n", "↵")
    if len(text) > 80:
        preview += "…"
    print(f"Clipboard ({len(text)}c): \"{preview}\"")
    print()

    all_windows = get_all_visible_windows()
    if not all_windows:
        print("No visible windows found.")
        return

    def _match(windows: list, keywords: list[str]) -> list:
        if not keywords:
            return list(windows)
        kw_lower = [k.lower() for k in keywords]
        return [w for w in windows
                if all(k in w.title.lower() for k in kw_lower)]

    matched = list(all_windows)
    _print_window_list(matched)

    while True:
        try:
            line = input("Windows (keywords, or Enter to confirm)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not line:
            break

        keywords = line.split()
        matched = _match(all_windows, keywords)
        if not matched:
            print("  (no matching windows)")
        else:
            s = "s" if len(matched) != 1 else ""
            print(f"  ({len(matched)} window{s})")
            _print_window_list(matched)

    if not matched:
        print("No windows selected.")
        return

    s = "s" if len(matched) != 1 else ""
    print(f"\nSending to {len(matched)} window{s} ...")
    for w in matched:
        ok, method = inject(backend, text, wid=w.wid)
        status = "OK" if ok else "FAIL"
        title = w.title[:50]
        print(f"  [{status}] {w.wid} {title} ({method})")
        time.sleep(0.05)


def _print_window_list(windows: list) -> None:
    for i, w in enumerate(windows, 1):
        title = w.title[:80]
        print(f"  {i:>3}. [{w.wid}] {title}")


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------

def run_daemon() -> None:
    """Run the global-hotkey daemon.  Ctrl+Shift+Q → paste clipboard."""
    try:
        from pynput.keyboard import Key, KeyCode, Listener
    except ImportError:
        sys.exit("Install pynput: pip install pynput")

    import os
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    backend = detect_backend()

    print(f"Clip2VM daemon  |  session={session_type}"
          f"  |  backend={backend.__class__.__name__}")
    if session_type == "wayland":
        print("WARNING: pynput global hotkeys do NOT work on Wayland.")
    print("Ctrl+Shift+Q → paste clipboard into active window.  Ctrl+C to stop.")

    _held: dict[str, bool] = {"ctrl": False, "shift": False}

    def on_press(key):
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            _held["ctrl"] = True; return
        if key in (Key.shift, Key.shift_l, Key.shift_r):
            _held["shift"] = True; return
        if not (_held.get("ctrl") and _held.get("shift")):
            return
        if hasattr(key, "char") and key.char and key.char.lower() == "q":
            try:
                text = read_clipboard()
                if not text.strip():
                    print("Clipboard is empty.")
                    return
                ok, method = inject(backend, text)
                if ok:
                    now = datetime.now().strftime("%H:%M:%S")
                    active = get_active_window()
                    target = f" → {active.title}" if active else ""
                    preview = text[:80].replace("\n", "↵")
                    if len(text) > 80:
                        preview += "…"
                    print(f"[{now}] {method} {len(text)}c{target}")
                    print(f"  \"{preview}\"")
                else:
                    print("Injection failed.", file=sys.stderr)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

    def on_release(key):
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            _held["ctrl"] = False
        elif key in (Key.shift, Key.shift_l, Key.shift_r):
            _held["shift"] = False

    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
