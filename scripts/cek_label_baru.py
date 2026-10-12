"""Visualisasi kotak bucket & excavator yang baru dilabel, untuk verifikasi."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
NAMA = {0: "bucket", 1: "truck", 2: "excavator"}
WARNA = {0: (0, 200, 0), 1: (200, 200, 200), 2: (0, 170, 255)}

semua = []
for split in ("train", "val"):
    for lbl in sorted((OUT / "labels" / split).glob("*.txt")):
        isi = [ln for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()]
        punya = {int(ln.split()[0]) for ln in isi}
        if punya & {0, 2}:   # bucket atau excavator, bukan truck
            semua.append((split, lbl.stem, isi))

print(f"frame dengan bucket/excavator: {len(semua)}")

COLS, ROWS = 6, 3
panel = []
for split, stem, isi in semua[:COLS * ROWS]:
    img = cv2.imread(str(OUT / "images" / split / f"{stem}.jpg"))
    h, w = img.shape[:2]
    for ln in isi:
        cid, cx, cy, bw, bh = ln.split()
        cid = int(cid)
        if cid not in (0, 2):
            continue
        cx, cy, bw, bh = float(cx), float(cy), float(bw), float(bh)
        x1 = int((cx - bw / 2) * w); y1 = int((cy - bh / 2) * h)
        x2 = int((cx + bw / 2) * w); y2 = int((cy + bh / 2) * h)
        cv2.rectangle(img, (x1, y1), (x2, y2), WARNA[cid], 3)
        cv2.putText(img, NAMA[cid], (x1, max(14, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, WARNA[cid], 2)
    img = cv2.resize(img, (239, 425), interpolation=cv2.INTER_AREA)
    cv2.putText(img, stem[-9:], (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 2)
    panel.append(img)

h0, w0 = panel[0].shape[:2]
sheet = np.zeros((h0 * ROWS, w0 * COLS, 3), dtype=np.uint8)
for k, im in enumerate(panel):
    r, c = divmod(k, COLS)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

keluaran = PROJECT / "data" / "cek_label_baru.jpg"
cv2.imwrite(str(keluaran), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
print(f"-> {keluaran}")