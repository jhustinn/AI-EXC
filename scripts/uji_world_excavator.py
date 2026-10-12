"""Uji: bisa bucket diturunkan otomatis dari kotak 'excavator'?

Kalau bbox excavator mencakup lengan + bucket, maka bagian distal
(ujung bawah dari bbox) adalah bucket - tanpa perlu labeling manusia.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from ultralytics import YOLO  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
imgs = sorted((OUT / "images" / "train").glob("*.jpg"))

model = YOLO("yolov8s-worldv2.pt")
model.set_classes(["excavator"])

lebar = 5
idxs = np.linspace(0, len(imgs) - 1, lebar * 2).astype(int)
panel = []
jumlah_kena = 0

for i in idxs:
    p = imgs[i]
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    res = model.predict(img, conf=0.20, verbose=False)[0]
    n = 0
    if res.boxes is not None and len(res.boxes):
        for b, cf in zip(res.boxes.xyxy.cpu().numpy(),
                         res.boxes.conf.cpu().numpy()):
            x1, y1, x2, y2 = [int(v) for v in b]
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.putText(img, f"excavator {cf:.2f}", (x1, max(14, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            n += 1
    jumlah_kena += n
    img = cv2.resize(img, (w // 2, h // 2))
    cv2.putText(img, f"#{i} n={n}", (5, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    panel.append(img)

h0, w0 = panel[0].shape[:2]
sheet = np.zeros((h0 * 2, w0 * lebar, 3), dtype=np.uint8)
for k, im in enumerate(panel):
    r, c = divmod(k, lebar)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

out = PROJECT / "data" / "uji_excavator_world.jpg"
cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print(f"kotak excavator ditemukan di {jumlah_kena} dari {len(idxs)} frame")
print(f"sheet -> {out}")