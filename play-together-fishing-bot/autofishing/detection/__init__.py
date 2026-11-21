from __future__ import annotations

import os

from .base import Det
from .template import TemplateDetector


def make_detector(cfg: dict, override: str | None = None):
    kind = override or cfg.get("detector", "auto")
    path = cfg["model"]["path"]
    has_model = os.path.exists(path)
    if kind == "yolo" or (kind == "auto" and has_model):
        if not has_model:
            raise FileNotFoundError(f"YOLO weights not found: {path}  (see README: Obtain YOLOv8 weights)")
        from .yolo import YoloDetector

        print(f"[detector] YOLOv8 -> {path}")
        return YoloDetector(path)
    t = cfg["template"]
    det = TemplateDetector(t["folder"], t["threshold"], t["hsv_bang_min_area"], t["hsv_bang_max_area"])
    print(f"[detector] OpenCV templates ({len(det.templates)} in '{t['folder']}/') + HSV '!' fallback")
    return det


__all__ = ["Det", "TemplateDetector", "make_detector"]
