"""Siapkan dataset deteksi bucket dari 4 video referensi.

Langkah:
  1. ambil frame dengan jarak cukup agar tidak banyak duplikat
  2. label otomatis kelas 'truck' memakai YOLO COCO (sudah andal: conf 0,86-0,95)
  3. 'bucket' sengaja dikosongkan - itu yang harus digambar manusia
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from ultralytics import YOLO  # noqa: E402

SRC = PROJECT / "INGIN SEPERTI INI"
OUT = PROJECT / "datasets" / "excavator"

# bersihkan isi lama supaya tidak tertinggal file dari build sebelumnya
for split in ("train", "val"):
    for folder in (OUT / "images" / split, OUT / "labels" / split):
        for old in folder.glob("*"):
            if old.is_file():
                old.unlink()
    (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

# yolov8n.pt sudah dilatih COCO yang memuat kelas 'truck'
detector = YOLO(str(PROJECT / "yolov8n.pt"))
COCO = detector.names
TRUCK_IDS = {i for i, n in COCO.items() if n in ("truck", "trailer truck", "bus")}
print(f"kelas COCO untuk truck: {sorted(COCO[i] for i in TRUCK_IDS)}")

FPS_SAMPLE = 1.5          # frame per detik dari video
MIN_IOU_UNIQUE = 0.90     # buang frame yang mirip frame sebelumnya

records: list[dict] = []
dupe_dropped = 0
truck_found = 0

for vno, path in enumerate(sorted(SRC.glob("*.mp4")), start=1):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"{path.name}: gagal dibuka")
        continue

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(fps / FPS_SAMPLE))
    # nomor video WAJIB ada di nama file, kalau tidak frame antar video
    # saling menimpa karena stempel waktunya mirip
    stem = f"v{vno}_{path.stem.replace('WhatsApp Video ', '').replace(' ', '_')[:16]}"

    prev_small: np.ndarray | None = None
    idx = 0
    saved = 0

    while idx < total:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        idx += step

        small = cv2.cvtColor(cv2.resize(frame, (64, 114)), cv2.COLOR_BGR2GRAY)
        if prev_small is not None:
            # jumlah piksel yang berubah drastis -> penanda gerakan / adegan baru
            changed = cv2.countNonZero(cv2.absdiff(small, prev_small))
            if changed < small.size * 0.03:
                dupe_dropped += 1
                continue
        prev_small = small

        h, w = frame.shape[:2]

        # --- label otomatis: truck ---
        boxes: list[list[float]] = []
        names: list[int] = []
        res = detector.predict(frame, conf=0.35, iou=0.5, device="0", verbose=False)[0]
        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy()
            conf = res.boxes.conf.cpu().numpy()
            for b, c, cf in zip(xyxy, cls, conf):
                if int(c) not in TRUCK_IDS:
                    continue
                x1, y1, x2, y2 = [float(v) for v in b]
                # hanya truck besar & dekat (yang jadi target tuang)
                if (x2 - x1) < w * 0.15:
                    continue
                cx = ((x1 + x2) / 2) / w
                cy = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                if bw <= 0 or bh <= 0:
                    continue
                boxes.append([cx, cy, bw, bh])
                names.append(1)          # kelas 1 = truck
                truck_found += 1

        split = "val" if saved % 5 == 4 else "train"
        fname = f"{stem}_{idx:05d}.jpg"
        cv2.imwrite(str(OUT / "images" / split / fname), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])

        label_txt = OUT / "labels" / split / f"{Path(fname).stem}.txt"
        with label_txt.open("w", encoding="utf-8") as fh:
            for name_id, bb in zip(names, boxes):
                fh.write(f"{name_id} {bb[0]:.6f} {bb[1]:.6f} {bb[2]:.6f} {bb[3]:.6f}\n")

        records.append({
            "file": f"images/{split}/{fname}",
            "video": path.name,
            "frame": idx,
            "truck": len(boxes),
        })
        saved += 1

    cap.release()
    print(f"  {path.name}: {saved} frame diambil")

(OUT / "data.yaml").write_text(
    "# Dataset deteksi bucket alat berat\n"
    "path: E:/App/AI-CCTV/datasets/excavator\n"
    "train: images/train\n"
    "val: images/val\n"
    "\n"
    "nc: 2\n"
    "names:\n"
    "  0: bucket\n"
    "  1: truck\n",
    encoding="utf-8",
)

(OUT / "manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

n_train = sum(1 for r in records if "/train/" in r["file"])
n_val = len(records) - n_train
print("=" * 60)
print(f"total frame   : {len(records)}   (train {n_train} / val {n_val})")
print(f"duplikat dibuang: {dupe_dropped}")
print(f"kotak truck otomatis: {truck_found} pada {sum(1 for r in records if r['truck'])} frame")
print(f"bucket        : 0  <- INI YANG PERLU DIGAMBAR MANUSIA")
print(f"lokasi        : {OUT}")