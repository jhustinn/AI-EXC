"""Statistik klasifikasi postur dari kamera nyata.

    .venv\\Scripts\\python.exe scripts\\diag_posture_stat.py cctv-2 [durasi_detik]
"""
from __future__ import annotations

import statistics
from dataclasses import replace
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from presence.config import load_config  # noqa: E402
from presence.pose import KNEE_SITTING_ANGLE, KNEE_STANDING_ANGLE, Skeleton  # noqa: E402


def angle(a, v, b) -> float:
    va, vb = a[:2] - v[:2], b[:2] - v[:2]
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na < 1e-6 or nb < 1e-6:
        return float("nan")
    cos = float(np.clip(np.dot(va, vb) / (na * nb), -1.0, 1.0))
    return float(np.degrees(np.arccos(cos)))


def main() -> int:
    camera_id = sys.argv[1] if len(sys.argv) > 1 else "cctv-2"
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 40.0
    subtype = sys.argv[3] if len(sys.argv) > 3 else None  # 0 = main 1080p, 1 = sub 576p
    kp_conf = float(sys.argv[4]) if len(sys.argv) > 4 else None

    cfg = load_config("config.cctv.yaml")
    ch = next((c for c in cfg.channels if c.id == camera_id), None)
    if ch is None:
        print(f"kamera '{camera_id}' tidak ada")
        return 2

    source = str(ch.source)
    if subtype is not None:
        source = source.replace("subtype=1", f"subtype={subtype}")

    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
    if not cap.isOpened():
        print("gagal membuka stream")
        return 2
    actual = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"

    pc = cfg.pose
    if kp_conf is not None:
        pc = replace(pc, keypoint_confidence=kp_conf)
    print(f"kamera {camera_id}  {actual}  ({duration:.0f} detik sampling)")
    print(
        f"ambang: sitting_knee_ratio={pc.sitting_knee_ratio} "
        f"standing_knee_ratio={pc.standing_knee_ratio} "
        f"KNEE_SITTING={KNEE_SITTING_ANGLE} KNEE_STANDING={KNEE_STANDING_ANGLE} "
        f"keypoint_conf={pc.keypoint_confidence} ankle_conf={pc.ankle_confidence}"
    )
    print("-" * 74)

    drops, angles, labels = [], [], []
    ank_conf_seen, labels_no_guard = [], []
    tilts = []
    end = time.time() + duration
    frames = 0
    while time.time() < end:
        ok, frame = cap.read()
        if not ok:
            break
        frames += 1
        for r in model.predict(frame, conf=0.4, device="0", verbose=False):
            kps = getattr(r, "keypoints", None)
            if kps is None or kps.data is None:
                continue
            for person in kps.data:
                arr = person.detach().cpu().numpy()
                skel = Skeleton(keypoints=arr, score=1.0)
                if skel.valid_count(pc.keypoint_confidence) < 8:
                    continue
                k = arr
                sh_mid = np.mean([k[5, :2], k[6, :2]], axis=0)
                hip_mid = np.mean([k[11, :2], k[12, :2]], axis=0)
                torso = abs(float(sh_mid[1] - hip_mid[1]))
                if torso < 1e-3:
                    continue

                # sudut batang badan terhadap vertikal (0 = tegak)
                if all(k[i, 2] >= pc.keypoint_confidence for i in (5, 6, 11, 12)):
                    vx = float(sh_mid[0] - hip_mid[0])
                    vy = float(sh_mid[1] - hip_mid[1])
                    if abs(vx) > 1e-3 or abs(vy) > 1e-3:
                        cos_t = abs(vy) / (float(np.hypot(vx, vy)) or 1e-6)
                        tilts.append(float(np.degrees(np.arccos(min(1.0, cos_t)))))

                if all(k[i, 2] >= pc.keypoint_confidence for i in (13, 14)):
                    knee_y = float(np.mean([k[13, 1], k[14, 1]]))
                    drops.append(abs(knee_y - float(hip_mid[1])) / torso)

                angs = []
                for i in (0, 1):
                    if all(k[j, 2] >= pc.keypoint_confidence for j in (11 + i, 13 + i, 15 + i)):
                        angs.append(angle(k[11 + i], k[13 + i], k[15 + i]))
                angs = [a for a in angs if not np.isnan(a)]
                if angs:
                    angles.append(float(np.median(angs)))

                ank_conf_seen.extend([float(k[15, 2]), float(k[16, 2])])
                labels.append(skel.posture(
                    min_conf=pc.keypoint_confidence,
                    sitting_knee_ratio=pc.sitting_knee_ratio,
                    standing_knee_ratio=pc.standing_knee_ratio,
                    min_keypoints=pc.min_keypoints,
                    ankle_conf=pc.ankle_confidence,
                ))
                # versi tanpa pengaman mata kaki, untuk perbandingan
                labels_no_guard.append(skel.posture(
                    min_conf=pc.keypoint_confidence,
                    sitting_knee_ratio=pc.sitting_knee_ratio,
                    standing_knee_ratio=pc.standing_knee_ratio,
                    min_keypoints=pc.min_keypoints,
                ))

    cap.release()

    def dist(vals):
        if not vals:
            return "(tidak ada)"
        c: dict[str, int] = {}
        for v in vals:
            c[v] = c.get(v, 0) + 1
        n = len(vals)
        return "  ".join(f"{k}={v} ({v * 100 // n}%)" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))

    def stat(vals, name):
        if not vals:
            return f"  {name}: (tidak ada)"
        return (
            f"  {name}: median={statistics.median(vals):.2f} "
            f"min={min(vals):.2f} max={max(vals):.2f} n={len(vals)}"
        )

    print(f"frame diproses: {frames}, sampel orang: {len(labels)}")
    print()
    print(f"label DENGAN ankle_conf={pc.ankle_confidence}: {dist(labels)}")
    print(f"label TANPA pengaman mata kaki          : {dist(labels_no_guard)}")
    print()
    print(stat(drops, "knee_drop"))
    print("    DUDUK bila <", pc.sitting_knee_ratio, "| BEDIRI bila >=", pc.standing_knee_ratio)
    print(stat(angles, "knee_angle"))
    print("    DUDUK bila <", KNEE_SITTING_ANGLE, "| BEDIRI bila >", KNEE_STANDING_ANGLE)
    print(stat(ank_conf_seen, "keypoint conf mata kaki"))
    print("    (ambang ankle_conf =", pc.ankle_confidence, ")")
    print(stat(tilts, "sudut batang badan vs vertikal"))
    print("    0-15 tegak, 15-30 condong, >30 bersandar")
    return 0


if __name__ == "__main__":
    sys.exit(main())