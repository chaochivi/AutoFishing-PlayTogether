"""Paid-repair safety layer (Phase 2A).

Two independent lines of defence live here, deliberately free of heavy
dependencies (no cv2 / pyautogui / numpy) so they can be unit-tested anywhere:

1. ``classify_repair_ui``  - decides what a repair dialog *is* from detections.
   Anything that is not positively identified as a free repair step is
   PAID or UNKNOWN and must never be clicked.

2. ``RepairGuardMixin``    - mixed into ``DesktopInput`` and ``AdbInput``.
   Even if the bot logic is wrong (or a config value is flipped), the input
   layer itself refuses to deliver a paid-repair confirmation, refuses
   unlabeled clicks / confirm-type keypresses while a repair session is
   active, and refuses to click on a detection that is a paid-repair class.

``allow_paid_repair`` is intentionally NOT consulted anywhere in this module:
automatic paid-repair confirmation is not a supported operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from . import constants as C

# --------------------------------------------------------------------------
# Policy constants
# --------------------------------------------------------------------------

#: Detection classes that indicate a paid repair. Seeing ANY of these (at any
#: confidence) means the dialog is treated as paid.
PAID_CLASSES = frozenset({C.PAID_REPAIR_BUTTON, C.PAID_REPAIR_TEXT})

#: Keys that may be sent while a repair session is active. They only cancel /
#: go back; they can never confirm a purchase. Space / Enter are excluded.
SAFE_REPAIR_KEYS = frozenset({"esc", "escape", "back"})

#: Minimum number of consecutive agreeing frames before a click is automated.
MIN_CONFIRM_FRAMES = 2

DEFAULT_MIN_CONFIDENCE = 0.50
DEFAULT_CONFIRM_FRAMES = 2


class RepairDialog(Enum):
    """What the current screen is, as far as the detector can prove."""

    PAID = auto()      # paid-repair evidence present            -> never click
    DONE = auto()      # positive evidence repair finished       -> may dismiss
    FREE = auto()      # positive evidence of a free repair step -> may click
    TAB = auto()       # tools-tab navigation                    -> may click
    UNKNOWN = auto()   # nothing / ambiguous / low confidence    -> never click


class ClickIntent(Enum):
    """Why the bot is clicking. Declared by the caller, enforced by the input layer."""

    GENERIC = auto()              # ordinary gameplay click (cast / reel / store)
    NAVIGATION = auto()           # fixed-coordinate bag / rod / close taps
    TOOLS_TAB = auto()
    FREE_REPAIR = auto()
    REPAIR_DONE = auto()
    PAID_REPAIR_CONFIRM = auto()  # ALWAYS refused
    UNKNOWN_DIALOG = auto()       # ALWAYS refused


#: Intents refused unconditionally, whatever the config says.
ALWAYS_BLOCKED_INTENTS = frozenset({ClickIntent.PAID_REPAIR_CONFIRM, ClickIntent.UNKNOWN_DIALOG})


class PaidRepairBlocked(RuntimeError):
    """Raised by the input layer when an action violates the repair-safety policy."""


def paid_repair_allowed(cfg: Optional[dict] = None) -> bool:
    """Whether automatic paid-repair confirmation is permitted. Always False.

    ``cfg`` is accepted (and ignored) so call sites read naturally and so a
    test can prove that ``allow_paid_repair: true`` changes nothing.
    """
    return False


# --------------------------------------------------------------------------
# Dialog classification
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RepairDecision:
    state: RepairDialog
    target: object = None  # a Det (has .name / .conf / .center) or None
    reason: str = ""
    ambiguous: bool = False  # UNKNOWN because evidence existed but was weak / conflicting

    @property
    def clickable(self) -> bool:
        return self.state in (RepairDialog.FREE, RepairDialog.DONE, RepairDialog.TAB)

    @property
    def intent(self) -> ClickIntent:
        return {
            RepairDialog.FREE: ClickIntent.FREE_REPAIR,
            RepairDialog.DONE: ClickIntent.REPAIR_DONE,
            RepairDialog.TAB: ClickIntent.TOOLS_TAB,
            RepairDialog.PAID: ClickIntent.PAID_REPAIR_CONFIRM,
        }.get(self.state, ClickIntent.UNKNOWN_DIALOG)


def _best(ui: dict, *names: str):
    cands = [ui[n] for n in names if n in ui]
    return max(cands, key=lambda d: d.conf) if cands else None


def classify_repair_ui(ui: dict, min_conf: float = DEFAULT_MIN_CONFIDENCE) -> RepairDecision:
    """Classify detections (``{class_name: Det}``) into a :class:`RepairDecision`.

    Precedence is fail-safe: PAID beats everything; a free action needs
    positive, sufficiently confident evidence; everything else is UNKNOWN.
    """
    # 1. Any paid evidence, at any confidence, blocks the dialog outright.
    paid = _best(ui, *sorted(PAID_CLASSES))
    if paid is not None:
        return RepairDecision(RepairDialog.PAID, paid, f"paid evidence: {paid.name} ({paid.conf:.2f})")

    # 2. Repair finished: dismissing it is harmless, but still needs evidence.
    done = _best(ui, C.REPAIR_DONE_BUTTON, C.REPAIR_DONE_TEXT)
    if done is not None:
        if done.conf >= min_conf:
            return RepairDecision(RepairDialog.DONE, done, f"repair-done evidence ({done.conf:.2f})")
        return RepairDecision(RepairDialog.UNKNOWN, None,
                              f"repair-done below confidence {min_conf:.2f} ({done.conf:.2f})", True)

    # 3. A generic repair button is NOT proof that repair is free.
    # The detector must gain a dedicated, positively trained FREE_REPAIR class
    # (or equivalent independent evidence) before automated repair can be enabled.
    rep = ui.get(C.REPAIR_BUTTON)
    if rep is not None:
        return RepairDecision(
            RepairDialog.UNKNOWN, None,
            "generic repair-button is not proof of free repair; refusing to click", True
        )

    # 4. Navigation to the tools tab is harmless only when no repair control
    # is simultaneously visible.
    tab = ui.get(C.TOOL_TAB)
    if tab is not None:
        return RepairDecision(RepairDialog.TAB, tab, "tools tab visible")

    return RepairDecision(RepairDialog.UNKNOWN, None, "no recognised repair dialog")


def same_evidence(a: RepairDecision, b: RepairDecision, tol_px: float = 30.0) -> bool:
    """True if two decisions are the same clickable state on (nearly) the same spot."""
    if a.state != b.state or not a.clickable or a.target is None or b.target is None:
        return False
    if a.target.name != b.target.name:
        return False
    (ax, ay), (bx, by) = a.target.center, b.target.center
    return abs(ax - bx) <= tol_px and abs(ay - by) <= tol_px


# --------------------------------------------------------------------------
# Input-layer enforcement
# --------------------------------------------------------------------------


def check_click(intent: ClickIntent, in_repair_session: bool, target: Optional[str] = None) -> None:
    """Raise :class:`PaidRepairBlocked` if a click violates policy."""
    if intent in ALWAYS_BLOCKED_INTENTS:
        raise PaidRepairBlocked(f"click blocked: intent {intent.name} is never permitted")
    if target is not None and target in PAID_CLASSES:
        raise PaidRepairBlocked(f"click blocked: target '{target}' is a paid-repair control")
    if in_repair_session and intent is ClickIntent.GENERIC:
        raise PaidRepairBlocked("click blocked: unlabeled click during repair session")


def check_key(key: str, in_repair_session: bool) -> None:
    """Raise :class:`PaidRepairBlocked` if a keypress could confirm a dialog."""
    if in_repair_session and str(key).lower() not in SAFE_REPAIR_KEYS:
        raise PaidRepairBlocked(f"key '{key}' blocked during repair session (could confirm a dialog)")


class RepairGuardMixin:
    """Shared by ``DesktopInput`` and ``AdbInput`` so both enforce identical rules."""

    _repair_depth: int = 0
    blocked_actions: int = 0

    def begin_repair_session(self) -> None:
        self._repair_depth += 1

    def end_repair_session(self) -> None:
        self._repair_depth = max(0, self._repair_depth - 1)

    @property
    def in_repair_session(self) -> bool:
        return self._repair_depth > 0

    def _guard_click(self, intent: ClickIntent, target: Optional[str]) -> None:
        try:
            check_click(intent, self.in_repair_session, target)
        except PaidRepairBlocked:
            self.blocked_actions += 1
            raise

    def _guard_key(self, key: str) -> None:
        try:
            check_key(key, self.in_repair_session)
        except PaidRepairBlocked:
            self.blocked_actions += 1
            raise
