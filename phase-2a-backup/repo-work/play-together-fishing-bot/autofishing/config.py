"""Config loading / saving (config.yaml)."""
from __future__ import annotations

import copy
import os
import sys
from typing import Any

import yaml

DEFAULTS: dict[str, Any] = {
    "backend": "window",
    "window_title": "",
    "detector": "auto",
    "input_backend": "pyautogui",
    "hotkeys": {"pause_vk": 0x77, "stop_vk": 0x79},
    "capture": {
        "image_width": 1600,
        "image_height": 900,
        "top": 50,
        "left": 850,
        "width": 500,
        "height": 400,
    },
    "model": {
        "path": "models/best.pt",
        "confidence": 0.40,
        "imgsz": 256,
        "bite_classes": ["exclamation-mark"],
    },
    "template": {
        "folder": "templates",
        "threshold": 0.80,
        "hsv_bang_min_area": 40,
        "hsv_bang_max_area": 6000,
    },
    "bot": {
        "poll_interval_ms": 0,
        "click_delay_ms": 0,
        "cast_delay_ms": 400,
        "after_catch_min_ms": 300,
        "after_catch_timeout_ms": 12000,
        "cooldown_after_bite_ms": 1200,
        "min_wait_before_bite_ms": 0,
        "bite_timeout_ms": 60000,
        "hold_ms": 300,
    },
    # SAFETY: paid repairs are never confirmed automatically. This flag is kept for
    # backwards compatibility only; setting it to true does NOT enable paid repair.
    "allow_paid_repair": False,
    "repair_timeout_ms": 25000,
    "repair_click_gap_ms": 700,
    # Free-repair evidence: minimum detector confidence, and number of consecutive
    # fresh frames (minimum 2) that must agree before a repair click is automated.
    "repair_min_confidence": 0.50,
    "repair_confirm_frames": 2,
    "repair_confirm_interval_ms": 150,
    "bag_x": 1537,
    "bag_y": 500,
    "rod_x": 0,
    "rod_y": 0,
    "close_x": 0,
    "close_y": 0,
    "ui_imgsz": 416,
    "ui_confidence": 0.35,
    "auto_cast": True,
    "cast_mode": "tap",
    "jerk_mode": "tap",
    "store_mode": "tap",
    "action_mode": "tap",
    "action_key": "space",
    "cast_x": 1268,
    "cast_y": 541,
    "reel_x": 1405,
    "reel_y": 695,
    "store_x": 1153,
    "store_y": 600,
    "adb_path": "adb",
    "adb_serial": "",
}


def _merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _read_raw(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(path: str = "config.yaml") -> dict:
    cfg = _merge(DEFAULTS, _read_raw(path))
    if cfg.get("allow_paid_repair"):
        print("[config] WARNING: allow_paid_repair is true but has NO effect - paid repairs are "
              "never confirmed automatically. The bot stops when a paid repair is required.",
              file=sys.stderr)
    return cfg


def save_values(updates: dict, path: str = "config.yaml") -> None:
    """Merge `updates` into the YAML file on disk (comments are not preserved)."""
    raw = _merge(_read_raw(path), updates)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(raw, f, sort_keys=False, allow_unicode=True)
