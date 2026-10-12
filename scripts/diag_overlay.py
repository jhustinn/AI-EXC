"""Kenapa sebagian orang tidak mendapat label di overlay?

Bandingkan jumlah deteksi YOLO vs skeleton yang diterima pipeline
(syarat: in_box_ratio, valid_count, validate_limbs).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from presence.config import load_config  # noqa: E402
from presence.pose import Skeleton, clip_to_bbox, validate_skeleton  # noqa: E402

NAMES = ["nose", "eye_l", "eye_r", "ear_l", "ear_r", "sh_l", "sh_r", "el_l", "el_r",
         "wr_l", "wr_r", "hip_l", "hip_r", "knee_l", "knee_r", "ank_l", "ank_r"]


def main() -> int:
    camera_id = sys.argv[1] if len(sys.argv) > 1 else "cctv-4"
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 200

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

    pc = cfg.pose
    print(f"kamera {camera_id}   ambang: min_inbox_ratio={pc.min_inbox_ratio} "
          f"min_keypoints={pc.min_keypoints} draw_min_keypoints={pc.draw_min_keypoints} "
          f"keypoint_conf={pc.keypoint_confidence}")
    print("-" * 70)

    det_count = 0
    accepted = 0
    reject_box = 0
    reject_valid = 0
    inbox_ratios: list[float] = []
    valid_counts: list[int] = []
    per_frame_det = Counter()
    per_frame_ok = Counter()

    for _ in range(frames):
        ok, frame = cap.read()
        if not ok:
            break
        res = model.predict(frame, conf=cfg.detection.confidence, device="0", verbose=False)[0]
        boxes = res.boxes
        if boxes is None or len(boxes) == 0:
            continue
        n_det = len(boxes)
        per_frame_det[n_det] += 1
        kps = res.keypoints.data if res.keypoints is not None else None
        if kps is None:
            continue

        for i in range(n_det):
            det_count += 1
            arr = kps[i].detach().cpu().numpy()
            bbox = boxes.xyxy[i].detach().cpu().numpy()
            skel = Skeleton(keypoints=np.asarray(arr, dtype=np.float32), score=float(boxes.conf[i]))
            clipped, ratio = clip_to_bbox(skel, bbox, pc.bbox_margin)
            inbox_ratios.append(ratio)
            valid_counts.append(clipped.valid_count(pc.keypoint_confidence))
            if pc.validate_limbs:
                clipped = validate_skeleton(
                    clipped,
                    min_conf=pc.keypoint_confidence,
                    limb_ratio_range=(pc.limb_ratio_min, pc.limb_ratio_max),
                )
            if ratio < pc.min_inbox_ratio:
                reject_box += 1
                continue
            if clipped.valid_count(pc.keypoint_confidence) < pc.draw_min_keypoints:
                reject_valid += 1
                continue
            accepted += 1
            per_frame_ok[1] += 1

    cap.release()
    print(f"frame diproses     : {frames}")
    print(f"total deteksi orang: {det_count}")
    print(f"diterima (ada label): {accepted}")
    print(f"  ditolak in_box_ratio < {pc.min_inbox_ratio}: {reject_box}")
    print(f"  ditolak valid_count < {pc.draw_min_keypoints}: {reject_valid}")
    if inbox_ratios:
        arr = np.array(inbox_ratios)
        print(f"\nin_box_ratio: median={np.median(arr):.2f} min={arr.min():.2f} max={arr.max():.2f}")
        print(f"  kurva     : p10={np.percentile(arr, 10):.2f} p25={np.percentile(arr, 25):.2f} "
              f"p50={np.percentile(arr, 50):.2f}")
    if valid_counts:
        arr = np.array(valid_counts)
        print(f"valid_count : median={np.median(arr):.0f} min={arr.min()} max={arr.max()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())