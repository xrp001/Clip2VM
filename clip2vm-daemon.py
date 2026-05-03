#!/usr/bin/env python3
"""Clip2VM — Ctrl+Shift+Q to paste clipboard into the active VM window.

Usage:
  python3 clip2vm-daemon.py      # daemon mode (hotkey listener)
  python3 clip2vm-daemon.py m    # multi-window interactive mode
"""

import sys

if not getattr(sys, "frozen", False):
    # Running from source — ensure clip2vm/ is importable
    from pathlib import Path
    _PROJECT = Path(__file__).resolve().parent
    if str(_PROJECT) not in sys.path:
        sys.path.insert(0, str(_PROJECT))

from clip2vm.client import run_daemon, run_multi

if len(sys.argv) > 1 and sys.argv[1] == "m":
    run_multi()
else:
    run_daemon()
