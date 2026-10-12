"""Uji SAM mode otomatis: apakah bisa_mask bucket tanpa prompt manusia?"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from ultralytics import SAM  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
imgs = sorted((OUT / "images" / "train").glob("*.jpg"))
uji = [imgs[0], imgs[32], imgs[97], imgs[129], imgs[161], imgs[194], imgs[258], imgs[291]]

sam = SAM("sam2.1_b.pt")

lebar = 4
panel = []
for p in uji:
    img = cv2.imread(str(p))
    h, w = img.shape[:2]

    # mode otomatis: tanpa bbox / tanpa point
    try:
        res = sam.predict(img, verbose=False)[0]
    except Exception as exc:  # noqa: BLE001
        print(f"{p.name}: SAM otomatis gagal -> {type(exc).__name__}: {exc}")
        continue

    n = 0
    if res.masks is not None:
        data = res.masks.data.cpu().numpy()
        for m in data:
            ys, xs = np.where(m > 0.5)
            if len(xs) == 0:
                continue
            frac = len(xs) / m.size
            if not (0.005 < frac < 0.60):      # buang terlalu kecil / terlalu besar
                continue
            cv2.rectangle(img, (int(xs.min()), int(ys.min())),
                          (int(xs.max()), int(ys.max())), (0, 0, 255), 2)
            n += 1
    img = cv2.resize(img, (w // 2, h // 2))
    cv2.putText(img, f"{p.stem[-9:]} mask={n}", (5, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    panel.append(img)

baris = (len(panel) + lebar - 1) // lebar
h0, w0 = panel[0].shape[:2]
sheet = np.zeros((h0 * baris, w0 * lebar, 3), dtype=np.uint8)
for k, im in enumerate(panel):
    r, c = divmod(k, lebar)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

out = PROJECT / "data" / "uji_sam_otomatis.jpg"
cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print(f"frame diuji: {len(panel)}")
print(f"sheet -> {out}")