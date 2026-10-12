"""Ukur distribusi energi gerak per video, untuk deciding ambang yang jujur."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from excavator.config import load_config  # noqa: E402
from excavator.detector import Detector  # noqa: E402

VIDEO_DIR = PROJECT / "INGIN SEPERTI INI"
cfg = load_config(PROJECT / "config.excavator.yaml")
det = Detector(cfg.detector, cfg.zones, PROJECT)

print("Distribusi energi gerak di zona gali (semua frame, tiap 3 frame)")
print("=" * 78)
print(f"{'video':<32}{'min':>8}{'p25':>8}{'median':>8}{'p75':>8}{'maks':>8}{'truck%':>9}")
print("=" * 78)

for p in sorted(VIDEO_DIR.glob("*.mp4")):
    cap = cv2.VideoCapture(str(p))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    gerak: list[float] = []
    ada_truck = 0
    n = 0
    for idx in range(0, total, 3):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        hasil = det.detect(frame)
        gerak.append(hasil.dig_motion)
        if hasil.trucks:
            ada_truck += 1
        n += 1
    cap.release()

    a = np.array(gerak)
    print(f"{p.stem[-28:]:<32}{a.min():>8.4f}{np.percentile(a,25):>8.4f}"
          f"{np.median(a):>8.4f}{np.percentile(a,75):>8.4f}{a.max():>8.4f}"
          f"{ada_truck/n*100:>8.0f}%")

print("=" * 78)
print("Bacalah: bila min dan median jauh, sinyal ada Discrimination.")
print("Bila semuanya rapat (mis 0.05-0.08), ambang apa pun tidak akan")
print("membedakan mengguk dari diam, jadi ambang tidak boleh dipalsukan.")