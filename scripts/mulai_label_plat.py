"""Lembar kerja untuk melabeli plat nomor.

Plat nomor kecil dan hanya terlihat jelas kalau truck dekat. Frame dipilih
dari yang bbox truck-nya paling besar, lalu di-crop dan diperbesar supaya
plat mudah dibaca.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
SHEET_DIR = PROJECT / "data" / "plate_sheets"
SHEET_DIR.mkdir(parents=True, exist_ok=True)


def area_truck(lbl: Path) -> float:
    if not lbl.exists():
        return 0.0
    best = 0.0
    for ln in lbl.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        cid, cx, cy, bw, bh = ln.split()
        if int(cid) == 1:
            best = max(best, float(bw) * float(bh))
    return best


kandidat = []
for split in ("train", "val"):
    for lbl in (OUT / "labels" / split).glob("*.txt"):
        a = area_truck(lbl)
        if a > 0.05:
            kandidat.append((a, split, lbl.stem))
kandidat.sort(reverse=True)
kandidat = kandidat[::3][:24]          # sebar, ambil 24
print(f"frame dengan truck besar: {len(kandidat)}")

GRID_W, GRID_H = 300, 533


def dengan_grid(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    canvas = np.full((GRID_H, GRID_W + 30, 3), 20, dtype=np.uint8)
    canvas[:, 30:] = cv2.resize(img, (GRID_W, GRID_H), interpolation=cv2.INTER_AREA)
    for u in range(0, 101, 10):
        x = int(u / 100 * GRID_W) + 30
        cv2.line(canvas, (x, 0), (x, GRID_H),
                 (0, 0, 255) if u % 50 == 0 else (85, 85, 85), 1)
        cv2.putText(canvas, str(u), (x - 8, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.32,
                    (255, 255, 255), 1)
    for v in range(0, 101, 10):
        y = int(v / 100 * GRID_H)
        cv2.line(canvas, (30, y), (30 + GRID_W, y),
                 (0, 0, 255) if v % 50 == 0 else (85, 85, 85), 1)
        cv2.putText(canvas, str(v), (1, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.32,
                    (255, 255, 255), 1)
    return canvas


PER_SHEET, COLS, ROWS = 6, 3, 2
for nomor in range(0, len(kandidat), PER_SHEET):
    bagian = kandidat[nomor:nomor + PER_SHEET]
    sel = []
    for i, (a, split, stem) in enumerate(bagian):
        img = cv2.imread(str(OUT / "images" / split / f"{stem}.jpg"))
        if img is None:
            continue
        sel.append((i, stem, dengan_grid(img)))
    if not sel:
        continue
    ch, cw = sel[0][2].shape[:2]
    sheet = np.full((ROWS * ch, COLS * cw, 3), 20, dtype=np.uint8)
    for k, (_, stem, im) in enumerate(sel):
        r, c = divmod(k, COLS)
        sheet[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = im
    ke = nomor // PER_SHEET + 1
    cv2.imwrite(str(SHEET_DIR / f"plat_{ke:02d}.jpg"), sheet,
                [cv2.IMWRITE_JPEG_QUALITY, 93])
    (SHEET_DIR / f"plat_{ke:02d}.txt").write_text(
        "\n".join(f"{i + 1}\t{stem}" for i, (_, stem, _) in enumerate(sel)),
        encoding="utf-8")
    print(f"  plat_{ke:02d}.jpg: " + ", ".join(s[-11:] for _, s, _ in sel))