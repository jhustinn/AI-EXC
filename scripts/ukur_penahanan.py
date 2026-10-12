"""Ukur dampak penahanan kotak: frame kosong sebelum vs sesudah."""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402

from excavator.config import load_config  # noqa: E402
from excavator.detector import Detector  # noqa: E402

VIDEO = PROJECT / "INGIN SEPERTI INI" / "WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4"

print(f"{'video':<30}{'kosong tanpa':>14}{'kosong dengan':>15}"
      f"{'terdeteksi':>11}{'ditahan':>9}")
print("=" * 80)

for p in sorted((PROJECT / "INGIN SEPERTI INI").glob("*.mp4")):
    baris = {}
    for mode in ("tanpa", "dengan"):
        cfg = load_config(PROJECT / "config.excavator.yaml")
        if mode == "tanpa":
            cfg.detector.hold_seconds = 0.0
            cfg.detector.release_confidence = cfg.detector.confidence
        det = Detector(cfg.detector, cfg.zones, PROJECT)

        cap = cv2.VideoCapture(str(p))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        kosong = ditahan = n = 0
        for idx in range(0, total, 3):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                break
            r = det.detect(frame)
            if not r.trucks:
                kosong += 1
            if r.ditahan:
                ditahan += 1
            n += 1
        cap.release()
        baris[mode] = (kosong, ditahan, n)

    a, b = baris["tanpa"], baris["dengan"]
    nama = p.stem[-26:]
    terdeteksi = 100 - b[1] / b[2] * 100
    ditahan = 100 - terdeteksi
    print(f"{nama:<30}{a[0]:>8}/{a[2]:<5}{b[0]:>9}/{b[2]:<5}"
          f"{terdeteksi:>10.1f}%{ditahan:>8.1f}%")

print()
print("kosong tanpa   = frame tanpa truck sebelum penahanan")
print("kosong dengan  = frame tanpa truck sesudah penahanan")
print("terdeteksi     = frame dengan deteksi asli (conf >= 0,35)")
print("ditahan        = frame yang kotaknya bukan deteksi frame itu")