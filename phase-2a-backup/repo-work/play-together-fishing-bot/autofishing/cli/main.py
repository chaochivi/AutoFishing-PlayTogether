from __future__ import annotations

import argparse
import sys

from ..config import load_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autofishing", description="Play Together auto-fishing macro")
    p.add_argument("--config", default="config.yaml", help="path to config.yaml")
    p.add_argument("--pick", action="store_true", help="calibrate UI coordinates and bite region")
    p.add_argument("--preview", action="store_true", help="live preview of capture + detections")
    p.add_argument("--test", metavar="IMAGE", help="run detection on a screenshot")
    p.add_argument("--snip", metavar="NAME", help="save a template image (e.g. store-button)")
    p.add_argument("--detector", choices=["auto", "yolo", "template"], help="override detector")
    p.add_argument("--dry-run", action="store_true", help="detect and log but never click")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(args.config)

    # --test needs no capture / input at all
    if args.test:
        from ..detection import make_detector
        from . import tools

        tools.test_image(cfg, make_detector(cfg, args.detector), args.test)
        return 0

    from ..capture import make_capture
    from . import tools

    cap = make_capture(cfg)

    if args.pick:
        tools.pick(cfg, cap, args.config)
        return 0
    if args.snip:
        tools.snip(cfg, cap, args.snip)
        return 0

    from ..detection import make_detector

    det = make_detector(cfg, args.detector)

    if args.preview:
        tools.preview(cfg, cap, det)
        return 0

    from ..bot import FishingBot
    from ..input import Hotkeys, make_input

    inp = make_input(cfg, cap)
    if args.dry_run:
        class _Dry:
            def __getattr__(self, name):
                return lambda *a, **k: print(f"[dry-run] {name}{a}")

        inp = _Dry()

    print("Starting in 3 seconds - focus the game window now...")
    import time

    time.sleep(3)
    try:
        FishingBot(cfg, cap, inp, det, Hotkeys(cfg)).run()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
