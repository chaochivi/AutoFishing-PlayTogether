"""Play Together Auto-Fishing - entry point.

    python main.py              start fishing
    python main.py --pick       calibrate coordinates
    python main.py --preview    live detection preview
    python main.py --test X.png test detection on a screenshot
    python main.py --snip NAME  save a template (no-YOLO mode)
"""
import sys

from autofishing.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
