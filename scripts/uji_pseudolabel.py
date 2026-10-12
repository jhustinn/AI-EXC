"""Pseudo-label bucket otomatis: SAM auto-mask + filter geometris & warna.

Nol labeling manusia. Ambil mask dari SAM (mode otomatis), beri skor dengan
ciri bucket, pilih yang terbaik. Kandidat ditampilkan agar bisa dinilai.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(POV := "src")) if False else None
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from ultralytics import SAM  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
imgs = sorted((OUT / "images" / "train").glob("*.jpg"))
uji = [imgs[0], imgs[32], imgs[64], imgs[97], imgs[129],
       imgs[161], imgs[194], imgs[258], imgs[291]]

sam = SAM("sam2.1_b.pt")


def skor(mask: np.ndarray, hsv: np.ndarray) -> float:
    """0-1: seberapa mirip kandidat dengan bucket alat berat."""
    m = mask > 0.5
    ys, xs = np.where(m)
    if len(xs) == 0:
        return 0.0
    bw = xs.max() - xs.min() + 1
    bh = ys.max() - ys.min() + 1
    area = len(xs) / mask.size

    if not (0.02 < area < 0.32):
        return 0.0
    s_luas = max(0.0, min(1.0, 1.0 - abs(area - 0.10) / 0.10))

    rasio = bw / max(1, bh)
    if not (0.35 < rasio < 3.2):
        return 0.0
    s_bentuk = 1.0 - min(1.0, abs(rasio - 1.0) / 1.4)

    # warna:bucket kuning.tools / pucat karena sinar matahari
    px = hsv[m]
    if len(px) == 0:
        return 0.0
    hue = px[:, 0].astype(np.float32) * 2.0          # OpenCV 0-179 -> 0-359
    sat = px[:, 1].astype(np.float32)
    val = px[:, 2].astype(np.float32)
    kuning = ((hue >= 12) & (hue <= 45) & (sat >= 45) & (val >= 60)).mean()
    pucat = ((sat >= 15) & (sat <= 90) & (val >= 110)).mean()   # krem terik
    s_warna = max(kuning, pucat * 0.6)

    return s_luas * s_bentuk * s_warna


lebar = 3
panel = []
for p in uji:
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    res = sam.predict(img, verbose=False)[0]
    best = None
    if res.masks is not None:
        for mask in res.masks.data.cpu().numpy():
            s = skor(mask, hsv)
            if s > 0 and (best is None or s > best[0]):
                ys, xs = np.where(mask > 0.5)
                best = (s, int(xs.min()), int(ys.min()),
                        int(xs.max()), int(ys.max()))

    visual = img.copy()
    if best:
        _, x1, y1, x2, y2 = best
        cv2.rectangle(visual, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(visual, f"skor {best[0]:.2f}", (x1, max(14, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    img2 = cv2.resize(visual, (w // 2, h // 2))
    cv2.putText(img2, f"{p.stem[-9:]}", (5, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    panel.append(img2)

baris = (len(panel) + lebar - 1) // lebar
h0, w0 = panel[0].shape[:2]
sheet = np.zeros((h0 * baris, w0 * lebar, 3), dtype=np.uint8)
for k, im in enumerate(panel):
    r, c = divmod(k, lebar)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

out = PROJECT / "data" / "uji_pseudolabel.jpg"
cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print(f"frame diuji: {len(panel)}")
print(f"sheet -> {out}")