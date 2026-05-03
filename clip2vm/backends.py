"""Paste backends for different display environments."""

import os
import subprocess
import sys
from abc import ABC, abstractmethod


class PasteBackend(ABC):
    """Abstract paste backend. Implementations handle the specifics of
    setting clipboard and simulating paste on different display servers."""

    @abstractmethod
    def set_clipboard(self, text: str) -> bool:
        """Place text into the system clipboard."""

    @abstractmethod
    def paste(self, wid: str | None = None) -> bool:
        """Simulate paste keyboard shortcut (Ctrl+V / Ctrl+Shift+V).

        If *wid* is given, target that window (X11 only).
        """

    @abstractmethod
    def type_text(self, text: str, wid: str | None = None) -> bool:
        """Simulate typing text character by character.

        If *wid* is given, target that window (X11 only).
        """

    def press_enter(self) -> bool:
        """Simulate pressing Enter."""
        return True

    def release_modifiers(self) -> None:
        """Release any held modifier keys (Ctrl, Shift, Alt, Super)."""
        pass


# ---------------------------------------------------------------------------
# X11 backend
# ---------------------------------------------------------------------------

class XdotoolBackend(PasteBackend):
    """X11 environments via xdotool + xclip."""

    def set_clipboard(self, text: str) -> bool:
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard", "-in", "-rmlastnl"],
                input=text.encode(), check=True, timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def paste(self, wid: str | None = None) -> bool:
        try:
            cmd = ["xdotool", "key", "--clearmodifiers"]
            if wid is not None:
                cmd.extend(["--window", wid])
            cmd.append("ctrl+shift+v")
            subprocess.run(cmd, check=True, timeout=1,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            try:
                cmd = ["xdotool", "key", "--clearmodifiers"]
                if wid is not None:
                    cmd.extend(["--window", wid])
                cmd.append("ctrl+v")
                subprocess.run(cmd, check=True, timeout=1,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                return False

    def type_text(self, text: str, wid: str | None = None) -> bool:
        try:
            cmd = ["xdotool", "type", "--delay", "3"]
            if wid is not None:
                cmd.extend(["--window", wid])
            cmd.extend(["--", text])
            subprocess.run(cmd, check=True, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def press_enter(self) -> bool:
        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "Return"],
                check=True, timeout=1,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def release_modifiers(self) -> None:
        subprocess.run(
            ["xdotool", "keyup", "ctrl", "shift", "alt", "super"],
            timeout=1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


# ---------------------------------------------------------------------------
# Wayland backends
# ---------------------------------------------------------------------------

class YdotoolBackend(PasteBackend):
    """Wayland via ydotool + wl-copy. Requires ydotool daemon running."""

    def set_clipboard(self, text: str) -> bool:
        try:
            subprocess.run(
                ["wl-copy"], input=text.encode(), check=True, timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def paste(self, wid: str | None = None) -> bool:
        # Ctrl+Shift+V = 29(ctrl) 42(shift) 47(v)
        try:
            subprocess.run(
                ["ydotool", "key", "29:1", "42:1", "47:1", "47:0", "42:0", "29:0"],
                check=True, timeout=1,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def type_text(self, text: str, wid: str | None = None) -> bool:
        try:
            subprocess.run(
                ["ydotool", "type", "--", text], check=True, timeout=30,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def press_enter(self) -> bool:
        try:
            subprocess.run(
                ["ydotool", "key", "28:1", "28:0"], check=True, timeout=1,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def release_modifiers(self) -> None:
        # ydotool: release ctrl(29) shift(42) alt(56) super(125)
        subprocess.run(
            ["ydotool", "key", "29:0", "42:0", "56:0", "125:0"],
            timeout=1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


class WtypeBackend(PasteBackend):
    """Minimal Wayland backend using wtype. No paste simulation — types directly."""

    def set_clipboard(self, text: str) -> bool:
        try:
            subprocess.run(
                ["wl-copy"], input=text.encode(), check=True, timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def paste(self, wid: str | None = None) -> bool:
        # wtype has no paste shortcut — fall back to typing
        return False

    def type_text(self, text: str, wid: str | None = None) -> bool:
        try:
            subprocess.run(
                ["wtype", "--", text], check=True, timeout=30,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def press_enter(self) -> bool:
        try:
            subprocess.run(["wtype", "-k", "Return"], check=True, timeout=1)
            return True
        except Exception:
            return False

    def release_modifiers(self) -> None:
        pass  # wtype has no equivalent; wayland compositor handles this


# ---------------------------------------------------------------------------
# Cross-platform fallback
# ---------------------------------------------------------------------------

class PyAutoGUIBackend(PasteBackend):
    """Cross-platform fallback using pyautogui + pyperclip."""

    def set_clipboard(self, text: str) -> bool:
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    def paste(self, wid: str | None = None) -> bool:
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "v")
            return True
        except Exception:
            return False

    def type_text(self, text: str, wid: str | None = None) -> bool:
        try:
            import pyautogui
            pyautogui.write(text, interval=0.002)
            return True
        except Exception:
            return False

    def press_enter(self) -> bool:
        try:
            import pyautogui
            pyautogui.press("enter")
            return True
        except Exception:
            return False

    def release_modifiers(self) -> None:
        pass  # pyautogui doesn't track modifier state


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _check_exe(*names: str) -> bool:
    """Return True if any of the named executables are on PATH."""
    for name in names:
        try:
            subprocess.run([name, "--version"], capture_output=True, timeout=2,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
        except Exception:
            return True  # ran but maybe --version not supported
    return False


def detect_backend() -> PasteBackend:
    """Auto-detect the best available paste backend for the current session."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()

    if session_type == "wayland":
        if _check_exe("ydotool"):
            return YdotoolBackend()
        if _check_exe("wtype"):
            return WtypeBackend()

    if session_type in ("x11", ""):
        if _check_exe("xdotool", "xclip"):
            return XdotoolBackend()

    # Final fallback
    try:
        import pyautogui  # noqa: F401
        return PyAutoGUIBackend()
    except ImportError:
        pass

    sys.exit(
        "No paste backend available.\n"
        "  X11:   sudo apt install xdotool xclip\n"
        "  Wayland: sudo apt install ydotool wl-clipboard\n"
        "  Cross:  pip install pyautogui pyperclip"
    )
