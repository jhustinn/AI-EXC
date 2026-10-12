from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from presence.detector import (  # noqa: E402
    Detection,
    DetectionResult,
    candidate_desks,
)


class _FakeBoxes:
    def __init__(self, xyxy, conf, ids):
        self.xyxy = _Arr(np.array(xyxy, dtype=np.float32))
        self.conf = _Arr(np.array(conf, dtype=np.float32))
        self.id = _Arr(np.array(ids, dtype=np.float32))
        self._data_len = xyxy

    def __len__(self):
        return len(self._data_len)

    def __getitem__(self, idx):
        return self.xyxy[idx]


class _Arr:
    """Porsi .cpu().numpy() yang dipakai deteksi."""

    def __init__(self, data):
        self._data = data

    def cpu(self):
        return self

    def numpy(self):
        return self._data

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        row = self._data[idx]
        return _Arr(row) if getattr(row, "ndim", 0) > 0 else row

    def item(self):
        return float(self._data)


class _FakeResult:
    def __init__(self, xyxy, conf, ids, keypoints=None, speed=None):
        self.boxes = _FakeBoxes(xyxy, conf, ids)
        self.keypoints = keypoints
        self.speed = speed or {"inference": 10.0}


class _FakeKeypoints:
    def __init__(self, data):
        self.data = data


class _ArrK:
    def __init__(self, data):
        self._d = data

    def cpu(self):
        return self

    def numpy(self):
        return self._d.astype(np.float32)


class _FakeKptsData:
    def __init__(self, data):
        self.data = [_ArrK(item) for item in data]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def _make_detector(max_width):
    from presence.config import DetectionConfig
    from presence.detector import PersonDetector as Detector

    cfg = DetectionConfig(model="yolov8n-pose.pt", max_width=max_width, device="cpu")
    det = Detector.__new__(Detector)
    det._cfg = cfg
    det._model = _StubModel()
    det._frame_id = 0
    det._tracker_cfg = None
    det._device = "cpu"
    det._has_keypoints = True
    return det


class _StubModel:
    def __init__(self):
        self.result = None

    def track(self, frame, **_kwargs):
        assert frame.shape[1] == self.expected_width, (
            f"model menerima frame lebar {frame.shape[1]}, diharapkan {self.expected_width}"
        )
        return self.result


def test_bbox_and_keypoints_scaled_back_to_original_frame():
    """Regresi: bbox dulu dikembalikan dalam koordinat max_width.

    Akibatnya ROI meja (dihitung pada frame asli) tidak pernah cocok untuk
    kamera beresolusi tinggi seperti 1920x1080.
    """
    model = _StubModel()
    model.expected_width = 1280
    # satu orang dikoordinat 1280: x 640-896, y 360-720
    kp = np.zeros((1, 17, 3), dtype=np.float32)
    kp[0, 5] = [700, 400, 0.9]
    kp[0, 11] = [700, 500, 0.9]
    model.result = [
        _FakeResult(
            xyxy=[[640.0, 360.0, 896.0, 720.0]],
            conf=[0.9],
            ids=[1.0],
            keypoints=_FakeKeypoints(_FakeKptsData(kp)),
        )
    ]

    det = _make_detector(max_width=1280)
    det._model = model

    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    result = det.track(frame)

    assert len(result.detections) == 1
    bbox = result.detections[0].bbox
    # harus kembali ke ruang 1920: x 960-1344, y 540-1080
    assert bbox[0] == 960, bbox
    assert bbox[2] == 1344, bbox
    assert bbox[1] == 540, bbox
    assert bbox[3] == 1080, bbox
    assert result.frame_shape == (1080, 1920)

    points = result.detections[0].keypoints
    assert points is not None
    assert points[5][0] == pytest.approx(1050.0), points[5]
    assert points[11][1] == pytest.approx(750.0), points[11]


def test_no_scaling_when_frame_already_small():
    model = _StubModel()
    model.expected_width = 704
    kp = np.zeros((1, 17, 3), dtype=np.float32)
    kp[0, 5] = [100, 100, 0.9]
    model.result = [
        _FakeResult(xyxy=[[10.0, 20.0, 300.0, 400.0]], conf=[0.9], ids=[3.0],
                    keypoints=_FakeKeypoints(_FakeKptsData(kp)))
    ]
    det = _make_detector(max_width=1280)
    det._model = model

    frame = np.zeros((576, 704, 3), dtype=np.uint8)
    result = det.track(frame)
    assert result.detections[0].bbox == (10, 20, 300, 400)
    assert result.detections[0].keypoints[5][0] == pytest.approx(100.0)


def test_scaled_bbox_lands_inside_correct_desk_roi():
    """Penggabungan: setelah diskalakan, orang benar-benar ter-assign ke mejanya."""
    model = _StubModel()
    model.expected_width = 1280
    # di 1280: x 200-500, y 500-900  -> di 1920: x 300-750, y 750-1350 (terpotong)
    model.result = [
        _FakeResult(xyxy=[[200.0, 500.0, 500.0, 900.0]], conf=[0.9], ids=[1.0])
    ]
    det = _make_detector(max_width=1280)
    det._model = model

    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    result = det.track(frame)
    det_box = result.detections[0]

    # ROI menutupi x 0.15-0.40 (=288-768), y 0.6-1.0 (=648-1080)
    desks = [(1, "Meja 1", (0.15, 0.6, 0.40, 1.0))]
    cands = candidate_desks(det_box, desks, result.frame_shape, 0.4, anchor=None)
    assert cands, "orang seharusnya ter-assign ke Meja 1"


def test_detection_result_frame_shape_optional():
    """Field baru harus opsional agar konstruktor lama tidak pecah."""
    r = DetectionResult(detections=[], fps=1.0, frame_id=0)
    assert r.frame_shape is None
    d = Detection(track_id=1, bbox=(0, 0, 10, 10), conf=0.5)
    assert d.center == (5.0, 5.0)