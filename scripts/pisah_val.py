"""Pindahkan sebagian frame berlabel ke val agar mAP bisa diukur.

Tanpa ini semua 35 frame berlabel ada di train dan kelas bucket/excavator
tidak punya data validasi sama sekali - mAP-nya tidak bisa dipercaya.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
OUT = PROJECT / "datasets" / "excavator"

# 7 dari 35 = 20% untuk validasi
KE_VAL = 7

terlabel: list[str] = []
for lbl in sorted((OUT / "labels" / "train").glob("*.txt")):
    isi = [ln for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if any(int(ln.split()[0]) in (0, 2) for ln in isi):
        terlabel.append(lbl.stem)

print(f"frame berlabel di train: {len(terlabel)}")
dipindah = terlabel[::5][:KE_VAL]      # sebar, bukan beruntun

for stem in dipindah:
    src_img = OUT / "images" / "train" / f"{stem}.jpg"
    src_lbl = OUT / "labels" / "train" / f"{stem}.txt"
    dst_img = OUT / "images" / "val" / f"{stem}.jpg"
    dst_lbl = OUT / "labels" / "val" / f"{stem}.txt"
    if not src_img.exists():
        continue
    shutil.move(str(src_img), str(dst_img))
    if src_lbl.exists():
        shutil.move(str(src_lbl), str(dst_lbl))
    print(f"  -> val: {stem}")

def hitung(split: str) -> tuple[int, int, int]:
    b = e = n = 0
    for lbl in (OUT / "labels" / split).glob("*.txt"):
        isi = [ln for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ids = {int(ln.split()[0]) for ln in isi}
        n += 1
        if 0 in ids:
            b += 1
        if 2 in ids:
            e += 1
    return n, b, e

for s in ("train", "val"):
    n, b, e = hitung(s)
    print(f"{s:5s}: {n:3d} frame | berlabel bucket {b:3d} | excavator {e:3d}")