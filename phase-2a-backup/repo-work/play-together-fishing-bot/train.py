"""Train a YOLOv8 model on the Play Together dataset (Roboflow 'play-together2').

1. Export the dataset in "YOLOv8" format and extract it into datasets/
   (it must contain datasets/data.yaml).
2. python train.py [--epochs 100] [--imgsz 640] [--batch 16]
3. best.pt is copied to models/best.pt
"""
import argparse
import glob
import os
import shutil


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="datasets/data.yaml")
    ap.add_argument("--base", default="yolov8n.pt")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default=None, help="0 for first GPU, 'cpu' otherwise")
    a = ap.parse_args()

    if not os.path.exists(a.data):
        raise SystemExit(f"Dataset config not found: {a.data}")

    from ultralytics import YOLO

    model = YOLO(a.base)
    model.train(data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, device=a.device,
                project="runs", name="playtogether", exist_ok=True)

    runs = sorted(glob.glob("runs/**/weights/best.pt", recursive=True), key=os.path.getmtime)
    if runs:
        os.makedirs("models", exist_ok=True)
        shutil.copy(runs[-1], "models/best.pt")
        print("Copied", runs[-1], "-> models/best.pt")


if __name__ == "__main__":
    main()
