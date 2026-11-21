# 🎣 Play Together Auto-Fishing Macro

Python + OpenCV + YOLOv8 macro for Play Together (BlueStacks, LDPlayer, Steam PC).
Loop: **CAST → WAIT FOR BITE → REEL → STORE → REPAIR → REPEAT**

## Quick start (Windows)

```bat
setup.bat                 :: venv + dependencies
run.bat --pick            :: calibrate buttons + bite region (hover, press F7)
run.bat --preview         :: verify detections live (q to quit)
run.bat                   :: start fishing
```

Hotkeys while running: **F8** pause / resume · **F10** stop · mouse to a screen corner = emergency abort.
Use `--dry-run` to see what the bot *would* click without clicking.

## Detection modes

| Mode | When | What you need |
|------|------|---------------|
| **YOLOv8** | `models/best.pt` exists | trained weights (see `train.py`) |
| **Template / HSV** | no model | PNG crops in `templates/` — create with `python main.py --snip store-button` |

With no templates at all the bot still looks for the red/orange `!` using HSV colour filtering,
but you need templates for `store-button`, `tool-is-broken`, `too-late-run-away`, and the repair classes
if you want store/repair automation.

Force one with `--detector yolo|template`.

## Steps for a first run

1. Set BlueStacks / LDPlayer to a fixed resolution; set `window_title` in `config.yaml`.
2. Stand at a fishing spot with the rod equipped.
3. `run.bat --pick` – record Cast, Reel, Store, Backpack (+ optional rod slot / close) and the bite ROI.
4. `run.bat --preview` – cast manually; the green box must contain the `!` when a fish bites.
5. `run.bat`.

## Backends

* `backend: window` – MSS capture of the window + PyAutoGUI / PyDirectInput clicks (BlueStacks, LDPlayer, Steam)
* `backend: screen` – full primary monitor
* `backend: adb` – `adb exec-out screencap` + `adb shell input tap` (set `adb_serial`)

## Files

```
main.py  train.py  config.yaml  requirements.txt  setup.bat  run.bat
autofishing/
  cli/        main.py (arguments)  tools.py (--pick --preview --test --snip)
  bot/        fishing_bot.py       (state machine)
  detection/  yolo.py  template.py (OpenCV templates + HSV)
  capture/    window.py            (MSS window / ADB)
  input/      controller.py  hotkeys.py
  config.py   constants.py
```

> ⚠️ Automating online games may violate their Terms of Service. Use at your own risk.
