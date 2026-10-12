"""Uji SAM untuk membantu melabeli bucket dengan kotak kasar manusia."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
imgs = sorted((OUT / "images" / "train").glob("*.jpg"))

# frame #0: POV kabin, bucket besar di tengah -> kotak kasar buatan manusia
uji = [
    (imgs[0], [140, 250, 245, 440]),    # bucket POV
    (imgs[194], [250, 380, 420, 520]),   # bucket eksternal dekat truck hijau
]

print("memuat SAM2.1-b (unduh sekali)...")
from ultralytics import SAM  # noqa: E402

try:
    sam = SAM("sam2.1_b.pt")
except Exception as exc:  # noqa: BLE001
    print("gagal muat SAM:", type(exc).__name__, exc)
    sys.exit(1)

panel = []
for p, kasar in uji:
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    res = sam.predict(img, bboxes=[kasar], verbose=False)[0]
    if res.boxes is None or len(res.boxes) == 0:
        print(f"{p.name}: SAM tidak mengembalikan mask")
        continue
    b = res.boxes.xyxy.cpu().numpy()[0]
    x1, y1, x2, y2 = [int(v) for v in b]

    visual = img.copy()
    # kotak kasar hijau (prompt manusia)
    cv2.rectangle(visual, tuple(kasar[:2]), tuple(kasar[2:]), (0, 255, 0), 3)
    # hasil SAM merah
    cv2.rectangle(visual, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.putText(visual, "hijau=prompt  merah=SAM", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    panel.append(visual)
    print(f"{p.name}: prompt={kasar} -> SAM={[x1, y1, x2, y2]}")

if panel:
    sheet = np.hstack([cv2.resize(im, (300, 533)) for im in panel])
    out = PROJECT / "data" / "uji_sam.jpg"
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"\nsheet -> {out}")