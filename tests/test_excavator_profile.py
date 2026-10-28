from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from excavator.config import Config


def test_apply_profile_mutates_config_fields():
    cfg = Config()

    profile_dict = {
        "kode_profil": "PROF-TEST-01",
        "nama": "Test Profile Excavator",
        "detector": {
            "confidence": 0.45,
            "release_confidence": 0.35,
            "truck_confidence": 0.55,
            "hold_seconds": 3.2,
            "min_width_ratio": 0.18,
            "plate_confidence": 0.60,
        },
        "zones": {
            "dig": [0.1, 0.4, 0.9, 0.95],
            "dump_top_ratio": 0.08,
            "dump_height_ratio": 0.42,
            "motion_threshold": 0.07,
        },
        "activity": {
            "dig_min_seconds": 2.5,
            "dump_min_seconds": 2.0,
            "phase_min_seconds": 0.7,
            "idle_seconds": 15.0,
            "bucket_low_ratio": 0.62,
        },
    }

    cfg.apply_profile(profile_dict)

    # Verifikasi Detector
    assert cfg.detector.confidence == 0.45
    assert cfg.detector.release_confidence == 0.35
    assert cfg.detector.truck_confidence == 0.55
    assert cfg.detector.hold_seconds == 3.2
    assert cfg.detector.min_width_ratio == 0.18
    assert cfg.detector.plate_confidence == 0.60

    # Verifikasi Zones
    assert cfg.zones.dig == [0.1, 0.4, 0.9, 0.95]
    assert cfg.zones.dump_top_ratio == 0.08
    assert cfg.zones.dump_height_ratio == 0.42
    assert cfg.zones.motion_threshold == 0.07

    # Verifikasi Activity
    assert cfg.activity.dig_min_seconds == 2.5
    assert cfg.activity.dump_min_seconds == 2.0
    assert cfg.activity.phase_min_seconds == 0.7
    assert cfg.activity.idle_seconds == 15.0
    assert cfg.activity.bucket_low_ratio == 0.62


def test_apply_profile_partial_payload():
    cfg = Config()
    original_idle = cfg.activity.idle_seconds

    partial = {
        "detector": {
            "confidence": 0.65,
        },
        "zones": {
            "motion_threshold": 0.09,
        },
    }

    cfg.apply_profile(partial)

    assert cfg.detector.confidence == 0.65
    assert cfg.zones.motion_threshold == 0.09
    assert cfg.activity.idle_seconds == original_idle
