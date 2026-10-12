"""Coba berbagai istilah untuk bucket alat berat lewat YOLO-World."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

SRC = PROJECT / "INGIN SEPERTI INI"

KELAS = [
    "shovel", "scoop", "digger bucket", "excavator arm", "backhoe",
    "clamshell bucket", "grab bucket", "bucket teeth", "construction bucket",
]

model = YOLO("yolov8s-worldv2.pt")
model.set_classes(KELAS)

grand: Counter = Counter()
best: dict[str, float] = {}

for path in sorted(SRC.glob("*.mp4")):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        continue
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // 20)
    for idx in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        res = model.predict(frame, conf=0.15, device="0", verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            continue
        for cid, cf in zip(res.boxes.cls.cpu().numpy(), res.boxes.conf.cpu().numpy()):
            nm = KELAS[int(cid)]
            grand[nm] += 1
            if float(cf) > best.get(nm, 0.0):
                best[nm] = float(cf)
    cap.release()

print("\nHASIL YOLO-World (ambang 0.15):")
if grand:
    for nm, c in grand.most_common():
        print(f"  {nm:20s} {c:4d} deteksi   conf tertinggi {best.get(nm, 0):.2f}")
else:
    print("  TIDAK ADA yang terdeteksi untuk istilah manapun")