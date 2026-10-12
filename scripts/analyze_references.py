"""Analisis 4 video referensi: apa yang bisa dideteksi YOLO COCO?

Tujuannya menentukan kelas apa yang perlu dilabeli manual dan mana
yang sudah otomatis (mis. 'truck' ada di COCO).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402

SRC = PROJECT / "INGIN SEPERTI INI"

from ultralytics import YOLO  # noqa: E402

model = YOLO(str(PROJECT / "yolov8n.pt"))
NAMES = model.names

total_classes: Counter = Counter()

for path in sorted(SRC.glob("*.mp4")):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"{path.name}: gagal dibuka")
        continue

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = total / fps if fps else 0

    print("=" * 72)
    print(path.name)
    print(f"  {w}x{h} | {fps:.1f} fps | {dur:.1f} dtk ({total} frame)")

    step = max(1, total // 30)
    per_class: Counter = Counter()
    frames_with_det = 0
    sampled = 0
    best_conf: dict[str, float] = {}

    for idx in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        sampled += 1
        res = model.predict(frame, conf=0.30, device="0", verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            continue
        frames_with_det += 1
        cls_arr = res.boxes.cls.cpu().numpy()
        conf_arr = res.boxes.conf.cpu().numpy()
        for cid, cf in zip(cls_arr, conf_arr):
            nm = NAMES[int(cid)]
            per_class[nm] += 1
            total_classes[nm] += 1
            if float(cf) > best_conf.get(nm, 0.0):
                best_conf[nm] = float(cf)

    print(f"  frame dianalisis: {sampled} | frame dengan deteksi: {frames_with_det}")
    if per_class:
        print("  kelas terdeteksi:")
        for nm, cnt in per_class.most_common():
            print(f"    {nm:14s} {cnt:4d}   conf tertinggi {best_conf.get(nm, 0):.2f}")
    else:
        print("  TIDAK ADA objek COCO yang terdeteksi")
    cap.release()

print("=" * 72)
print("TOTAL semua video:")
if total_classes:
    for nm, cnt in total_classes.most_common():
        print(f"  {nm:14s} {cnt}")
else:
    print("  (tidak ada deteksi COCO sama sekali)")