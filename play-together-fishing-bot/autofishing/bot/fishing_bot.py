"""Finite-state machine: CAST -> WAITING_BITE -> REEL -> AFTER_CATCH -> STORE
-> (REPAIR) -> COOLDOWN -> CAST ..."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto

from .. import constants as C


class State(Enum):
    CAST = auto()
    WAITING_BITE = auto()
    AFTER_CATCH = auto()
    REPAIR = auto()
    COOLDOWN = auto()


@dataclass
class Stats:
    started: float = field(default_factory=time.time)
    casts: int = 0
    bites: int = 0
    catches: int = 0
    missed: int = 0
    repairs: int = 0

    def line(self) -> str:
        m = int((time.time() - self.started) // 60)
        return (f"casts={self.casts} bites={self.bites} stored={self.catches} "
                f"missed={self.missed} repairs={self.repairs} runtime={m}m")


class FishingBot:
    def __init__(self, cfg: dict, cap, inp, det, keys):
        self.cfg, self.cap, self.inp, self.det, self.keys = cfg, cap, inp, det, keys
        self.b = cfg["bot"]
        self.stats = Stats()
        self.bite_classes = set(cfg["model"]["bite_classes"])
        c = cfg["capture"]
        self.roi = (int(c["left"]), int(c["top"]), int(c["width"]), int(c["height"]))

    # ------------------------------------------------------------------ utils
    def log(self, msg: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def sleep(self, ms: float) -> bool:
        """Interruptible sleep. Returns False if the bot was stopped."""
        end = time.time() + ms / 1000
        while time.time() < end:
            if not self.keys.alive():
                return False
            time.sleep(min(0.05, max(0, end - time.time())))
        return self.keys.alive()

    def act(self, x: float, y: float, mode: str) -> None:
        self.inp.act(x, y, mode)
        if self.b["click_delay_ms"]:
            time.sleep(self.b["click_delay_ms"] / 1000)

    def click_det(self, det) -> None:
        cx, cy = det.center
        self.inp.click(cx, cy)

    def roi_crop(self, frame):
        l, t, w, h = self.roi
        return frame[t:t + h, l:l + w]

    def bite_seen(self, frame) -> bool:
        ds = self.det.detect(self.roi_crop(frame), self.cfg["model"]["confidence"],
                             self.cfg["model"]["imgsz"], only=self.bite_classes)
        return any(d.name in self.bite_classes for d in ds)

    def ui(self, frame, names) -> dict:
        names = set(names)
        best: dict = {}
        for d in self.det.detect(frame, self.cfg["ui_confidence"], self.cfg["ui_imgsz"], only=names):
            if d.name in names and (d.name not in best or d.conf > best[d.name].conf):
                best[d.name] = d
        return best

    # ------------------------------------------------------------------- loop
    def run(self) -> None:
        self.log("Bot started.  F8 = pause/resume   F10 = stop   (mouse to a screen corner = emergency abort)")
        handlers = {
            State.CAST: self.s_cast,
            State.WAITING_BITE: self.s_wait,
            State.AFTER_CATCH: self.s_after_catch,
            State.REPAIR: self.s_repair,
            State.COOLDOWN: self.s_cooldown,
        }
        state = State.CAST
        while self.keys.alive():
            state = handlers[state]()
        self.log("Stopped. " + self.stats.line())

    # ----------------------------------------------------------------- states
    def s_cast(self) -> State:
        if self.cfg["auto_cast"]:
            self.act(self.cfg["cast_x"], self.cfg["cast_y"], self.cfg["cast_mode"])
            self.stats.casts += 1
            self.log(f"CAST #{self.stats.casts}")
        self.sleep(self.b["cast_delay_ms"])
        return State.WAITING_BITE

    def s_wait(self) -> State:
        t0 = last_ui = time.time()
        while self.keys.alive():
            frame = self.cap.grab()
            now = time.time()
            elapsed = (now - t0) * 1000

            if elapsed >= self.b["min_wait_before_bite_ms"] and self.bite_seen(frame):
                self.stats.bites += 1
                self.log(f"BITE! ({elapsed / 1000:.1f}s) -> reel")
                self.act(self.cfg["reel_x"], self.cfg["reel_y"], self.cfg["jerk_mode"])
                return State.AFTER_CATCH

            if now - last_ui > 0.5:  # cheaper UI checks every 500 ms
                last_ui = now
                ui = self.ui(frame, [C.TOOL_BROKEN, C.TOO_LATE, C.STORE_BUTTON])
                if C.TOOL_BROKEN in ui:
                    self.log("Rod is broken -> REPAIR")
                    return State.REPAIR
                if C.TOO_LATE in ui:
                    self.stats.missed += 1
                    self.log("Too late, fish ran away")
                    return State.COOLDOWN
                if C.STORE_BUTTON in ui:
                    return State.AFTER_CATCH

            if elapsed > self.b["bite_timeout_ms"]:
                self.log("No bite for a long time -> recast")
                return State.COOLDOWN

            if self.b["poll_interval_ms"]:
                time.sleep(self.b["poll_interval_ms"] / 1000)
        return State.WAITING_BITE

    def s_after_catch(self) -> State:
        t0 = time.time()
        timeout = self.b["after_catch_timeout_ms"] / 1000
        min_wait = self.b["after_catch_min_ms"] / 1000
        while self.keys.alive() and time.time() - t0 < timeout:
            frame = self.cap.grab()
            ui = self.ui(frame, [C.STORE_BUTTON, C.TOO_LATE, C.TOOL_BROKEN])
            if C.STORE_BUTTON in ui and time.time() - t0 >= min_wait:
                if self.cfg["store_x"] and self.cfg["store_y"]:
                    self.act(self.cfg["store_x"], self.cfg["store_y"], self.cfg["store_mode"])
                else:
                    self.click_det(ui[C.STORE_BUTTON])
                self.stats.catches += 1
                self.log("STORED catch  | " + self.stats.line())
                return State.COOLDOWN
            if C.TOO_LATE in ui:
                self.stats.missed += 1
                self.log("Missed catch")
                return State.COOLDOWN
            if C.TOOL_BROKEN in ui:
                self.log("Rod is broken -> REPAIR")
                return State.REPAIR
            time.sleep(0.05)
        self.log("After-catch timeout")
        return State.COOLDOWN

    def s_repair(self) -> State:
        gap = self.cfg["repair_click_gap_ms"]
        deadline = time.time() + self.cfg["repair_timeout_ms"] / 1000
        self.log("REPAIR: opening backpack")
        self.act(self.cfg["bag_x"], self.cfg["bag_y"], "tap")
        if not self.sleep(gap):
            return State.COOLDOWN
        tab_clicks = 0
        idle = 0
        while self.keys.alive() and time.time() < deadline:
            ui = self.ui(self.cap.grab(), C.REPAIR_CLASSES)

            if C.REPAIR_DONE_BUTTON in ui or C.REPAIR_DONE_TEXT in ui:
                self.click_det(ui.get(C.REPAIR_DONE_BUTTON) or ui[C.REPAIR_DONE_TEXT])
                self.stats.repairs += 1
                self.log("Rod repaired | " + self.stats.line())
                self.sleep(gap)
                self._close_bag()
                return State.COOLDOWN

            if C.PAID_REPAIR_BUTTON in ui or C.PAID_REPAIR_TEXT in ui:
                if not self.cfg["allow_paid_repair"]:
                    self.log("Paid repair required but allow_paid_repair=false -> stopping bot")
                    self._close_bag()
                    self.keys.stop()
                    return State.COOLDOWN
                if C.PAID_REPAIR_BUTTON in ui:
                    self.log("Confirming paid repair")
                    self.click_det(ui[C.PAID_REPAIR_BUTTON])
                    idle = 0
            elif C.REPAIR_BUTTON in ui:
                self.log("Clicking repair")
                self.click_det(ui[C.REPAIR_BUTTON])
                idle = 0
            elif C.TOOL_TAB in ui and tab_clicks < 3:
                self.log("Opening tools tab")
                self.click_det(ui[C.TOOL_TAB])
                tab_clicks += 1
                self.sleep(gap)
                if self.cfg["rod_x"] and self.cfg["rod_y"]:
                    self.act(self.cfg["rod_x"], self.cfg["rod_y"], "tap")
                idle = 0
            else:
                idle += 1
                if idle % 6 == 0:  # backpack probably didn't open
                    self.act(self.cfg["bag_x"], self.cfg["bag_y"], "tap")
            if not self.sleep(gap):
                break
        self.log("Repair timed out")
        self._close_bag()
        return State.COOLDOWN

    def _close_bag(self) -> None:
        if self.cfg["close_x"] and self.cfg["close_y"]:
            self.act(self.cfg["close_x"], self.cfg["close_y"], "tap")

    def s_cooldown(self) -> State:
        self.sleep(self.b["cooldown_after_bite_ms"])
        return State.CAST
