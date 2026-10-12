"""Laporan akurasi per kelas untuk model alat berat."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

from ultralytics import YOLO  # noqa: E402

BEST = PROJECT / "runs" / "alat_berat_v1" / "weights" / "best.pt"
DATA = PROJECT / "datasets" / "excavator" / "data.yaml"

model = YOLO(str(BEST))
# workers harus 0 di Windows, kalau tidak DataLoader gagal spawn
r = model.val(data=str(DATA), split="val", workers=0, imgsz=640,
               batch=4, verbose=False)

print()
print("=" * 62)
print("AKURASI PER KELAS (validasi)")
print("=" * 62)
print("peringatan: hanya 6 frame validasi berlabel manual, jadi angka ini")
print("sangat berfluktuasi dan belum layak dipakai sebagai tolok ukur.")
print()
nama = list(model.names.values())
for i, n in enumerate(nama):
    print(f"  {n:12s} precision={float(r.box.p[i]):.3f}  "
          f"mAP50={float(r.box.ap50[i]):.3f}  mAP50-95={float(r.box.ap[i]):.3f}")
print()
print(f"  {'RATA-RATA':12s} mAP50={float(r.box.map50):.3f}  "
      f"mAP50-95={float(r.box.map):.3f}")