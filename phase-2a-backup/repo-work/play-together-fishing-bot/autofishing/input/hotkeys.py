"""Global pause / stop hotkeys (Windows, via GetAsyncKeyState)."""
from __future__ import annotations

import ctypes
import sys
import time


def key_down(vk: int) -> bool:
    if sys.platform != "win32":
        return False
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


class Hotkeys:
    def __init__(self, cfg: dict):
        hk = cfg.get("hotkeys", {})
        self.pause_vk = int(hk.get("pause_vk", 0x77))  # F8
        self.stop_vk = int(hk.get("stop_vk", 0x79))  # F10
        self.paused = False
        self.stopped = False
        self._pause_prev = False

    def poll(self) -> None:
        now = key_down(self.pause_vk)
        if now and not self._pause_prev:
            self.paused = not self.paused
            print("[bot] PAUSED  (F8 to resume)" if self.paused else "[bot] RESUMED")
        self._pause_prev = now
        if key_down(self.stop_vk):
            self.stopped = True

    def alive(self) -> bool:
        """Call inside every loop. Blocks while paused. False once stopped."""
        self.poll()
        while self.paused and not self.stopped:
            time.sleep(0.1)
            self.poll()
        return not self.stopped

    def stop(self) -> None:
        self.stopped = True
