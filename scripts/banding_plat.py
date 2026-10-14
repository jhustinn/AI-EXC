"""Bandingkan varian model plat: akurasi vs kecepatan."""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

DS = PROJECT / "datasets" / "excavator"
ACUAN = ["v2_2026-10-10_at_10_00200", "v2_2026-10-10_at_10_01380",
         "v1_2026-10-10_at_10_01780", "v1_2026-10-10_at_10_00720"]

VARIAN = ["v1n", "v1s", "v1l"]

gambar = []
for stem in ACUAN:
    for split in ("train", "val"):
        p = DS / "images" / split / f"{stem}.jpg"
        if p.exists():
            gambar.append(cv2.imread(str(p)))
            break

print(f"gambar uji: {len(gambar)}")
print(f"{'varian':8s}{'deteksi':>9}{'conf rata':>11}{'ms/frame':>11}")
print("-" * 40)

for v in VARIAN:
    path = PROJECT / "weights" / "plate" / f"license-plate-finetune-{v}.pt"
    if not path.is_file():
        continue
    m = YOLO(str(path))
    m.predict(gambar[0], imgsz=960, device="0", verbose=False)  # pemanasan

    konf, n_deteksi = [], 0
    t0 = time.perf_counter()
    for im in gambar:
        res = m.predict(im, conf=0.30, imgsz=960, device="0", verbose=False)[0]
        n = 0 if res.boxes is None else len(res.boxes)
        n_deteksi += n
        if n:
            konf.extend(float(c) for c in res.boxes.conf.cpu().numpy())
    ms = (time.perf_counter() - t0) / len(gambar) * 1000

    rata = sum(konf) / len(konf) if konf else 0.0
    print(f"{v:8s}{n_deteksi:>9}{rata:>11.2f}{ms:>11.0f}")