"""Finite-state machine: CAST -> WAITING_BITE -> REEL -> AFTER_CATCH -> STORE
-> (REPAIR) -> COOLDOWN -> CAST ..."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto

from .. import constants as C
from ..safety import (
    DEFAULT_CONFIRM_FRAMES,
    DEFAULT_MIN_CONFIDENCE,
    MIN_CONFIRM_FRAMES,
    ClickIntent,
    RepairDecision,
    RepairDialog,
    classify_repair_ui,
    same_evidence,
)


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
        if cfg.get("allow_paid_repair"):
            self.log("WARNING: allow_paid_repair is set but IGNORED - paid repairs are never "
                     "confirmed automatically. The bot will stop if a paid repair is required.")

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

    def act(self, x: float, y: float, mode: str, intent: ClickIntent = ClickIntent.GENERIC) -> None:
        self.inp.act(x, y, mode, intent=intent)
        if self.b["click_delay_ms"]:
            time.sleep(self.b["click_delay_ms"] / 1000)

    def click_det(self, det, intent: ClickIntent = ClickIntent.GENERIC) -> None:
        cx, cy = det.center
        self.inp.click(cx, cy, intent=intent, target=det.name)

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

    # ----------------------------------------------------------------- repair
    def _input_is_guarded(self) -> bool:
        return all(callable(getattr(self.inp, n, None)) for n in ("begin_repair_session", "end_repair_session"))

    def s_repair(self) -> State:
        """Free-repair flow. Paid / unknown / ambiguous dialogs are NEVER clicked.

        The input backend is put into a "repair session" in which it independently
        refuses paid confirmations, unlabeled clicks and confirm-type keypresses.
        """
        if not self._input_is_guarded():
            self.log("REPAIR refused: input backend does not enforce repair safety -> stopping bot")
            self.keys.stop()
            return State.COOLDOWN
        self.inp.begin_repair_session()
        try:
            return self._repair_flow()
        finally:
            self.inp.end_repair_session()

    def _confirm_decision(self, first: RepairDecision, min_conf: float):
        """Require the same clickable evidence on several consecutive fresh frames.

        The last frame is grabbed immediately before the click, so a dialog that
        changed in between (e.g. free -> paid) is caught. Returns the confirmed
        decision, a PAID decision if one appeared, or None if evidence disagreed.
        """
        frames = max(MIN_CONFIRM_FRAMES, int(self.cfg.get("repair_confirm_frames", DEFAULT_CONFIRM_FRAMES)))
        interval = self.cfg.get("repair_confirm_interval_ms", 150)
        cur = first
        for _ in range(frames - 1):
            if not self.sleep(interval):
                return None
            nxt = classify_repair_ui(self.ui(self.cap.grab(), C.REPAIR_CLASSES), min_conf)
            if nxt.state is RepairDialog.PAID:
                return nxt
            if not same_evidence(cur, nxt):
                return None
            cur = nxt
        return cur

    def _abort_paid_repair(self, dec: RepairDecision) -> State:
        # Deliberately no blind taps here: a paid dialog may be on screen.
        self.log(f"Paid repair detected ({dec.reason}) -> NOT confirming; stopping bot. "
                 "Handle the repair manually in-game.")
        self.keys.stop()
        return State.COOLDOWN

    def _repair_flow(self) -> State:
        gap = self.cfg["repair_click_gap_ms"]
        min_conf = float(self.cfg.get("repair_min_confidence", DEFAULT_MIN_CONFIDENCE))
        deadline = time.time() + self.cfg["repair_timeout_ms"] / 1000
        self.log("REPAIR: opening backpack")
        self.act(self.cfg["bag_x"], self.cfg["bag_y"], "tap", intent=ClickIntent.NAVIGATION)
        if not self.sleep(gap):
            return State.COOLDOWN
        tab_clicks = 0
        ambiguous_seen = False
        last_reason = ""
        while self.keys.alive() and time.time() < deadline:
            dec = classify_repair_ui(self.ui(self.cap.grab(), C.REPAIR_CLASSES), min_conf)

            if dec.state is RepairDialog.PAID:
                return self._abort_paid_repair(dec)

            if dec.state is RepairDialog.TAB and tab_clicks >= 3:
                dec = RepairDecision(RepairDialog.UNKNOWN, None, "tools tab did not open the rod list")

            if dec.state is RepairDialog.UNKNOWN:
                # Never click anything on an unrecognised / ambiguous screen. Wait for it to resolve.
                if dec.ambiguous:
                    ambiguous_seen = True
                if dec.reason != last_reason:
                    self.log(f"Repair dialog not actionable ({dec.reason}) -> not clicking")
                    last_reason = dec.reason
                if not self.sleep(gap):
                    break
                continue
            last_reason = ""

            if dec.state in (RepairDialog.FREE, RepairDialog.DONE):
                dec = self._confirm_decision(dec, min_conf)
                if dec is None:  # evidence flickered -> treat as ambiguous, re-evaluate
                    ambiguous_seen = True
                    if not self.sleep(gap):
                        break
                    continue
                if dec.state is RepairDialog.PAID:
                    return self._abort_paid_repair(dec)

            if dec.state is RepairDialog.DONE:
                self.click_det(dec.target, dec.intent)
                self.stats.repairs += 1
                self.log("Rod repaired | " + self.stats.line())
                self.sleep(gap)
                self._close_bag()
                return State.COOLDOWN

            if dec.state is RepairDialog.FREE:
                self.log("Clicking free repair")
                self.click_det(dec.target, dec.intent)
            elif dec.state is RepairDialog.TAB:
                self.log("Opening tools tab")
                self.click_det(dec.target, dec.intent)
                tab_clicks += 1
                self.sleep(gap)
                if self.cfg["rod_x"] and self.cfg["rod_y"]:
                    self.act(self.cfg["rod_x"], self.cfg["rod_y"], "tap", intent=ClickIntent.NAVIGATION)
            if not self.sleep(gap):
                break

        if ambiguous_seen and self.keys.alive():
            self.log("Repair timed out on an ambiguous dialog -> stopping bot without clicking")
            self.keys.stop()
            return State.COOLDOWN
        self.log("Repair timed out")
        self._close_bag()
        return State.COOLDOWN

    def _close_bag(self) -> None:
        if self.cfg["close_x"] and self.cfg["close_y"]:
            self.act(self.cfg["close_x"], self.cfg["close_y"], "tap", intent=ClickIntent.NAVIGATION)

    def s_cooldown(self) -> State:
        self.sleep(self.b["cooldown_after_bite_ms"])
        return State.CAST
