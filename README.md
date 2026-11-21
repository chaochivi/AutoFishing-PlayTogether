🎣 Play Together Auto-Fishing Bot

A computer vision-based auto-fishing bot for Play Together, supporting Windows PC (Steam) and Android emulators (BlueStacks and LDPlayer).

Automate fishing, detect fish bites, store catches, and repair your fishing rod using Python, OpenCV, and YOLOv8.

📖 Table of Contents
Overview
Supported Platforms
How It Works
Prerequisites
Installation
Emulator Setup
Configuration
Usage
Detection Classes
Control Flow
Training Your Own Model
Alternative Approaches
Troubleshooting
Project Structure
Related Projects
Disclaimer
🎯 Overview

This project automates the fishing mini-game in Play Together using computer vision and input automation.

The bot continuously monitors the game screen and automatically:

Detects when a fish bites using the exclamation mark (!) indicator.
Reacts to the bite and reels in the fish.
Detects the Store button and saves the catch.
Detects when the fishing rod breaks.
Automatically navigates the inventory and repairs the rod.
Repeats the fishing process continuously.

The main goal is to create a computer vision automation system that handles the complete fishing cycle with minimal manual interaction.

🖥️ Supported Platforms
Platform	Client / Emulator	Capture Method
Android	BlueStacks	MSS window capture / ADB
Android	LDPlayer	OpenCV / Win32 API
Windows	Steam PC Client	Computer Vision / OCR
⚙️ How It Works

The bot combines four main technologies.

1. Screen Capture

Captures the game window continuously to monitor fishing activity.

MSS

Fast screen capture.
Recommended for BlueStacks.
Suitable for real-time detection.

ADB Screencap

Captures Android emulator screenshots.
Useful for debugging and calibration.
Generally slower than direct window capture.

Win32 API

Supports emulator window interaction.
Can be used with LDPlayer.
2. Fish Bite Detection

The bot detects the exclamation mark (!) displayed above the character when a fish bites.

Two detection methods are supported:

YOLOv8 Object Detection

Detects game UI elements, including:

Exclamation mark.
Store button.
Broken rod notification.
Repair button.
Inventory tabs.

OpenCV Pixel Detection

Monitors a predefined screen region for pixel changes.

Advantages:

Lightweight.
Fast.
No machine learning model required.

Disadvantages:

More sensitive to resolution and visual changes.
3. Input Automation

The bot simulates mouse clicks and keyboard actions.

Supported libraries:

PyAutoGUI
PyDirectInput
Win32 API
4. Complete Automation Loop

The bot follows this process:

CAST → WAIT FOR BITE → REEL → STORE → REPAIR → REPEAT

📦 Prerequisites
Hardware
Windows 10 or Windows 11.
At least 8 GB RAM recommended.
NVIDIA GPU optional for model training.
Software
Python 3.10 or newer.
BlueStacks or LDPlayer.
Play Together installed.
Android SDK Platform Tools (optional).
Python Dependencies

Create a file named requirements.txt:

txt
mss>=9.0.0
numpy>=1.24.0
opencv-python>=4.8.0
pyautogui>=0.9.54
PyGetWindow>=0.0.9
PyYAML>=6.0.0
python-dotenv>=1.0.0
ultralytics
pywin32
Pillow


Install dependencies:

bash
pip install -r requirements.txt

🚀 Installation
Option A: YOLOv8-Based Bot (BlueStacks)

This approach uses a trained YOLOv8 model to detect fishing indicators and game UI elements.

Step 1: Clone Repository
bash
git clone https://github.com/tannguyen2k1/Play-Together-Auto-Fishing.git

cd Play-Together-Auto-Fishing

Step 2: Create Virtual Environment
bash
python -m venv .venv


Activate the environment:

PowerShell

powershell
.\.venv\Scripts\Activate.ps1


Windows CMD

cmd
.venv\Scripts\activate.bat

Step 3: Install Dependencies
bash
pip install -r requirements.txt

Step 4: Obtain YOLOv8 Weights

Place the trained model inside:

text
models/best.pt


You can use an available trained checkpoint or train your own model.

Step 5: Calibrate Coordinates

Run:

bash
python main.py --pick


Calibrate the following elements:

Cast button.
Reel/Jerk button.
Store button.
Backpack icon.

Save the resulting coordinates in config.yaml.

Step 6: Test Detection

Preview the game screen:

bash
python main.py --preview


Test detection using a screenshot:

bash
python main.py --test path/to/screenshot.png

Option B: OpenCV + Win32 API (LDPlayer)

This approach uses pixel change detection instead of a trained YOLO model.

Step 1: Install LDPlayer

Download and install LDPlayer.

Step 2: Clone Repository
bash
git clone https://github.com/Uranium1901/Autofishing_Playtogether.git

cd Autofishing_Playtogether

Step 3: Install Dependencies
bash
pip install pywin32 numpy imutils PyAutoGUI scipy Pillow opencv-python

Step 4: Configure LDPlayer

Recommended settings:

Setting	Value
Resolution	960 × 540
DPI	160
Language	Vietnamese
View	Highest / Zoomless
Step 5: Start the Bot
bash
python Autofishing.py

Option C: PC / Steam Alternative

PTFish is a commercial alternative for the native Windows version.

Features may include:

Automatic fishing.
Bite detection.
Store detection.
Gigantic fish support.
Automatic rod repair.
Session statistics.
Adjustable detection regions.

Check the provider's official page for availability, licensing, and compatibility.

🎮 Emulator Setup
BlueStacks
Install BlueStacks.
Sign in to Google Play.
Install Play Together.
Set the resolution to match config.yaml.
Enable the Keymap Overlay if required by your input configuration.
Use windowed mode for easier screen capture.
Launch the game and enter a fishing area.
LDPlayer
Install LDPlayer.
Set resolution to 960 × 540.
Set DPI to 160.
Change the language to Vietnamese if required by the pixel-detection implementation.
Set the game view to maximum.
Configure the input mapping.
Launch Play Together.
🔧 Configuration

The YOLOv8 implementation uses config.yaml to control detection, screen capture, timing, and automation.

Capture Settings
yaml
backend: window

capture:
  image_width: 1600
  image_height: 900

  top: 50
  left: 850
  width: 500
  height: 400

Model Settings
yaml
model:
  path: "models/best.pt"
  confidence: 0.40
  imgsz: 256

  bite_classes:
    - "exclamation-mark"

Bot Timing Settings
yaml
bot:
  poll_interval_ms: 0
  click_delay_ms: 0
  cast_delay_ms: 400

  after_catch_min_ms: 300
  after_catch_timeout_ms: 12000

  cooldown_after_bite_ms: 1200
  min_wait_before_bite_ms: 0

Repair Settings
yaml
allow_paid_repair: true

repair_timeout_ms: 25000
repair_click_gap_ms: 700

bag_x: 1537
bag_y: 500


Set allow_paid_repair to false if you do not want the bot to use paid repairs.

UI Detection Settings
yaml
ui_imgsz: 416
ui_confidence: 0.35

auto_cast: true

cast_mode: tap
jerk_mode: tap
store_mode: tap

action_mode: tap
action_key: space

Coordinate Settings
yaml
cast_x: 1268
cast_y: 541

reel_x: 1405
reel_y: 695

store_x: 1153
store_y: 600


Important: These are example coordinates for a 1600 × 900 logical resolution. Recalibrate them for your own emulator and window configuration.

▶️ Usage
Start the Bot

Activate your virtual environment:

powershell
.\.venv\Scripts\Activate.ps1


Run:

bash
python main.py


Alternatively:

bash
python -m autofishing

Command-Line Options
Command	Description
python main.py --pick	Calibrate UI coordinates
python main.py --preview	Preview screen capture
python main.py --test image.png	Test detection
python main.py	Start automatic fishing
Calibration Workflow
Open Play Together.
Equip your fishing rod.
Move to a fishing location.
Run python main.py --pick.
Follow the calibration prompts.
Click the required UI elements.
Save the generated coordinates.
Start the bot.
🔍 Detection Classes

The YOLOv8 model uses the following detection classes.

Detection Class	Purpose
exclamation-mark	Detects fish bites
store-button	Detects the Store popup
too-late-run-away	Detects missed catches
tool-is-broken	Detects broken fishing rods
tool-tab	Detects the inventory tools tab
repair-button	Detects the repair action
paid-repair-button	Detects paid repair confirmation
paid-repair-text	Detects paid repair text
repair-done-button	Detects completed repairs
repair-done-text	Detects repair completion text
🔄 Control Flow

The bot operates using a finite-state machine.

text
                  ┌──────────────┐
                  │     CAST     │
                  └──────┬───────┘
                         │
                         ▼
                ┌─────────────────┐
                │  WAITING_BITE   │
                └────────┬────────┘
                         │
             ┌───────────┼────────────┐
             │           │            │
             ▼           ▼            ▼
        Bite Found   Rod Broken   Missed Catch
             │           │            │
             ▼           ▼            ▼
          REEL         REPAIR       COOLDOWN
             │           │
             ▼           │
        AFTER_CATCH      │
             │           │
             ▼           │
           STORE         │
             │           │
             └─────┬─────┘
                   │
                   ▼
              COOLDOWN
                   │
                   ▼
                  CAST

State Descriptions

CAST

Clicks the fishing button.
Starts a new fishing attempt.

WAITING_BITE

Monitors the detection region.
Waits for the exclamation mark.
Checks for broken rod notifications.

AFTER_CATCH

Detects the Store popup.
Confirms the catch.
Handles missed catches.

REPAIR

Opens the backpack.
Navigates to the tools tab.
Selects the fishing rod.
Executes the repair flow.

COOLDOWN

Waits for the configured delay.
Returns to the casting state.
🧠 Training Your Own Model

You can train a custom YOLOv8 model to improve detection accuracy.

Step 1: Prepare Dataset

Download the Play Together dataset from Roboflow.

Dataset:

play-together2

Export the dataset in YOLO format and extract it into:

text
datasets/

Step 2: Train the Model

Run:

bash
python train.py


You can also use a GPU environment such as Kaggle for faster training.

Step 3: Deploy the Model

Copy your trained checkpoint:

bash
copy path\to\best.pt models\best.pt

Step 4: Validate Detection
bash
python main.py --test path\to\screenshot.png


Check the results before running the automation loop.

🛠️ Alternative Approaches
1. OpenCV Template Matching

Template matching can detect the exclamation mark without machine learning.

Example:

python
import cv2
import numpy as np

template = cv2.imread(
    "exclamation_mark_template.png",
    0
)

screenshot = cv2.imread(
    "screenshot.png",
    0
)

result = cv2.matchTemplate(
    screenshot,
    template,
    cv2.TM_CCOEFF_NORMED
)

threshold = 0.8

locations = np.where(result >= threshold)


Advantages:

No model training.
Easy to implement.
Lightweight.

Disadvantages:

Sensitive to resolution changes.
Sensitive to scaling and animation.
2. Pixel Change Detection

Monitors a specific region for changes in pixel values.

Advantages:

Very fast.
Low CPU usage.
No GPU required.

Disadvantages:

Requires precise calibration.
Can produce false detections.
3. Audio-Based Detection

Audio processing can identify fishing sounds or splash effects.

Possible technologies:

VB-Cable.
Python audio capture.
NumPy.
SciPy.

Audio detection can complement visual detection.

4. HSV Color Detection

OpenCV HSV filtering can identify UI elements based on color.

Potential applications:

Exclamation mark detection.
Fishing bar detection.
Fish shadow detection.
🐛 Troubleshooting
Bot Cannot Detect Fish Bites

Try the following:

Check the detection ROI.
Verify the screen resolution.
Recalibrate coordinates.
Lower the YOLO confidence threshold.
Run preview mode.
Check that the trained model contains the correct classes.
Bot Clicks Incorrectly
Verify emulator resolution.
Check coordinate calibration.
Ensure the correct game window is active.
Check input permissions.
Adjust click delays.
Rod Does Not Repair Automatically
Verify backpack coordinates.
Check repair button detection.
Verify the inventory layout.
Check allow_paid_repair.
Increase repair_timeout_ms if necessary.
High Detection Latency
Prefer MSS window capture over ADB.
Reduce model.imgsz.
Reduce the detection ROI.
Use GPU inference if supported.
Avoid unnecessary full-screen detection.
📁 Project Structure

Example structure for the YOLOv8 implementation:

text
Play-Together-Auto-Fishing/
│
├── main.py
├── train.py
├── kaggle_train.ipynb
├── config.yaml
├── requirements.txt
│
├── yolov8n.pt
│
├── models/
│   └── best.pt
│
├── datasets/
│
├── autofishing/
│   ├── cli/
│   ├── bot/
│   ├── detection/
│   ├── capture/
│   ├── input/
│   ├── training/
│   ├── config.py
│   └── constants.py
│
└── src/

🔗 Related Projects
Project	Approach	Platform
Play-Together-Auto-Fishing	YOLOv8 + MSS + PyAutoGUI	BlueStacks
Autofishing_Playtogether	OpenCV + Win32 API	LDPlayer
PTFish	Computer Vision + OCR	Windows / Steam

Project references:

https://github.com/tannguyen2k1/Play-Together-Auto-Fishing
https://github.com/Uranium1901/Autofishing_Playtogether
⚠️ Disclaimer

This project is intended for educational and personal research purposes.

Automating online games may violate the game's Terms of Service and could result in account restrictions or bans.

Use automation at your own risk.
Always review the game's Terms of Service.
Do not use automation to disrupt other players.
This project is not affiliated with Play Together, BlueStacks, or LDPlayer.

The primary purpose of this project is to demonstrate computer vision, object detection, Python automation, and real-time image processing.

📚 Additional Resources
Play Together Wiki: https://playtogether.fandom.com/
YOLO Documentation: https://docs.ultralytics.com/
OpenCV Documentation: https://docs.opencv.org/
MSS Documentation: https://python-mss.readthedocs.io/
Roboflow: https://roboflow.com/
⭐ Final Notes

Happy fishing! 🎣

If you find this project useful, consider giving it a ⭐ on GitHub.

Technologies: Python · OpenCV · YOLOv8 · MSS · PyAutoGUI · Win32 API · Computer Vision