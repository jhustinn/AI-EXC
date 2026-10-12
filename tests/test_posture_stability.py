from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from presence.pose import (  # noqa: E402
    RECLINING,
    STANDING,
    UNKNOWN,
    PostureStabilizer,
    Skeleton,
    classify_posture,
)


def make_kp(hip_y=200.0, knee_y=260.0, ankle_y=330.0, ankle_conf=0.9, conf=0.9):
    """17 keypoint COCO: 5,6 bahu; 11,12 pinggul; 13,14 lutut; 15,16 mata kaki."""
    kp = np.zeros((17, 3), dtype=np.float32)
    kp[5] = [90, 140, conf]
    kp[6] = [110, 140, conf]
    kp[11] = [95, hip_y, conf]
    kp[12] = [105, hip_y, conf]
    kp[13] = [92, knee_y, conf]
    kp[14] = [108, knee_y, conf]
    kp[15] = [90, ankle_y, ankle_conf]
    kp[16] = [110, ankle_y, ankle_conf]
    return kp


# --- ankle_conf -------------------------------------------------------


def test_low_confidence_ankles_are_ignored():
    """Mata kaki tertutup meja -> YOLO menebak posisi lurus -> duduk terbaca berdiri.

    Fixture ini memakai knee_drop 0.5 (ambigu, tidak cukup untuk DUDUK maupun
    BERDIRI). Semula tebasan keypoint mata kaki yang confidence-nya rendah
     determining BERDIRI lewat sudut 180 derajat.
    """
    # bahu y=140, pinggul y=200 -> torso 60; lutut y=230 -> knee_drop 0.5
    kp = make_kp(hip_y=200.0, knee_y=230.0, ankle_y=260.0, ankle_conf=0.35)
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.3) == STANDING
    # ambang lebih tinggi -> tebasan keypoint dibuang, jatuh ke UNKNOWN
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.5) == UNKNOWN


def test_confident_ankles_still_used_for_standing():
    # lutut di bawah pinggul jelas (drop 1.0) -> berdiri, kaki memang terbaca
    kp = make_kp(hip_y=200.0, knee_y=260.0, ankle_y=330.0, ankle_conf=0.9)
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.5) == STANDING


def test_sitting_is_not_broken_by_ankle_guard():
    """Orang duduk: lutut dekat pinggul (drop 0.2) -> tetap DUDUK."""
    kp = make_kp(hip_y=200.0, knee_y=212.0, ankle_y=345.0, ankle_conf=0.35)
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.5) == "DUDUK"


# --- PostureStabilizer ------------------------------------------------


def test_stabilizer_removes_single_frame_flicker():
    """Orang diam, satu frame salah baca -> label tidak boleh ikut berubah."""
    s = PostureStabilizer(window=9, min_share=0.6)
    now = 0.0
    labels = [ "DUDUK" ] * 8 + [ "BERDIRI" ] + [ "DUDUK" ] * 5
    out = [s.update(1, lab, now + i * 0.05) for i, lab in enumerate(labels)]
    assert "BERDIRI" not in out, f"label berkedip: {out}"


def test_stabilizer_follows_real_transition():
    s = PostureStabilizer(window=5, min_share=0.6)
    for i in range(10):
        s.update(1, "DUDUK", i * 0.05)
    after_stand = [s.update(1, "BERDIRI", 0.5 + i * 0.05) for i in range(8)]
    assert after_stand[-1] == STANDING, "perubahan postur nyata harus tertangkap"


def test_stabilizer_separates_track_ids():
    s = PostureStabilizer(window=5, min_share=0.6)
    for i in range(6):
        s.update(1, "DUDUK", i * 0.05)
        s.update(2, "BERDIRI", i * 0.05)
    assert s.get(1) == "DUDUK"
    assert s.get(2) == STANDING


def test_stabilizer_keeps_previous_when_no_majority():
    s = PostureStabilizer(window=9, min_share=0.6)
    for i in range(9):
        s.update(1, "DUDUK", i * 0.05)
    # seri 1 DUDUK / 1 BERDIRI berulang -> tidak ada mayoritas
    seq = ["DUDUK", "BERDIRI"] * 5
    out = [s.update(1, lab, 0.5 + i * 0.05) for i, lab in enumerate(seq)]
    assert set(out) == {"DUDUK"}, f"label berubah tanpa majorité: {set(out)}"


def test_stabilizer_prunes_stale_tracks():
    s = PostureStabilizer(window=5, ttl_sec=1.0)
    for i in range(5):
        s.update(7, "DUDUK", i * 0.05)
    assert s.get(7) == "DUDUK"
    s.prune(100.0)
    assert s.get(7) is None


def test_stabilizer_prune_keeps_fresh_tracks():
    s = PostureStabilizer(window=5, ttl_sec=3.0)
    for i in range(5):
        s.update(1, "DUDUK", 10.0 + i * 0.05)
    s.prune(10.2)
    assert s.get(1) == "DUDUK"


# --- reclining -------------------------------------------------------


def reclining_keypoints():
    """Orang bersandar di kursi: kaki lurus, batang miring 45 derajat.

    Kasus nyata di lapangan - tanpa cabang BERSANDAR, orang ini terbaca
    BERDIRI karena kaki lurus + lutut jauh di bawah pinggul.
    """
    kp = np.zeros((17, 3), dtype=np.float32)
    # batang: pinggul (200,200) -> bahu (200,140) tapi digeser ke kanan (miring 45)
    kp[11] = [180, 210, 0.9]
    kp[12] = [200, 210, 0.9]
    kp[5] = [260, 140, 0.9]
    kp[6] = [280, 140, 0.9]
    # kaki lurus ke bawah
    kp[13] = [185, 270, 0.9]
    kp[14] = [205, 270, 0.9]
    kp[15] = [188, 340, 0.9]
    kp[16] = [208, 340, 0.9]
    return kp


def test_reclining_is_not_standing():
    kp = reclining_keypoints()
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.3) == RECLINING


def test_standing_person_stays_standing():
    """Batang tegak + kaki lurus harus tetap BERDIRI."""
    kp = make_kp(hip_y=200.0, knee_y=260.0, ankle_y=330.0, ankle_conf=0.9)
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.5) == STANDING


def test_sitting_with_bent_knee_wins_over_tilt():
    """Lutut terlukut -> DUDUK,-however miring batangnya."""
    kp = reclining_keypoints()
    kp[13] = [230, 230, 0.9]
    kp[14] = [250, 230, 0.9]
    kp[15] = [300, 250, 0.9]
    kp[16] = [320, 250, 0.9]
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.3) == "DUDUK"


def test_reclining_tilt_threshold_is_configurable():
    kp = reclining_keypoints()
    # ambang sangat besar -> miring dianggap normal -> kembali jadi berdiri
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.3, reclining_tilt_deg=80.0) == STANDING
    assert classify_posture(kp, min_conf=0.3, ankle_conf=0.3, reclining_tilt_deg=20.0) == RECLINING


def test_stabilizer_smooths_reclining_flicker():
    s = PostureStabilizer(window=9, min_share=0.6)
    seq = ["BERSANDAR"] * 8 + ["BERDIRI"] + ["BERSANDAR"] * 4
    out = [s.update(3, lab, i * 0.05) for i, lab in enumerate(seq)]
    assert "BERDIRI" not in out, out


# --- integrasi skeleton ----------------------------------------------


def test_skeleton_posture_accepts_ankle_conf():
    kp = make_kp(hip_y=200.0, knee_y=230.0, ankle_y=260.0, ankle_conf=0.35)
    skel = Skeleton(keypoints=kp, score=0.9)
    assert skel.posture(min_conf=0.3, ankle_conf=0.3) == STANDING
    assert skel.posture(min_conf=0.3, ankle_conf=0.5) == UNKNOWN


def test_too_few_keypoints_is_unknown():
    kp = make_kp()
    kp[:, 2] = 0.0
    kp[0, 2] = 0.9
    skel = Skeleton(keypoints=kp, score=0.5)
    assert skel.posture() == UNKNOWN