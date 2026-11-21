"""Calibration / debugging tools: --pick, --preview, --test, --snip."""
from __future__ import annotations

import os
import time

import cv2

from .. import constants as C
from ..config import save_values
from ..input.hotkeys import key_down

VK_F6, VK_F7 = 0x75, 0x76


def _mouse_pos():
    import pyautogui

    p = pyautogui.position()
    return p.x, p.y


def _wait_point(label: str, allow_skip: bool = False):
    """Hover the mouse over `label` and press F7 (F6 to skip)."""
    hint = "F7 = record" + (", F6 = skip" if allow_skip else "")
    print(f"  -> hover over {label} and press {hint}")
    try:
        import sys

        if sys.platform != "win32":
            raise RuntimeError
        while key_down(VK_F7) or key_down(VK_F6):
            time.sleep(0.05)
        while True:
            if key_down(VK_F7):
                return _mouse_pos()
            if allow_skip and key_down(VK_F6):
                return None
            time.sleep(0.02)
    except RuntimeError:
        s = input("     (non-Windows) place mouse, press Enter" + (" or type 's' to skip: " if allow_skip else ": "))
        if allow_skip and s.strip().lower() == "s":
            return None
        return _mouse_pos()


def pick(cfg, cap, config_path: str) -> None:
    print("\n=== Coordinate calibration ===")
    print("Make sure the game window is visible and you are standing at a fishing spot.\n")
    cap.grab()  # refresh window rect
    updates: dict = {}

    points = [
        ("cast", "the CAST / fishing button", False),
        ("reel", "the REEL / JERK button", False),
        ("store", "the STORE button (after catching a fish)", False),
        ("bag", "the BACKPACK icon", False),
        ("rod", "the first ROD slot in the Tools tab (optional)", True),
        ("close", "the CLOSE-backpack button (optional)", True),
    ]
    for key, label, skip in points:
        p = _wait_point(label, skip)
        cap.grab()
        if p is None:
            updates[f"{key}_x"], updates[f"{key}_y"] = 0, 0
            print("     skipped")
            continue
        x, y = cap.from_screen(*p)
        updates[f"{key}_x"], updates[f"{key}_y"] = x, y
        print(f"     {key}: ({x}, {y})")

    print("\nBite region (where the '!' appears above your character):")
    a = _wait_point("the TOP-LEFT corner of the bite region")
    b = _wait_point("the BOTTOM-RIGHT corner of the bite region")
    ax, ay = cap.from_screen(*a)
    bx, by = cap.from_screen(*b)
    updates["capture"] = {
        "left": min(ax, bx),
        "top": min(ay, by),
        "width": abs(bx - ax),
        "height": abs(by - ay),
    }
    print(f"     ROI: {updates['capture']}")
    save_values(updates, config_path)
    print(f"\nSaved to {config_path}. Run `python main.py --preview` to verify.")


def _draw(frame, cfg, det):
    c = cfg["capture"]
    l, t, w, h = c["left"], c["top"], c["width"], c["height"]
    cv2.rectangle(frame, (l, t), (l + w, t + h), (0, 255, 0), 2)
    cv2.putText(frame, "bite ROI", (l, max(15, t - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    found = []
    roi = frame[t:t + h, l:l + w].copy()
    for d in det.detect(roi, cfg["model"]["confidence"], cfg["model"]["imgsz"], only=set(cfg["model"]["bite_classes"])):
        x1, y1, x2, y2 = d.box
        found.append((d.name, d.conf, (x1 + l, y1 + t, x2 + l, y2 + t)))
    for d in det.detect(frame, cfg["ui_confidence"], cfg["ui_imgsz"], only=set(C.ALL_CLASSES) - set(cfg["model"]["bite_classes"])):
        found.append((d.name, d.conf, d.box))
    for name, conf, (x1, y1, x2, y2) in found:
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
        cv2.putText(frame, f"{name} {conf:.2f}", (int(x1), max(15, int(y1) - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    for k in ("cast", "reel", "store", "bag"):
        x, y = cfg[f"{k}_x"], cfg[f"{k}_y"]
        if x and y:
            cv2.drawMarker(frame, (int(x), int(y)), (255, 200, 0), cv2.MARKER_CROSS, 24, 2)
            cv2.putText(frame, k, (int(x) + 12, int(y) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)
    return found


def preview(cfg, cap, det) -> None:
    print("Preview running - press 'q' in the preview window to quit.")
    last = time.time()
    fps = 0.0
    while True:
        frame = cap.grab()
        found = _draw(frame, cfg, det)
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1 / max(now - last, 1e-3))
        last = now
        cv2.putText(frame, f"{fps:.1f} FPS | {len(found)} det", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        scale = 960 / frame.shape[1]
        cv2.imshow("autofishing preview", cv2.resize(frame, None, fx=scale, fy=scale))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()


def test_image(cfg, det, path: str) -> None:
    frame = cv2.imread(path)
    if frame is None:
        raise SystemExit(f"Cannot read image: {path}")
    iw, ih = cfg["capture"]["image_width"], cfg["capture"]["image_height"]
    if frame.shape[1] != iw or frame.shape[0] != ih:
        print(f"[test] resizing {frame.shape[1]}x{frame.shape[0]} -> {iw}x{ih}")
        frame = cv2.resize(frame, (iw, ih))
    found = _draw(frame, cfg, det)
    if not found:
        print("No detections.")
    for name, conf, box in found:
        print(f"  {name:22s} {conf:.2f}  box={tuple(int(v) for v in box)}")
    out = "test_result.png"
    cv2.imwrite(out, frame)
    print(f"Annotated image saved to {out}")
    try:
        cv2.imshow("autofishing test", cv2.resize(frame, None, fx=960 / iw, fy=960 / iw))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except cv2.error:
        pass


def snip(cfg, cap, name: str) -> None:
    """Save a template crop from the live game into templates/<name>.png."""
    name = C.norm(name)
    print(f"\n=== Snip template '{name}' ===")
    a = _wait_point(f"the TOP-LEFT of '{name}'")
    b = _wait_point(f"the BOTTOM-RIGHT of '{name}'")
    frame = cap.grab()
    ax, ay = cap.from_screen(*a)
    bx, by = cap.from_screen(*b)
    x1, x2, y1, y2 = min(ax, bx), max(ax, bx), min(ay, by), max(ay, by)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        raise SystemExit("Empty selection.")
    folder = cfg["template"]["folder"]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{name}.png")
    cv2.imwrite(path, crop)
    print(f"Saved {path} ({x2 - x1}x{y2 - y1})")
    print("Known classes: " + ", ".join(C.ALL_CLASSES))
