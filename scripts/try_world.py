"""Coba deteksi bucket tanpa training pakai YOLO-World (open-vocabulary).

Kalau berhasil, labelan awal bisa dibuat otomatis dan hanya perlu
dikoreksi manusia - jauh lebih cepat daripada menggambar dari nol.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402

SRC = PROJECT / "INGIN SEPERTI INI"
KELAS = ["bucket", "excavator", "dump truck", "arm"]

try:
    from ultralytics import YOLO
except Exception as exc:  # noqa: BLE001
    print("gagal import ultralytics:", exc)
    sys.exit(1)

print("memuat YOLO-World (unduh sekali, ~25 MB)...")
try:
    model = YOLO("yolov8s-worldv2.pt")
except Exception as exc:  # noqa: BLE001
    print("YOLO-World tidak tersedia:", type(exc).__name__, exc)
    sys.exit(1)

try:
    model.set_classes(KELAS)
    print(f"kelas terbuka: {KELAS}")
except Exception as exc:  # noqa: BLE001
    print("set_classes gagal:", exc)
    sys.exit(1)

from collections import Counter

grand = Counter()

for path in sorted(SRC.glob("*.mp4")):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        continue
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total // 25)
    per = Counter()
    best: dict[str, float] = {}
    for idx in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        res = model.predict(frame, conf=0.20, device="0", verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            continue
        for cid, cf in zip(res.boxes.cls.cpu().numpy(), res.boxes.conf.cpu().numpy()):
            nm = KELAS[int(cid)]
            per[nm] += 1
            grand[nm] += 1
            if float(cf) > best.get(nm, 0.0):
                best[nm] = float(cf)
    cap.release()
    print(f"\n{path.name}")
    if per:
        for nm, c in per.most_common():
            print(f"   {nm:14s} {c:3d}  conf tertinggi {best.get(nm, 0):.2f}")
    else:
        print("   tidak ada yang terdeteksi")

print("\nTOTAL:")
for nm, c in grand.most_common():
    print(f"   {nm:14s} {c}")