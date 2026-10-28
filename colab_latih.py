# ============================================================
#  CELL 1 - Colab siap + pasang ultralytics
# ============================================================
!nvidia-smi --query-gpu=name,memory.total --format=csv
!pip install -q ultralytics==8.4.173
from ultralytics import YOLO
print("ultralytics siap")

# ============================================================
#  CELL 2 - unggah dataset  (220 MB)
#  Klik ikon folder di atas, lalu upload: datasets/alat_berat.zip
#  Setelah selesai, variabel ini harus terisi:
# ============================================================
import os
ZIP = next((os.path.join("/content", f) for f in os.listdir("/content")
            if f.endswith(".zip")), None)
assert ZIP, "ZIP belum ada. Upload datasets/alat_berat.zip ke /content dulu."
print("ditemukan:", ZIP)

# ============================================================
#  CELL 3 - ekstrak + sesuaikan path Linux + sanity check
# ============================================================
!unzip -q -o "{ZIP}" -d /content/dataset

# Sesuaikan path data.yaml dari path Windows lokal ke path Linux Colab
yaml_colab = """path: /content/dataset/alat_berat
train: images/train
val: images/val

nc: 3
names:
  0: excavator
  1: truck
  2: bucket
"""
with open("/content/dataset/alat_berat/data.yaml", "w") as f:
    f.write(yaml_colab.strip())

print("data.yaml disesuaikan untuk Colab:")
print(open("/content/dataset/alat_berat/data.yaml").read())

from collections import Counter
c = Counter()
import glob
for f in glob.glob("/content/dataset/alat_berat/labels/**/*.txt", recursive=True):
    for ln in open(f):
        if ln.strip():
            c[ln.split()[0]] += 1
print("\nkelas di label:", dict(sorted(c.items())))
assert set(c) <= {"0", "1", "2"}, "ADA KELAS ASING - jangan dilatih!"

# ============================================================
#  CELL 4 - latih
#  3 kelas: excavator / truck / bucket.  imgsz 640 dijaga:
#  bucket median hanya 7,1% luas frame, lowering hurts.
# ============================================================
DATA = "/content/dataset/alat_berat/data.yaml"
model = YOLO("yolov8n.pt")
model.train(data=DATA, epochs=40, imgsz=640, batch=16,
            patience=15, workers=2, device=0,
            project="/content/runs", name="alat_berat_v4")

# ============================================================
#  CELL 5 - ukur mAP per kelas
# ============================================================
m = YOLO("/content/runs/alat_berat_v4/weights/best.pt")
r = m.val(data=DATA, split="val", workers=2, imgsz=640, batch=16, verbose=False)
print("=" * 52)
for i, n in m.names.items():
    print(f"  {n:12s} mAP50={float(r.box.ap50[i]):.3f}  mAP50-95={float(r.box.ap[i]):.3f}")

# ============================================================
#  CELL 6 - kirim balik ke komputer ini
#  Hasilnya: /content/alat_berat_v4_best.zip  (kecil, ~6 MB)
# ============================================================
import shutil
shutil.copy("/content/runs/alat_berat_v4/weights/best.pt", "/content/best.pt")
!zip -j /content/alat_berat_v4_best.zip /content/best.pt
import os
print("size:", round(os.path.getsize("/content/alat_berat_v4_best.zip")/1e6, 1), "MB")
from google.colab import files
files.download("/content/alat_berat_v4_best.zip")

