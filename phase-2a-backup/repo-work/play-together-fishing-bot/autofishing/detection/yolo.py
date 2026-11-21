"""YOLOv8 detector (ultralytics)."""
from __future__ import annotations

from ..constants import norm
from .base import Det


class YoloDetector:
    kind = "yolo"

    def __init__(self, path: str):
        from ultralytics import YOLO

        self.model = YOLO(path)
        self.names = {i: norm(n) for i, n in self.model.names.items()}
        # warm-up so the first real frame is not slow
        import numpy as np

        self.model.predict(np.zeros((64, 64, 3), np.uint8), verbose=False, imgsz=64)

    def detect(self, frame, conf: float, imgsz: int, only: set[str] | None = None) -> list[Det]:
        res = self.model.predict(frame, conf=conf, imgsz=imgsz, verbose=False)[0]
        out: list[Det] = []
        for b in res.boxes:
            name = self.names[int(b.cls[0])]
            if only and name not in only:
                continue
            x1, y1, x2, y2 = (float(v) for v in b.xyxy[0].tolist())
            out.append(Det(name, float(b.conf[0]), (x1, y1, x2, y2)))
        return out
