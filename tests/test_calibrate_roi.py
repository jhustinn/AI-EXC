from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from calibrate_roi import regions_from_config, save_to_config  # noqa: E402


MULTI = {
    "timezone": "Asia/Jakarta",
    "cameras": [
        {
            "id": "cctv-1",
            "source": "rtsp://a/1",
            "stream_port": 8001,
            "desks": [
                {"id": 1, "label": "Meja 1", "roi": [0.05, 0.35, 0.3, 0.95]},
                {"id": 2, "label": "Meja 2", "roi": [0.32, 0.35, 0.57, 0.95]},
            ],
        },
        {
            "id": "cctv-4",
            "source": "rtsp://a/4",
            "stream_port": 8004,
            "desks": [{"id": 1, "label": "Meja 1", "roi": [0.55, 0.3, 0.85, 0.95]}],
        },
    ],
}

SINGLE = {
    "camera": {"id": "cam-1", "name": "Cam", "source": "0"},
    "desks": [{"id": 1, "label": "Kursi 1", "roi": [0.1, 0.1, 0.4, 0.9]}],
}


def _write(tmp_path: Path, data: dict, name: str = "config.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_multi_config_requires_camera_id(tmp_path: Path):
    """Tanpa --camera-id, ROI tiap kamera akan saling menimpa."""
    path = _write(tmp_path, MULTI)
    with pytest.raises(SystemExit) as exc:
        regions_from_config(path)
    assert "--camera-id" in str(exc.value)


def test_regions_read_from_selected_camera(tmp_path: Path):
    path = _write(tmp_path, MULTI)
    regions = regions_from_config(path, "cctv-4")
    assert regions == [("Meja 1", (0.55, 0.3, 0.85, 0.95))]

    regions1 = regions_from_config(path, "cctv-1")
    assert len(regions1) == 2
    assert regions1[1][0] == "Meja 2"


def test_unknown_camera_is_rejected(tmp_path: Path):
    path = _write(tmp_path, MULTI)
    with pytest.raises(SystemExit):
        regions_from_config(path, "tidak-ada")


def test_save_updates_only_target_camera(tmp_path: Path):
    path = _write(tmp_path, MULTI)
    new = [("Meja Baru", (0.1, 0.2, 0.3, 0.4))]
    save_to_config(path, new, "cctv-4")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    cam4 = next(c for c in raw["cameras"] if c["id"] == "cctv-4")
    cam1 = next(c for c in raw["cameras"] if c["id"] == "cctv-1")

    assert cam4["desks"] == [{"id": 1, "label": "Meja Baru", "employee_id": None, "roi": [0.1, 0.2, 0.3, 0.4]}]
    # kamera lain harus utuh
    assert len(cam1["desks"]) == 2
    assert cam1["desks"][1]["label"] == "Meja 2"
    # struktur lain tidak hilang
    assert cam4["stream_port"] == 8004
    assert raw["timezone"] == "Asia/Jakarta"


def test_save_creates_backup(tmp_path: Path):
    path = _write(tmp_path, MULTI)
    save_to_config(path, [("X", (0.0, 0.0, 1.0, 1.0))], "cctv-1")
    assert path.with_suffix(".yaml.bak").exists()


def test_single_camera_config_still_works(tmp_path: Path):
    """Format lama (desks di level atas) tidak boleh rusak."""
    path = _write(tmp_path, SINGLE)
    regions = regions_from_config(path)
    assert regions == [("Kursi 1", (0.1, 0.1, 0.4, 0.9))]

    save_to_config(path, [("Kursi Baru", (0.0, 0.0, 0.5, 0.5))])
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["desks"][0]["label"] == "Kursi Baru"


def test_run_py_exposes_camera_id_for_calibrate():
    text = (PROJECT_ROOT / "run.py").read_text(encoding="utf-8")
    assert '"--camera-id", args.camera_id' in text
    assert 'calibrate.add_argument("--camera-id"' in text