"""Cek progres pelabelan bucket + Validasi dataset YOLO."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
OUT = PROJECT / "datasets" / "excavator"

SEMUA: list[tuple[Path, Path]] = []
for split in ("train", "val"):
    for img in sorted((OUT / "images" / split).glob("*.jpg")):
        SEMUA.append((split, OUT / "labels" / split / f"{img.stem}.txt"))

bucket_frame = 0
truck_frame = 0
kosong = 0
rusak: list[str] = []
kelas_hist: Counter = Counter()
bucket_kotak = 0
truck_kotak = 0
area_bucket: list[float] = []

for split, lbl in SEMUA:
    if not lbl.exists():
        kosong += 1
        continue
    isi = [ln for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not isi:
        kosong += 1
        continue
    ada_bucket = ada_truck = False
    for ln in isi:
        bagian = ln.split()
        if len(bagian) != 5:
            rusak.append(f"{lbl.name}: {ln}")
            continue
        try:
            cid = int(bagian[0])
            v = [float(x) for x in bagian[1:]]
        except ValueError:
            rusak.append(f"{lbl.name}: {ln}")
            continue
        kelas_hist[cid] += 1
        cx, cy, bw, bh = v
        if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < bw <= 1 and 0 < bh <= 1):
            rusak.append(f"{lbl.name}: di luar [0,1] -> {v}")
            continue
        if bw <= 0 or bh <= 0:
            rusak.append(f"{lbl.name}: ukuran nol -> {v}")
            continue
        if cx - bw / 2 < -0.001 or cx + bw / 2 > 1.001:
            rusak.append(f"{lbl.name}: kotak melewati tepi -> {v}")
        if cid == 0:
            ada_bucket = True
            bucket_kotak += 1
            area_bucket.append(bw * bh)
        elif cid == 1:
            ada_truck = True
            truck_kotak += 1
    bucket_frame += ada_bucket
    truck_frame += ada_truck

total = len(SEMUA)
print("=" * 62)
print("PROGRES PELABELAN BUCKET")
print("=" * 62)
print(f"total frame          : {total}")
print(f"frame berlabel bucket: {bucket_frame:4d}  ({bucket_frame / total * 100:.1f}%)")
print(f"frame berlabel truck : {truck_frame:4d}  ({truck_frame / total * 100:.1f}%)  <- otomatis COCO")
print(f"frame kosong         : {kosong:4d}")
print(f"kotak bucket         : {bucket_kotak}")
print(f"kotak truck          : {truck_kotak}")
print(f"distribusi kelas     : {dict(kelas_hist)}   (0=bucket 1=truck)")

if area_bucket:
    a = sorted(area_bucket)
    print(f"\nluas bucket (% frame): min {a[0] * 100:.1f}  "
          f"median {a[len(a) // 2] * 100:.1f}  maks {a[-1] * 100:.1f}")

print(f"\nlabel rusak          : {len(rusak)}")
for r in rusak[:10]:
    print(f"   {r}")

siap = bucket_frame >= 150 and not rusak
print("\n" + ("SIAP DILATIH: label bucket >= 150 frame, tidak ada format rusak"
              if siap else
              f"BELUM SIAP: butuh >=150 frame berlabel bucket "
              f"(sekarang {bucket_frame})"))