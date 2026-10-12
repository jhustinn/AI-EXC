"""Buat kontak sheet dari beberapa frame + label, supaya bisa dicek mata."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
NAMA = {0: "bucket", 1: "truck"}
WARNA = {0: (0, 200, 0), 1: (0, 170, 255)}   # BGR

imgs = sorted((OUT / "images" / "train").glob("*.jpg"))
lebar = 5
dipilih = np.linspace(0, len(imgs) - 1, lebar * 2).astype(int)

panel_list = []
for i in dipilih:
    p = imgs[i]
    img = cv2.imread(str(p))
    h, w = img.shape[:2]

    lbl = OUT / "labels" / "train" / f"{p.stem}.txt"
    n = 0
    if lbl.exists():
        for line in lbl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            cid, cx, cy, bw, bh = line.split()
            cid = int(cid)
            x1 = int((float(cx) - float(bw) / 2) * w)
            y1 = int((float(cy) - float(bh) / 2) * h)
            x2 = int((float(cx) + float(bw) / 2) * w)
            y2 = int((float(cy) + float(bh) / 2) * h)
            cv2.rectangle(img, (x1, y1), (x2, y2), WARNA[cid], 2)
            cv2.putText(img, f"{NAMA[cid]}", (x1, max(12, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, WARNA[cid], 1)
            n += 1

    # diperkecil supaya muat di kontak sheet
    img = cv2.resize(img, (w // 2, h // 2))
    cv2.putText(img, f"#{i} label={n}", (5, 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    panel_list.append(img)

h0, w0 = panel_list[0].shape[:2]
sheet = np.zeros((h0 * 2, w0 * lebar, 3), dtype=np.uint8)
for k, im in enumerate(panel_list):
    r, c = divmod(k, lebar)
    sheet[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = im

out = PROJECT / "data" / "cek_label_truck.jpg"
out.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
print(f"kontak sheet -> {out}")
print(f"total frame train: {len(imgs)}")