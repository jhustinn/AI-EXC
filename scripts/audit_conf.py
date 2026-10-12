"""Audit label truck pada beberapa ambang conf, supaya pilih yang jujur.

Kriteria: bucket/truck di video ini besar dan sering menutup sebagian frame,
jadi conf>=0.70 dipakai sebagai kandidat label yang lebih bersih.
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

OUT = PROJECT / "datasets" / "excavator"
detector = YOLO(str(PROJECT / "yolov8n.pt"))
NAMA = detector.names

imgs = sorted((OUT / "images" / "train").glob("*.jpg"))

for ambang in (0.50, 0.60, 0.70, 0.80):
    total = 0
    frame_ada = 0
    for p in imgs:
        img = cv2.imread(str(p))
        if img is None:
            continue
        h, w = img.shape[:2]
        res = detector.predict(img, conf=ambang, verbose=False)[0]
        if res.boxes is None:
            continue
        n = 0
        for b, c in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy()):
            if NAMA[int(c)] not in ("truck", "bus"):
                continue
            x1, y1, x2, y2 = b
            if (x2 - x1) / w < 0.15:
                continue
            n += 1
        if n:
            frame_ada += 1
        total += n
    print(f"conf>={ambang:.2f}: kotak={total:4d}  frame_berlabel={frame_ada:3d}/{len(imgs)}")

# sheet visual: hanya kotak conf>=0.70, supaya bisa dinilai mata
sheet_list = []
lebar = 5
idxs = np.linspace(0, len(imgs) - 1, lebar * 2).astype(int)
for i in idxs:
    p = imgs[i]
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    res = detector.predict(img, conf=0.70, verbose=False)[0]
    n = 0
    if res.boxes is not None:
        for b, c, cf in zip(res.boxes.xyxy.cpu().numpy(),
                            res.boxes.cls.cpu().numpy(),
                            res.boxes.conf.cpu().numpy()):
            if NAMA[int(c)] not in ("truck", "bus"):
                continue
            x1, y1, x2, y2 = [int(v) for v in b]
            if (x2 - x1) / w < 0.15:
                continue
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 170, 255), 3)
            cv2.putText(img, f"{cf:.2f}", (x1, max(14, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 170, 255), 2)
            n += 1
    img = cv2.resize(img, (w // 2, h // 2))
    cv2.putText(img, f"#{i} n={n}", (5, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    sheet_list.append(img)

h0, w0 = sheet_list[0].shape[:2]
sheet = np.zeros((h0 * 2, w0 * lebar, 3), dtype=np.uint8)
for k, im in enumerate(sheet_list):
    r, c = divmod(k, lebar)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

out = PROJECT / "data" / "audit_conf070.jpg"
cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print(f"\nsheet -> {out}")