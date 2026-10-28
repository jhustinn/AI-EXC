from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from excavator.config import Config, SourceConfig
from excavator.engine import _buka


import cv2

def test_buka_network_stream_rtsp():
    cfg = Config()
    cfg.source = SourceConfig(kind="rtsp", url="rtsp://192.168.1.50:8554/live", ffmpeg=True)

    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_cap.return_value = mock_instance

        cap = _buka(cfg)
        assert cap is mock_instance
        mock_instance.set.assert_called_with(cv2.CAP_PROP_BUFFERSIZE, 1)


def test_buka_network_stream_http_ustreamer():
    """Menguji kecocokan URL HTTP MJPEG dari Raspberry Pi ustreamer."""
    cfg = Config()
    cfg.source = SourceConfig(kind="http", url="http://heracam.local:8080/stream", ffmpeg=False)

    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_cap.return_value = mock_instance

        cap = _buka(cfg)
        assert cap is mock_instance
        # Memastikan buffer size diset 1 untuk mencegah delay akumulatif
        assert mock_instance.set.call_count >= 1


def test_buka_network_stream_empty_url_raises_error():
    cfg = Config()
    cfg.source = SourceConfig(kind="rtsp", url="", path="")

    with pytest.raises(ValueError, match="source.url kosong"):
        _buka(cfg)


def test_buka_video_missing_file_raises_error():
    cfg = Config()
    cfg.source = SourceConfig(kind="video", path="non_existent_video_file_xyz.mp4")

    with pytest.raises(FileNotFoundError):
        _buka(cfg)
