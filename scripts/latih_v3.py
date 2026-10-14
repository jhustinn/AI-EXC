"""Latih model alat berat dari dataset gabungan (publik + manual)."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

from ultralytics import YOLO  # noqa: E402

DATA = PROJECT / "datasets" / "alat_berat" / "data.yaml"
RUN = PROJECT / "runs" / "alat_berat_v3"

model = YOLO(str(PROJECT / "yolov8n.pt"))
model.train(
    data=str(DATA),
    epochs=40,
    # GTX 1650 hanya punya 4 GB VRAM. imgsz 768 dengan batch 12 terlalu
    # berat. 640 dengan batch 8 aman dan cukup untuk ukuran objek ini.
    imgsz=640,
    batch=8,
    device=0,
    workers=0,
    project=str(PROJECT / "runs"),
    name="alat_berat_v3",
    exist_ok=True,
    seed=0,
    patience=15,
    hsv_v=0.3, hsv_s=0.4,
    degrees=10, translate=0.1, scale=0.4, fliplr=0.5,
    mosaic=0.5,
)

print()
print("=" * 66)
print("AKURASI PER KELAS")
print("=" * 66)
r = model.val(data=str(DATA), split="val", workers=0, imgsz=640,
              batch=8, verbose=False)
nama = list(model.names.values())
for i, n in enumerate(nama):
    print(f"  {n:12s} precision={float(r.box.p[i]):.3f}  "
          f"recall={float(r.box.r[i]):.3f}  "
          f"mAP50={float(r.box.ap50[i]):.3f}  mAP50-95={float(r.box.ap[i]):.3f}")
print()
print(f"  {'RATA-RATA':12s} mAP50={float(r.box.map50):.3f}  "
      f"mAP50-95={float(r.box.map):.3f}")
print()
print("terbaik:", RUN / "weights" / "best.pt")