"""Detection class names used by the YOLOv8 model (and template file names)."""

BITE = "exclamation-mark"
STORE_BUTTON = "store-button"
TOO_LATE = "too-late-run-away"
TOOL_BROKEN = "tool-is-broken"
TOOL_TAB = "tool-tab"
REPAIR_BUTTON = "repair-button"
PAID_REPAIR_BUTTON = "paid-repair-button"
PAID_REPAIR_TEXT = "paid-repair-text"
REPAIR_DONE_BUTTON = "repair-done-button"
REPAIR_DONE_TEXT = "repair-done-text"

ALL_CLASSES = [
    BITE,
    STORE_BUTTON,
    TOO_LATE,
    TOOL_BROKEN,
    TOOL_TAB,
    REPAIR_BUTTON,
    PAID_REPAIR_BUTTON,
    PAID_REPAIR_TEXT,
    REPAIR_DONE_BUTTON,
    REPAIR_DONE_TEXT,
]

REPAIR_CLASSES = [
    TOOL_TAB,
    REPAIR_BUTTON,
    PAID_REPAIR_BUTTON,
    PAID_REPAIR_TEXT,
    REPAIR_DONE_BUTTON,
    REPAIR_DONE_TEXT,
]


def norm(name: str) -> str:
    """Normalise a class / file name: 'Store_Button' -> 'store-button'."""
    return name.strip().lower().replace("_", "-").replace(" ", "-")
