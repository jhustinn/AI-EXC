"""Deteksi bucket TANPA training: segmentasi warna kuning alat + bentuk.

Bucket ekskavator berwarna kuning/'gold' yang mencolok dan berbeda dari
latar (aspal abu-abu, tanah, truck hijau, langit). Lengan juga kuning,
jadi bucket diambil sebagai gumpalan kuning di UJUNG lengan.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
imgs = sorted((OUT / "images" / "train").glob("*.jpg"))
uji = [imgs[0], imgs[32], imgs[64], imgs[97], imgs[129],
       imgs[161], imgs[194], imgs[258], imgs[291]]


def mask_kuning(img: np.ndarray) -> np.ndarray:
    """Kuningalat berat, bukan kuning tanah/beton."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    # rentang H untuk emas/kuning CAT: 10-40 (dalam skala OpenCV 0-179)
    m = ((h >= 8) & (h <= 40) & (s >= 70) & (v >= 60)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k, iterations=1)
    return m


def bucket_dari_warna(img: np.ndarray):
    """Gumpalan kuning terbesar yang berada di separuh bawah frame."""
    h, w = img.shape[:2]
    m = mask_kuning(img)
    n, label, stats, cent = cv2.connectedComponentsWithStats(m, 8)

    kandidat = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 0.004 * w * h:      # terlalu kecil untuk jadi bucket
            continue
        if area > 0.55 * w * h:       # terlalu besar = background kuning
            continue
        rasio = bw / max(1, bh)
        if not (0.25 < rasio < 5.0):
            continue
        # bucket condong di bawah titik tengah frame
        kandidat.append((area, int(x), int(y), int(x + bw), int(y + bh),
                         float(cent[i][1] / h)))

    if not kandidat:
        return None
    kandidat.sort(key=lambda t: -t[0])
    return kandidat[0]


lebar = 3
panel = []
jumlah = 0
for p in uji:
    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    vis = img.copy()
    cv2.addWeighted(img, 0.65, cv2.cvtColor(mask_kuning(img), cv2.COLOR_GRAY2BGR),
                    0.35, 0, vis)
    hasil = bucket_dari_warna(img)
    if hasil:
        jumlah += 1
        _, x1, y1, x2, y2, cy = hasil
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(vis, "bucket?", (x1, max(14, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    v2 = cv2.resize(vis, (w // 2, h // 2))
    cv2.putText(v2, f"{p.stem[-9:]}", (5, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    panel.append(v2)

baris = (len(panel) + lebar - 1) // lebar
h0, w0 = panel[0].shape[:2]
sheet = np.zeros((h0 * baris, w0 * lebar, 3), dtype=np.uint8)
for k, im in enumerate(panel):
    r, c = divmod(k, lebar)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

out = PROJECT / "data" / "uji_warna_bucket.jpg"
cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print(f"kandidat bucket ditemukan di {jumlah}/{len(uji)} frame")
print(f"sheet -> {out}")