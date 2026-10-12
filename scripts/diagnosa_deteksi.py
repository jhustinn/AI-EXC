"""Jawab: kenapa ekskavator tidak terdeteksi, dan kenapa kadang kosong?"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from ultralytics import YOLO  # noqa: E402

VIDEO = PROJECT / "INGIN SEPERTI INI" / "WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4"
model = YOLO(str(PROJECT / "yolov8n.pt"))

print("=" * 74)
print("1. APAKAH ADA KELAS 'EXCAVATOR' DI MODEL?")
print("=" * 74)
nama = model.names
print(f"total kelas COCO: {len(nama)}")
for i in sorted(nama):
    print(f"  {i:2d} {nama[i]}", end="\n" if i % 4 == 3 else "")
print()
cari = [n for n in nama.values() if any(k in n for k in ("excav", "bulldoz", "tractor", "loader", "shovel"))]
print(f"kelas mirip alat berat: {cari if cari else 'TIDAK ADA SATU PUN'}")

print()
print("=" * 74)
print("2. KENAPA KADANG TIDAK ADA DETEKSI SAMA SEKALI?")
print("=" * 74)

cap = cv2.VideoCapture(str(VIDEO))
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"video {w}x{h}, {total} frame, {fps:.0f} fps")

#Raster kumpulkan untuk sweep ambang
SEMUA: list[tuple] = []
n = 0
for idx in range(0, total, 5):
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, frame = cap.read()
    if not ok:
        break
    res = model.predict(frame, conf=0.10, iou=0.5, device="0", verbose=False)[0]
    boxes = []
    if res.boxes is not None and len(res.boxes):
        for b, c, cf in zip(res.boxes.xyxy.cpu().numpy(),
                            res.boxes.cls.cpu().numpy(),
                            res.boxes.conf.cpu().numpy()):
            x1, y1, x2, y2 = [float(v) for v in b]
            boxes.append((nama[int(c)], cf, (x2 - x1) / w, (x2 - x1) / (y2 - y1)))
    SEMUA.append((idx, boxes))
    n += 1
cap.release()
print(f"frame dianalisis: {n}")

print()
print("-- semua kelas yang muncul di video ini (conf >= 0,10) --")
semua_kelas: Counter = Counter()
for _, boxes in SEMUA:
    for nm, cf, _, _ in boxes:
        if cf >= 0.25:
            semua_kelas[nm] += 1
for nm, c in semua_kelas.most_common(12):
    print(f"  {nm:16s} {c:4d} frame  (dari {n})")

print()
print("-- sweep: berapa frame yang menghasilkan 'truck' layak --")
print(f"{'conf':>6}{'lebar_min':>11}{'frame truck':>13}{'frame kosong':>14}")
for conf in (0.25, 0.30, 0.35, 0.40, 0.50):
    for lebar_min in (0.0, 0.15, 0.25):
        ada = 0
        for _, boxes in SEMUA:
            ok = any(nm == "truck" and cf >= conf and lr >= lebar_min
                     for nm, cf, lr, ar in boxes)
            ada += ok
        print(f"{conf:>6.2f}{lebar_min:>11.2f}{ada:>10d}/{n}{n - ada:>11d}")

print()
print("-- kenapa frame kosong? periksa 5 frame tanpa truck --")
shown = 0
for idx, boxes in SEMUA:
    truck = [(cf, lr) for nm, cf, lr, ar in boxes if nm == "truck"]
    if truck and truck[0][0] >= 0.35 and truck[0][1] >= 0.15:
        continue
    if not boxes:
        print(f"  frame {idx:5d}: TIDAK ADA objek COCO sama sekali")
    else:
        ket = ", ".join(f"{nm} {cf:.2f} lebar{lr:.2f}" for nm, cf, lr, ar in boxes[:4])
        print(f"  frame {idx:5d}: {ket}")
    shown += 1
    if shown >= 5:
        break

# berapa lebar truck yang sebenarnya
lebar_truck = [lr for _, boxes in SEMUA for nm, cf, lr, ar in boxes
              if nm == "truck" and cf >= 0.35]
if lebar_truck:
    a = np.array(lebar_truck)
    print()
    print(f"-- lebar truck terdeteksi: min {a.min():.2f}  median {np.median(a):.2f}  maks {a.max():.2f}")
    print(f"  /Ambang min_width_ratio sekarang 0.15 membuang {int((a < 0.15).sum())} dari {len(a)} deteksi")