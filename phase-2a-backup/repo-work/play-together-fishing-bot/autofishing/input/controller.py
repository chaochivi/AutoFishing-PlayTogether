"""Mouse / keyboard output: PyAutoGUI, PyDirectInput or ADB.

Both backends share ``RepairGuardMixin`` (see ``autofishing/safety.py``), so the
paid-repair restrictions are enforced identically on desktop and ADB, and
independently of the bot logic and of ``allow_paid_repair``.
"""
from __future__ import annotations

import subprocess
import time
from typing import Optional

from ..safety import ClickIntent, RepairGuardMixin

ADB_KEYCODES = {"space": 62, "enter": 66, "esc": 111, "escape": 111, "back": 4}


class DesktopInput(RepairGuardMixin):
    def __init__(self, cfg: dict, cap):
        self.cfg = cfg
        self.cap = cap
        if cfg.get("input_backend") == "pydirectinput":
            import pydirectinput as d  # type: ignore

            d.PAUSE = 0
        else:
            import pyautogui as d  # type: ignore

            d.PAUSE = 0
            d.FAILSAFE = True  # slam mouse to a screen corner to abort
        self.d = d

    def click(self, x: float, y: float, hold_ms: int = 40, *,
              intent: ClickIntent = ClickIntent.GENERIC, target: Optional[str] = None) -> None:
        self._guard_click(intent, target)  # raises PaidRepairBlocked before any OS input
        sx, sy = self.cap.to_screen(x, y)
        self.d.moveTo(sx, sy)
        time.sleep(0.03)
        self.d.mouseDown()
        time.sleep(hold_ms / 1000)
        self.d.mouseUp()

    def key(self, key: str, hold_ms: int = 50) -> None:
        self._guard_key(key)
        self.d.keyDown(key)
        time.sleep(hold_ms / 1000)
        self.d.keyUp(key)

    def act(self, x: float, y: float, mode: str, *, intent: ClickIntent = ClickIntent.GENERIC) -> None:
        self._guard_click(intent, None)
        hold = int(self.cfg["bot"].get("hold_ms", 300))
        if mode == "key":
            self.key(self.cfg.get("action_key", "space"))
        elif mode == "hold":
            self.click(x, y, hold_ms=hold, intent=intent)
        else:
            self.click(x, y, intent=intent)

    def escape(self) -> None:
        self.key("esc")


class AdbInput(RepairGuardMixin):
    def __init__(self, cfg: dict, cap):
        self.cfg = cfg
        self.cap = cap

    def _run(self, *args: str) -> None:
        subprocess.run(self.cap.cmd("shell", "input", *args), check=False, capture_output=True)

    def click(self, x: float, y: float, hold_ms: int = 40, *,
              intent: ClickIntent = ClickIntent.GENERIC, target: Optional[str] = None) -> None:
        self._guard_click(intent, target)  # raises PaidRepairBlocked before any adb call
        sx, sy = self.cap.to_screen(x, y)
        if hold_ms > 100:
            self._run("swipe", str(sx), str(sy), str(sx), str(sy), str(hold_ms))
        else:
            self._run("tap", str(sx), str(sy))

    def key(self, key: str, hold_ms: int = 50) -> None:
        self._guard_key(key)
        self._run("keyevent", str(ADB_KEYCODES.get(key.lower(), 62)))

    def act(self, x: float, y: float, mode: str, *, intent: ClickIntent = ClickIntent.GENERIC) -> None:
        self._guard_click(intent, None)
        hold = int(self.cfg["bot"].get("hold_ms", 300))
        if mode == "key":
            self.key(self.cfg.get("action_key", "space"))
        elif mode == "hold":
            self.click(x, y, hold_ms=hold, intent=intent)
        else:
            self.click(x, y, intent=intent)

    def escape(self) -> None:
        self.key("esc")


def make_input(cfg: dict, cap):
    if cfg.get("backend") == "adb":
        return AdbInput(cfg, cap)
    return DesktopInput(cfg, cap)
