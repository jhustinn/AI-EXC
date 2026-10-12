"""Latih detektor bucket + excavator."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

from ultralytics import YOLO  # noqa: E402

DATA = PROJECT / "datasets" / "excavator" / "data.yaml"
RUN = PROJECT / "runs" / "alat_berat_v1"

model = YOLO(str(PROJECT / "yolov8n.pt"))
model.train(
    data=str(DATA),
    epochs=250,
    imgsz=768,
    batch=8,
    device=0,
    workers=0,
    project=str(PROJECT / "runs"),
    name="alat_berat_v2",
    exist_ok=True,
    seed=0,
    patience=60,
    # dataset kecil, augmentasimoderate supaya tidak overfit
    hsv_v=0.3, hsv_s=0.4,
    degrees=10, translate=0.1, scale=0.4, fliplr=0.5,
    mosaic=0.5,
)

BEST = PROJECT / "runs" / "alat_berat_v2" / "weights" / "best.pt"
print("terbaik:", BEST)