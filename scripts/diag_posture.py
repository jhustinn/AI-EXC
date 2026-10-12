"""Diagnosa klasifikasi postur: tampilkan nilai mentah yang menentukan DUDUK/BEDIRI.

Jalankan:
    .venv\\Scripts\\python.exe scripts\\diag_posture.py cctv-2 [jumlah_frame]
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from presence.config import load_config  # noqa: E402
from presence.pose import (  # noqa: E402
    KNEE_SITTING_ANGLE,
    KNEE_STANDING_ANGLE,
    Skeleton,
)

NAMES = [
    "nose", "eye_l", "eye_r", "ear_l", "ear_r",
    "shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "wrist_l", "wrist_r",
    "hip_l", "hip_r", "knee_l", "knee_r", "ankle_l", "ankle_r",
]


def angle(a, v, b) -> float:
    va = a[:2] - v[:2]
    vb = b[:2] - v[:2]
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na < 1e-6 or nb < 1e-6:
        return float("nan")
    cos = float(np.clip(np.dot(va, vb) / (na * nb), -1.0, 1.0))
    return float(np.degrees(np.arccos(cos)))


def main() -> int:
    camera_id = sys.argv[1] if len(sys.argv) > 1 else "cctv-2"
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 120

    cfg = load_config("config.cctv.yaml")
    channel = next((c for c in cfg.channels if c.id == camera_id), None)
    if channel is None:
        print(f"camera '{camera_id}' tidak ada di config")
        return 2

    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(str(channel.source), cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
    if not cap.isOpened():
        print("gagal membuka stream")
        return 2

    print(f"kamera {camera_id}: {channel.source}")
    print(
        f"ambang: sitting_knee_ratio={cfg.pose.sitting_knee_ratio} "
        f"standing_knee_ratio={cfg.pose.standing_knee_ratio} "
        f"KNEE_SITTING={KNEE_SITTING_ANGLE}deg KNEE_STANDING={KNEE_STANDING_ANGLE}deg"
    )
    print("-" * 78)

    reported = 0
    for _ in range(frames * 5):
        ok, frame = cap.read()
        if not ok:
            break
        results = model.predict(frame, conf=0.4, device="0", verbose=False)
        for r in results:
            kps = getattr(r, "keypoints", None)
            if kps is None or kps.data is None:
                continue
            for person in kps.data:
                raw = person.detach().cpu().numpy() if hasattr(person, "detach") else person
                score = 1.0
                try:
                    if r.boxes is not None and len(r.boxes) and float(r.boxes.conf[0]) > 0:
                        score = float(r.boxes.conf[0])
                except Exception:  # noqa: BLE001
                    pass
                skel = Skeleton(keypoints=raw, score=score)
                if skel.valid_count(0.3) < 8:
                    continue

                k = skel.keypoints
                conf_low = [NAMES[i] for i in range(17) if k[i, 2] < 0.5]
                sh = [k[5], k[6]]
                hip = [k[11], k[12]]
                knee = [k[13], k[14]]
                ank = [k[15], k[16]]

                sh_mid = np.mean([p[:2] for p in sh if p[2] >= 0.3], axis=0)
                hip_mid = np.mean([p[:2] for p in hip if p[2] >= 0.3], axis=0)
                torso = abs(float(sh_mid[1] - hip_mid[1]))

                angles = []
                for i in (0, 1):
                    if hip[i][2] >= 0.3 and knee[i][2] >= 0.3 and ank[i][2] >= 0.3:
                        angles.append(angle(hip[i], knee[i], ank[i]))
                angles = [a for a in angles if not np.isnan(a)]
                knee_angle = float(np.median(angles)) if angles else None

                drop = None
                if all(p[2] >= 0.3 for p in knee):
                    knee_mid_y = float(np.mean([p[1] for p in knee]))
                    drop = abs(knee_mid_y - float(hip_mid[1])) / torso if torso > 1e-3 else None

                verdict = skel.posture(
                    sitting_knee_ratio=cfg.pose.sitting_knee_ratio,
                    standing_knee_ratio=cfg.pose.standing_knee_ratio,
                )

                print(f"postur={verdict:8s} knee_angle={knee_angle} knee_drop={drop}")
                print(
                    f"  titik (x, y, conf):"
                    f" pinggul_l={np.round(k[11], 1)} pinggul_r={np.round(k[12], 1)}"
                )
                print(
                    f"                  lutut_l={np.round(k[13], 1)} lutut_r={np.round(k[14], 1)}"
                )
                print(
                    f"                  mata_kaki_l={np.round(k[15], 1)} mata_kaki_r={np.round(k[16], 1)}"
                )
                print(f"  keypoint rendah (conf<0.5): {conf_low or 'tidak ada'}")
                if torso > 1e-3:
                    print(f"  torso_px={torso:.1f}")
                if drop is not None:
                    print(
                        f"  knee_drop={drop:.3f}  "
                        f"(DUDUK<{cfg.pose.sitting_knee_ratio}, "
                        f"BEDIRI>={cfg.pose.standing_knee_ratio})"
                    )
                if knee_angle is not None:
                    print(
                        f"  knee_angle={knee_angle:.1f}deg  "
                        f"(DUDUK<{KNEE_SITTING_ANGLE}, BEDIRI>{KNEE_STANDING_ANGLE})"
                    )
                print()
                reported += 1
                if reported >= 6:
                    cap.release()
                    return 0
    cap.release()
    if reported == 0:
        print("tidak ada orang terdeteksi pada frame yang diperiksa")
    return 0


if __name__ == "__main__":
    sys.exit(main())