"""Shared fixtures. No emulator, OpenCV, PyAutoGUI or ADB is needed: the OS layer is faked,
but the real DesktopInput / AdbInput / FishingBot / safety code is what runs."""
from __future__ import annotations

import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from autofishing import constants as C  # noqa: E402
from autofishing.config import load_config  # noqa: E402
from autofishing.input import AdbInput, DesktopInput  # noqa: E402


def _load_det():
    """Load the tiny Det dataclass straight from its file: importing the `autofishing.detection`
    package would pull in OpenCV, which these tests deliberately do not need."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_det_base", os.path.join(ROOT, "autofishing", "detection", "base.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_det_base"] = mod  # dataclasses needs the module registered
    spec.loader.exec_module(mod)
    return mod.Det


Det = _load_det()


def det(name: str, conf: float = 0.9, cx: float = 100, cy: float = 100) -> Det:
    return Det(name, conf, (cx - 10, cy - 10, cx + 10, cy + 10))


# Distinct positions so we can tell exactly what was clicked.
POS = {
    "bag": (1537, 500),
    "close": (1600, 40),
    C.TOOL_TAB: (300, 120),
    C.REPAIR_BUTTON: (400, 500),
    C.PAID_REPAIR_BUTTON: (500, 600),
    C.PAID_REPAIR_TEXT: (500, 450),
    C.REPAIR_DONE_BUTTON: (700, 650),
    C.REPAIR_DONE_TEXT: (700, 640),
    C.STORE_BUTTON: (1153, 600),
    C.TOOL_BROKEN: (800, 300),
}


def d(name: str, conf: float = 0.9) -> Det:
    x, y = POS[name]
    return det(name, conf, x, y)


class FakeCap:
    """Replays a scripted list of 'screens'. Each screen is a list of Det. Last one repeats."""

    def __init__(self, script, cycle=False):
        self.script = list(script)
        self.cycle = cycle  # True: loop the script forever instead of repeating the last screen
        self.i = 0
        self.grabs = 0

    def grab(self):
        idx = self.i % len(self.script) if self.cycle else min(self.i, len(self.script) - 1)
        self.i += 1
        self.grabs += 1
        return idx

    def screen(self, idx):
        return self.script[idx]

    # used by the input backends
    def to_screen(self, x, y):
        return int(x), int(y)

    def cmd(self, *args):
        return ["adb", *args]


class FakeDetector:
    def __init__(self, cap: FakeCap):
        self.cap = cap

    def detect(self, frame, conf=0, imgsz=0, only=None):
        return [x for x in self.cap.screen(frame) if not only or x.name in only]


class FakeKeys:
    def __init__(self):
        self.stopped = False

    def alive(self):
        return not self.stopped

    def stop(self):
        self.stopped = True


class FakePyAutoGUI(types.ModuleType):
    """Stand-in for pyautogui / pydirectinput that records raw OS-level input."""

    def __init__(self):
        super().__init__("pyautogui")
        self.PAUSE = 0
        self.FAILSAFE = True
        self.pos = (0, 0)
        self.clicks = []   # (x, y) at mouseDown
        self.keys = []     # key names pressed

    def moveTo(self, x, y):
        self.pos = (x, y)

    def mouseDown(self):
        self.clicks.append(self.pos)

    def mouseUp(self):
        pass

    def keyDown(self, k):
        self.keys.append(k)

    def keyUp(self, k):
        pass


class Backend:
    """Uniform view over both input backends: .inp, .clicks (screen coords), .keys."""

    def __init__(self, inp, get_clicks, get_keys):
        self.inp = inp
        self._get_clicks, self._get_keys = get_clicks, get_keys

    @property
    def clicks(self):
        return list(self._get_clicks())

    @property
    def keys(self):
        return list(self._get_keys())


def make_cfg(**over):
    cfg = load_config("does-not-exist.yaml")  # pure defaults
    cfg["repair_click_gap_ms"] = 0
    cfg["repair_confirm_interval_ms"] = 0
    cfg["repair_timeout_ms"] = 400
    cfg["bot"]["cooldown_after_bite_ms"] = 0
    cfg.update(over)
    return cfg


@pytest.fixture(params=["desktop", "adb"])
def backend(request, monkeypatch):
    cfg = make_cfg()
    cap = FakeCap([[]])
    if request.param == "desktop":
        fake = FakePyAutoGUI()
        monkeypatch.setitem(sys.modules, "pyautogui", fake)
        inp = DesktopInput(cfg, cap)
        return Backend(inp, lambda: fake.clicks, lambda: fake.keys)

    calls = []

    def fake_run(argv, **kw):
        calls.append(argv)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr("autofishing.input.controller.subprocess.run", fake_run)
    inp = AdbInput(cfg, cap)

    def adb_clicks():
        out = []
        for a in calls:
            if "tap" in a:
                out.append((int(a[-2]), int(a[-1])))
            elif "swipe" in a:
                out.append((int(a[-5]), int(a[-4])))
        return out

    return Backend(inp, adb_clicks, lambda: [a[-1] for a in calls if "keyevent" in a])


def build_bot(script, backend, cycle=False, **cfg_over):
    from autofishing.bot import FishingBot

    cap = FakeCap(script, cycle=cycle)
    keys = FakeKeys()
    cfg = make_cfg(**cfg_over)
    backend.inp.cfg = cfg
    backend.inp.cap = cap
    bot = FishingBot(cfg, cap, backend.inp, FakeDetector(cap), keys)
    bot.log = lambda msg: bot.logs.append(msg)
    bot.logs = []
    return bot, keys
