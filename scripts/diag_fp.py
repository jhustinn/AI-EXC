"""Diagnosa false positive pada label truck."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
detector = YOLO(str(PROJECT / "yolov8n.pt"))
NAMA = detector.names

# frame yang salah tadi: index 129 di folder train
imgs = sorted((OUT / "images" / "train").glob("*.jpg"))
for idx in (32, 64, 129, 161, 226, 258):
    p = imgs[idx]
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    res = detector.predict(img, conf=0.25, verbose=False)[0]
    print(f"\n#{idx}  {p.name}  {w}x{h}")
    if res.boxes is None:
        print("   tidak ada deteksi")
        continue
    for b, c, cf in zip(res.boxes.xyxy.cpu().numpy(),
                        res.boxes.cls.cpu().numpy(),
                        res.boxes.conf.cpu().numpy()):
        x1, y1, x2, y2 = b
        frac_w = (x2 - x1) / w
        frac_h = (y2 - y1) / h
        area = frac_w * frac_h
        print(f"   {NAMA[int(c)]:12s} conf={cf:.2f}  "
              f"lebar={frac_w:.2f} tinggi={frac_h:.2f} area={area:.2f}")

# sebaran kelas yang dipakai sebagai 'truck'
print("\n" + "=" * 60)
print("kelas apa yang sebenarnya dipakaiAcross semua frame:")
dipakai: Counter = Counter()
for p in sorted((OUT / "images").rglob("*.jpg")):
    img = cv2.imread(str(p))
    if img is None:
        continue
    res = detector.predict(img, conf=0.25, verbose=False)[0]
    if res.boxes is None:
        continue
    for c in res.boxes.cls.cpu().numpy():
        nm = NAMA[int(c)]
        if nm in ("truck", "bus"):
            dipakai[nm] += 1
for nm, cnt in dipakai.most_common():
    print(f"   {nm:8s} {cnt}")