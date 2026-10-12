"""Uji sensitivitas ambang deteksi pada orang yang membungkung.

    .venv\\Scripts\\python.exe scripts\\diag_det_conf.py cctv-4 [jumlah_frame]
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from presence.config import load_config  # noqa: E402


def main() -> int:
    camera_id = sys.argv[1] if len(sys.argv) > 1 else "cctv-4"
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 80

    cfg = load_config("config.cctv.yaml")
    ch = next((c for c in cfg.channels if c.id == camera_id), None)
    if ch is None:
        print(f"kamera '{camera_id}' tidak ada")
        return 2

    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(str(ch.source), cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
    if not cap.isOpened():
        print("gagal membuka stream")
        return 2

    # kumpulkan skor mentah sekali saja, lalu hitung untuk tiap ambang
    confs: list[float] = []
    n_frames = 0
    for _ in range(frames):
        ok, frame = cap.read()
        if not ok:
            break
        n_frames += 1
        res = model.predict(frame, conf=0.01, device="0", verbose=False)[0]
        if res.boxes is None:
            continue
        for c in res.boxes.conf.detach().cpu().numpy():
            if float(c) >= 0.05:  # abaikan noise sangat rendah
                confs.append(float(c))
    cap.release()

    arr = np.array(confs) if confs else np.array([])
    print(f"kamera {camera_id}: {n_frames} frame, {len(arr)} deteksi (conf >= 0.05)")
    if arr.size == 0:
        print("TIDAK ADA deteksi sama sekali - masalah lebih besar dari ambang")
        return 0
    print()
    for thr in (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6):
        n = int((arr >= thr).sum())
        per_frame = n / max(1, n_frames)
        flag = "  <-- config sekarang" if abs(thr - cfg.detection.confidence) < 1e-9 else ""
        print(f"  conf>={thr:.2f}: {n:4d} deteksi  ({per_frame:.2f}/frame){flag}")
    print()
    print(f"skor tertinggi: {arr.max():.3f}   median: {np.median(arr):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())