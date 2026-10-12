"""Coba model Open Images (601 kelas) - mungkin ada kelas Excavator.

COCO cuma 80 kelas tanpa alat berat. Open Images jauh lebih besar dan
memang memuat 'Excavator' sebagai kelas resmi.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from ultralytics import YOLO  # noqa: E402

SRC = PROJECT / "INGIN SEPERTI INI"
KANDIDAT = ["yolo11n-oiv7.pt", "yolov8m-oiv7.pt", "yolov8n-oiv7.pt"]

model = None
for nama in KANDIDAT:
    try:
        print(f"mencoba {nama} ...")
        model = YOLO(nama)
        print(f"  OK -> {nama}")
        break
    except Exception as exc:  # noqa: BLE001
        print(f"  gagal: {type(exc).__name__}")

if model is None:
    sys.exit("tidak ada model Open Images yang bisa dimuat")

nama_kelas = model.names
print(f"\njumlah kelas: {len(nama_kelas)}")

alat = {i: n for i, n in nama_kelas.items()
        if any(k in n.lower() for k in (
            "excavat", "truck", "bulldoz", "loader", "tractor",
            "machin", "crane", "shovel", "dig", "vehicle", "trailer"))}
print(f"\nkelas alat berat / kendaraan yang tersedia:")
for i, n in sorted(alat.items()):
    print(f"  {i:4d}  {n}")

# uji deteksi di beberapa frame
print("\n" + "=" * 66)
print("DETEKSI DI VIDEO")
print("=" * 66)
for path in sorted(SRC.glob("*.mp4")):
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // 20)
    per: Counter = Counter()
    terbaik: dict[str, float] = {}
    for idx in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        res = model.predict(frame, conf=0.20, imgsz=960, device="0", verbose=False)[0]
        if res.boxes is None:
            continue
        for cid, cf in zip(res.boxes.cls.cpu().numpy(),
                           res.boxes.conf.cpu().numpy()):
            n = nama_kelas[int(cid)]
            per[n] += 1
            if float(cf) > terbaik.get(n, 0):
                terbaik[n] = float(cf)
    cap.release()
    print(f"\n{path.name}")
    if per:
        for n, c in per.most_common(8):
            print(f"   {n:22s} {c:3d}  conf {terbaik.get(n, 0):.2f}")
    else:
        print("   tidak ada")