"""MSS-based window / screen capture + ADB screencap backend."""
from __future__ import annotations

import ctypes
import subprocess
import sys
import time

import cv2
import numpy as np


def enable_dpi_awareness() -> None:
    """Make sure mouse + capture coordinates are physical pixels (Windows)."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def find_client_rect(title: str):
    """Return (left, top, width, height) of the largest visible window whose
    title contains `title` (client area only, no borders)."""
    import win32gui  # type: ignore

    matches = []

    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and title.lower() in win32gui.GetWindowText(hwnd).lower():
            l, t, r, b = win32gui.GetClientRect(hwnd)
            if r - l > 200 and b - t > 200:
                x, y = win32gui.ClientToScreen(hwnd, (0, 0))
                matches.append((x, y, r - l, b - t))

    win32gui.EnumWindows(cb, None)
    return max(matches, key=lambda m: m[2] * m[3]) if matches else None


class WindowCapture:
    """Grabs the game window and rescales it to image_width x image_height so
    every coordinate in config.yaml is resolution independent."""

    def __init__(self, cfg: dict):
        import mss

        self.title = cfg.get("window_title") or ""
        cap = cfg["capture"]
        self.iw, self.ih = int(cap["image_width"]), int(cap["image_height"])
        self.sct = mss.mss()
        self.rect = None
        self._last = 0.0
        self._warned = False
        self._refresh(force=True)

    def _refresh(self, force: bool = False) -> None:
        if not force and time.time() - self._last < 1.5:
            return
        self._last = time.time()
        rect = None
        if self.title and sys.platform == "win32":
            try:
                rect = find_client_rect(self.title)
            except Exception:
                rect = None
            if rect is None and not self._warned:
                print(f"[capture] window '{self.title}' not found - using full screen")
                self._warned = True
        if rect is None:
            m = self.sct.monitors[1]
            rect = (m["left"], m["top"], m["width"], m["height"])
        self.rect = rect

    def grab(self) -> np.ndarray:
        self._refresh()
        l, t, w, h = self.rect
        shot = self.sct.grab({"left": l, "top": t, "width": w, "height": h})
        img = np.ascontiguousarray(np.asarray(shot)[:, :, :3])  # BGRA -> BGR
        if (w, h) != (self.iw, self.ih):
            img = cv2.resize(img, (self.iw, self.ih), interpolation=cv2.INTER_AREA)
        return img

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        l, t, w, h = self.rect
        return int(l + x * w / self.iw), int(t + y * h / self.ih)

    def from_screen(self, sx: float, sy: float) -> tuple[int, int]:
        l, t, w, h = self.rect
        return int((sx - l) * self.iw / w), int((sy - t) * self.ih / h)


class AdbCapture:
    """Android screenshots through ADB (slower, but works with hidden windows)."""

    def __init__(self, cfg: dict):
        self.adb = cfg.get("adb_path") or "adb"
        self.serial = cfg.get("adb_serial") or ""
        cap = cfg["capture"]
        self.iw, self.ih = int(cap["image_width"]), int(cap["image_height"])
        self.dw, self.dh = self.iw, self.ih
        self.grab()

    def cmd(self, *args: str) -> list[str]:
        base = [self.adb]
        if self.serial:
            base += ["-s", self.serial]
        return base + list(args)

    def grab(self) -> np.ndarray:
        out = subprocess.run(self.cmd("exec-out", "screencap", "-p"), capture_output=True, check=True).stdout
        img = cv2.imdecode(np.frombuffer(out, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError("ADB screencap failed - is the device connected? (adb devices)")
        self.dh, self.dw = img.shape[:2]
        if (self.dw, self.dh) != (self.iw, self.ih):
            img = cv2.resize(img, (self.iw, self.ih), interpolation=cv2.INTER_AREA)
        return img

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        return int(x * self.dw / self.iw), int(y * self.dh / self.ih)

    def from_screen(self, sx: float, sy: float) -> tuple[int, int]:
        return int(sx * self.iw / self.dw), int(sy * self.ih / self.dh)


def make_capture(cfg: dict):
    enable_dpi_awareness()
    if cfg.get("backend") == "adb":
        return AdbCapture(cfg)
    if cfg.get("backend") == "screen":
        cfg = {**cfg, "window_title": ""}
    return WindowCapture(cfg)
