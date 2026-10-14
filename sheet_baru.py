"""Lembar label dari frame video yang belum dilabeli.
Frame diambil bergantian antar video agar satu lembar tidak semua dari
satu sumber. Batch lewat environment LABEL_BATCH.
"""
import os
from pathlib import Path

import cv2
import numpy as np

DS = Path("datasets/excavator/images")
LB = Path("datasets/excavator/labels")
OUT = Path("data/label_sheets")
OUT.mkdir(parents=True, exist_ok=True)

BATCH = int(os.environ.get("LABEL_BATCH", "0"))
PER_VIDEO = 8
PER_SHEET = 6
COLS, ROWS = 2, 3
CW, CH = 300, 533


def sudah(stem):
    for sp in ("train", "val"):
        f = LB / sp / f"{stem}.txt"
        if not f.exists():
            continue
        isi = [x for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
        if any(int(x.split()[0]) in (0, 2) for x in isi):
            return True
    return False


kandidat = [(sp, im) for sp in ("train", "val")
            for im in sorted((DS / sp).glob("*.jpg")) if not sudah(im.stem)]
print(f"belum dilabeli: {len(kandidat)}")

per = {}
for sp, im in kandidat:
    per.setdefault(im.stem.split("_")[0], []).append((sp, im))

grup = []
for vid, lst in sorted(per.items()):
    n = min(PER_VIDEO, max(1, len(lst)))
    awal = (BATCH * n) % len(lst)
    grup.append([lst[(awal + i) % len(lst)] for i in range(n)])

dipilih = []
i = 0
while len(dipilih) < PER_SHEET and any(len(x) > i for x in grup):
    for g in grup:
        if len(g) > i and len(dipilih) < PER_SHEET:
            dipilih.append(g[i])
    i += 1

if not dipilih:
    print("tidak ada frame tersisa")
    raise SystemExit

print("dari video:", sorted({im.stem.split("_")[0] for _, im in dipilih}))


def grid(img):
    c = np.full((CH, CW + 30, 3), 20, dtype=np.uint8)
    c[:, 30:] = cv2.resize(img, (CW, CH), interpolation=cv2.INTER_AREA)
    for u in range(0, 101, 10):
        x = int(u / 100 * CW) + 30
        cv2.line(c, (x, 0), (x, CH), (0, 0, 255) if u % 50 == 0 else (85, 85, 85), 1)
        cv2.putText(c, str(u), (x - 8, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1)
    for v in range(0, 101, 10):
        y = int(v / 100 * CH)
        cv2.line(c, (30, y), (30 + CW, y), (0, 0, 255) if v % 50 == 0 else (85, 85, 85), 1)
        cv2.putText(c, str(v), (1, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1)
    return c


panel = []
for k, (sp, im) in enumerate(dipilih):
    panel.append((k, im, grid(cv2.imread(str(im)))))

h0, w0 = panel[0][2].shape[:2]
sheet = np.zeros((ROWS * h0, COLS * w0, 3), dtype=np.uint8)
for k, (_, _, im) in enumerate(panel):
    r, cc = divmod(k, COLS)
    sheet[r * h0:(r + 1) * h0, cc * w0:(cc + 1) * w0] = im

nama = OUT / f"baru_{BATCH + 1:02d}.jpg"
cv2.imwrite(str(nama), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
(OUT / f"baru_{BATCH + 1:02d}.txt").write_text(
    chr(10).join(f"{k + 1}{chr(9)}{im.stem}" for k, (_, im, _) in enumerate(panel)),
    encoding="utf-8")
print("->", nama)
