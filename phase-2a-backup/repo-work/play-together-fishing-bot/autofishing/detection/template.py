"""No-ML detector: OpenCV template matching + HSV fallback for the '!' mark.

Drop cropped screenshots named after the classes into templates/, e.g.
    templates/exclamation-mark.png
    templates/store-button.png
Create them easily with:   python main.py --snip store-button
"""
from __future__ import annotations

import glob
import os

import cv2
import numpy as np

from ..constants import BITE, norm
from .base import Det


class TemplateDetector:
    kind = "template"

    def __init__(self, folder: str, threshold: float = 0.8, min_area: int = 40, max_area: int = 6000,
                 scales=(0.9, 1.0, 1.1)):
        self.threshold = threshold
        self.min_area = min_area
        self.max_area = max_area
        self.scales = scales
        self.templates: dict[str, np.ndarray] = {}
        for p in glob.glob(os.path.join(folder, "*.png")):
            img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                self.templates[norm(os.path.splitext(os.path.basename(p))[0])] = img

    # --- HSV fallback for the red/orange exclamation mark ----------------
    def _hsv_bang(self, frame) -> list[Det]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        m1 = cv2.inRange(hsv, (0, 140, 150), (12, 255, 255))
        m2 = cv2.inRange(hsv, (170, 140, 150), (180, 255, 255))
        mask = cv2.morphologyEx(m1 | m2, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = []
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            area = cv2.contourArea(c)
            if self.min_area <= area <= self.max_area and 1.3 <= h / max(w, 1) <= 6:
                out.append(Det(BITE, 0.9, (x, y, x + w, y + h)))
        return out

    def detect(self, frame, conf: float = 0, imgsz: int = 0, only: set[str] | None = None) -> list[Det]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        out: list[Det] = []
        for name, tpl in self.templates.items():
            if only and name not in only:
                continue
            best = None
            for s in self.scales:
                t = tpl if s == 1 else cv2.resize(tpl, None, fx=s, fy=s)
                if t.shape[0] > gray.shape[0] or t.shape[1] > gray.shape[1]:
                    continue
                res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
                _, mx, _, loc = cv2.minMaxLoc(res)
                if mx >= self.threshold and (best is None or mx > best.conf):
                    best = Det(name, float(mx), (loc[0], loc[1], loc[0] + t.shape[1], loc[1] + t.shape[0]))
            if best:
                out.append(best)
        if BITE not in self.templates and (not only or BITE in only):
            out += self._hsv_bang(frame)
        return out
