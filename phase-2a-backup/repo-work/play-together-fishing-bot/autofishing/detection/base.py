from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Det:
    name: str
    conf: float
    box: tuple[float, float, float, float]  # x1, y1, x2, y2

    @property
    def center(self) -> tuple[float, float]:
        return (self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2
