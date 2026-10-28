"""Latih model komponen ekskavator (arm, boom, bucket) dari dataset Roboflow baru."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

from ultralytics import YOLO

DATA = PROJECT / "data" / "unduhan" / "excavator_sotii" / "data.yaml"
RUN_DIR = PROJECT / "runs" / "excavator_parts"

# Pastikan path absolut di data.yaml agar YOLO tidak salah membaca direktori
data_yaml_content = f"""path: {PROJECT.as_posix()}/data/unduhan/excavator_sotii
train: train/images
val: valid/images
test: test/images

nc: 3
names: ['arm', 'boom', 'bucket']
"""
DATA.write_text(data_yaml_content, encoding="utf-8")
print(f"data.yaml disiapkan di: {DATA}")

model = YOLO(str(PROJECT / "yolov8n.pt"))

print("Memulai training komponen ekskavator (arm, boom, bucket) pada NVIDIA GTX 1650...")
model.train(
    data=str(DATA),
    epochs=35,
    imgsz=640,
    batch=8,
    device=0,
    workers=0,
    project=str(PROJECT / "runs"),
    name="excavator_parts",
    exist_ok=True,
    seed=42,
    patience=10,
    verbose=True,
)

print()
print("=" * 60)
print("VALIDASI AKURASI MODEL HASIL TRAINING")
print("=" * 60)
r = model.val(data=str(DATA), split="val", workers=0, imgsz=640, batch=8, verbose=False)
for i, name in enumerate(['arm', 'boom', 'bucket']):
    p = float(r.box.p[i])
    rc = float(r.box.r[i])
    ap50 = float(r.box.ap50[i])
    ap = float(r.box.ap[i])
    print(f"  {name:10s} | Precision: {p:.3f} | Recall: {rc:.3f} | mAP50: {ap50:.3f} | mAP50-95: {ap:.3f}")

print(f"\nModel tersimpan di: {RUN_DIR / 'weights' / 'best.pt'}")
