"""Kenapa orang di dalam ROI tidak ter-assign ke meja?

Menggunakan fungsi penugasan asli (candidate_desks) agar angkanya sama
dengan yang dipakai recorder.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from presence.config import load_config  # noqa: E402
from presence.detector import Detection, candidate_desks  # noqa: E402


def iou_geometry(bbox, roi_rel, shape):
    h, w = shape[:2]
    x1, y1, x2, y2 = bbox
    rx1, ry1 = roi_rel[0] * w, roi_rel[1] * h
    rx2, ry2 = roi_rel[2] * w, roi_rel[3] * h
    ix1, iy1 = max(x1, rx1), max(y1, ry1)
    ix2, iy2 = min(x2, rx2), min(y2, ry2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area = max(1.0, (x2 - x1) * (y2 - y1))
    desk_area = max(1.0, (rx2 - rx1) * (ry2 - ry1))
    return inter / area, inter / desk_area, (rx1, ry1, rx2, ry2)


def main() -> int:
    camera_id = sys.argv[1] if len(sys.argv) > 1 else "cctv-4"
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    cfg = load_config("config.cctv.yaml")
    ch = next((c for c in cfg.channels if c.id == camera_id), None)
    if ch is None:
        print(f"kamera '{camera_id}' tidak ada")
        return 2
    if not ch.desks:
        print(f"{camera_id} tidak punya ROI meja")
        return 2

    desk_tuples = [(d.id, d.label, d.roi) for d in ch.desks]
    min_ratio = cfg.presence.desk_overlap_ratio
    print(f"kamera {camera_id}   desk_overlap_ratio={min_ratio}")
    for did, label, roi in desk_tuples:
        print(f"  {label}: {roi}")
    print("-" * 72)

    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(str(ch.source), cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
    if not cap.isOpened():
        print("gagal membuka stream")
        return 2

    shown = 0
    for _ in range(frames):
        ok, frame = cap.read()
        if not ok:
            break
        res = model.predict(frame, conf=cfg.detection.confidence, device="0", verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            continue
        xyxy = res.boxes.xyxy.detach().cpu().numpy()
        kps = res.keypoints.data.detach().cpu().numpy() if res.keypoints is not None else None

        for i, bbox in enumerate(xyxy):
            anchor = None
            if kps is not None:
                k = kps[i]
                sel = [k[5], k[6], k[11], k[12]]
                sel = [p for p in sel if p[2] >= cfg.pose.keypoint_confidence]
                if sel:
                    anchor = (
                        float(np.mean([p[0] for p in sel])),
                        float(np.mean([p[1] for p in sel])),
                    )
            det = Detection(
                bbox=tuple(float(v) for v in bbox),
                track_id=i,
                conf=float(res.boxes.conf[i]),
                keypoints=None,
            )
            cands = candidate_desks(det, desk_tuples, frame.shape, min_ratio, anchor=anchor)

            print(f"\norang #{i}  bbox=({bbox[0]:.0f},{bbox[1]:.0f})-({bbox[2]:.0f},{bbox[3]:.0f})"
                  f"  conf={float(res.boxes.conf[i]):.2f}")
            print(f"  anchor(torso)={None if anchor is None else (round(anchor[0]), round(anchor[1]))}")
            for did, label, roi in desk_tuples:
                rp, rd, rect = iou_geometry(bbox, roi, frame.shape)
                rx1, ry1, rx2, ry2 = rect
                inside_anchor = anchor is not None and rx1 <= anchor[0] <= rx2 and ry1 <= anchor[1] <= ry2
                cx, cy = det.center
                inside_center = rx1 <= cx <= rx2 and ry1 <= cy <= ry2
                print(
                    f"  {label:7s} rasio_orang={rp:.2f} rasio_meja={rd:.2f} "
                    f"anchor_di_dalam={inside_anchor} pusat_di_dalam={inside_center}"
                    f"  (butuh rasio_orang>={min_ratio})"
                )
            print(f"  -> kandidat: {[(c[1], round(c[0], 2)) for c in cands] or 'TIDAK ADA'}")
            shown += 1
            if shown >= 4:
                cap.release()
                return 0

    cap.release()
    if shown == 0:
        print("tidak ada orang terdeteksi")
    return 0


if __name__ == "__main__":
    sys.exit(main())