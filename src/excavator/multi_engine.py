"""Multi-Camera Engine Manager.

Mengelola seluruh engine kamera CCTV secara paralel dengan membagikan 1 instance
bobot model YOLO di GPU (NVIDIA GTX 1650 CUDA) untuk efisiensi VRAM maksimal.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import cv2
import numpy as np

from .config import Config, SourceConfig, load_config
from .engine import Engine

logger = logging.getLogger("excavator.multi")


class SharedStreamProvider:
    """Membaca stream MJPEG (seperti RPi Zero W) sekali dan mendistribusikan frame ke beberapa engine.

    Mencegah RPi Zero W mengalami kehabisan CPU / bandwidth Wi-Fi bila beberapa
    kamera mengakses URL yang sama.
    """

    def __init__(self, url: str, fps: float = 35.0):
        self.url = url
        self.target_fps = max(34.0, fps)
        self._latest_frame: np.ndarray | None = None
        self._latest_stamp: float = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"shared-stream-{url}")
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                cap = cv2.VideoCapture(self.url)
                if not cap.isOpened():
                    time.sleep(2.0)
                    continue
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                while not self._stop.is_set():
                    t0 = time.perf_counter()
                    ok, frame = cap.read()
                    if not ok:
                        time.sleep(0.5)
                        break
                    with self._lock:
                        self._latest_frame = frame
                        self._latest_stamp = time.perf_counter()

                    dur = time.perf_counter() - t0
                    jeda = (1.0 / self.target_fps) - dur
                    if jeda > 0.001:
                        time.sleep(jeda)

                cap.release()
            except Exception as exc:
                logger.warning(f"SharedStream error {self.url}: {exc}")
                time.sleep(2.0)

    def get_latest(self) -> tuple[float, np.ndarray] | None:
        with self._lock:
            if self._latest_frame is None:
                return None
            return (self._latest_stamp, self._latest_frame.copy())

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


class MultiCameraManager:
    """Manajer multi-kamera CCTV HERA mining ops."""

    def __init__(self, base_cfg: Config):
        self.base_cfg = base_cfg
        self.engines: dict[int, Engine] = {}
        self.shared_streams: dict[str, SharedStreamProvider] = {}
        self.model_lock = threading.Lock()

        # 1. Muat model YOLO alat berat sekali saja di GPU VRAM
        from ultralytics import YOLO

        model_path = base_cfg.resolve(base_cfg.detector.model)
        logger.info(f"Memuat model YOLO dari {model_path} ke device {base_cfg.detector.device}...")
        self.shared_model = YOLO(str(model_path))

        # 2. Muat model plat jika tersedia
        self.shared_plate = None
        if base_cfg.detector.plate_model:
            plate_path = base_cfg.resolve(base_cfg.detector.plate_model)
            if plate_path.is_file():
                logger.info(f"Memuat model plat dari {plate_path}...")
                self.shared_plate = YOLO(str(plate_path))

        # 3. Inisialisasi daftar kamera
        self._init_cameras()

    def _init_cameras(self) -> None:
        # Coba ambil data kamera dari Laravel API
        cams_data = self._fetch_cameras_from_laravel()
        if not cams_data:
            # Fallback default 6 kamera dengan target FPS >= 30
            cams_data = [
                {"id": 1, "nama": "CAM-01: Cabin Dashcam EXC-07 (RPi Zero AI Live)", "posisi": "Cabin Dashcam (Boom POV)", "unit": "EXC-07", "source_type": "http", "source_path": "http://192.168.1.40:8080/stream.mjpg", "fps": 30, "is_primary": True},
                {"id": 2, "nama": "CAM-02: External Bench Loading Side", "posisi": "External Bench Side", "unit": "EXC-07", "source_type": "video", "source_path": "videos/cam2_bench.mp4", "fps": 30, "is_primary": False},
                {"id": 3, "nama": "CAM-03: Pit Barat Loading Overburden", "posisi": "Pit Barat Highwall", "unit": "EXC-03", "source_type": "video", "source_path": "videos/cam3_pit_barat.mp4", "fps": 30, "is_primary": False},
                {"id": 4, "nama": "CAM-04: Haul Road & Dispatch Gate", "posisi": "Haul Road Access North", "unit": "EXC-07", "source_type": "video", "source_path": "videos/cam4_haul_road.mp4", "fps": 30, "is_primary": False},
                {"id": 5, "nama": "CAM-05: Stockpile Seam 3 Loading", "posisi": "Stockpile Loading Zone", "unit": "EXC-11", "source_type": "video", "source_path": "videos/cam5_stockpile.mp4", "fps": 30, "is_primary": False},
                {"id": 6, "nama": "CAM-06: Raspberry Pi Zero W (Direct Stream)", "posisi": "Cabin Front Windshield (Direct Raw)", "unit": "EXC-07", "source_type": "http", "source_path": "http://192.168.1.40:8080/stream.mjpg", "fps": 30, "is_primary": False},
            ]

        # Buat shared stream provider untuk URL stream yang dipakai bersama
        http_counts: dict[str, int] = {}
        for c in cams_data:
            path = c.get("source_path", "")
            if path.startswith("http://") or path.startswith("https://"):
                http_counts[path] = http_counts.get(path, 0) + 1

        for url, count in http_counts.items():
            if count >= 2 and url not in self.shared_streams:
                self.shared_streams[url] = SharedStreamProvider(url, fps=30.0)

        for c in cams_data:
            cid = int(c["id"])
            cname = c.get("nama", f"CAM-{cid:02d}")
            cpos = c.get("posisi", "Operasional Pit")
            cunit = c.get("unit", self.base_cfg.unit)
            stype = c.get("source_type", "video")
            spath = c.get("source_path", "")
            cfps = max(34, int(c.get("fps", 35)))

            # Copy konfigurasi untuk kamera ini
            cfg = copy.deepcopy(self.base_cfg)
            cfg.unit = cunit
            cfg.server.stream_fps = cfps
            cfg.server.stream_quality = 68
            cfg.server.stream_width = 800
            # Sudut pandang detektor
            is_cabin = (cid == 1 or cid == 6 or "cabin" in cname.lower() or "dashcam" in cname.lower())
            cfg.detector.view = "cabin" if is_cabin else "external"

            provider = None
            if spath.startswith("http://") or spath.startswith("https://"):
                cfg.source.kind = "http"
                cfg.source.path = spath
                cfg.source.url = spath
                cfg.source.loop = False
                cfg.source.ffmpeg = False
                cfg.source.fps = cfps
                if spath in self.shared_streams:
                    provider = self.shared_streams[spath]
            else:
                cfg.source.kind = "video"
                # Resolve relative path
                if not os.path.isabs(spath):
                    cand1 = self.base_cfg.project_root / "laravel" / "public" / spath
                    cand2 = self.base_cfg.project_root / spath
                    if cand1.is_file():
                        cfg.source.path = str(cand1)
                    elif cand2.is_file():
                        cfg.source.path = str(cand2)
                    else:
                        cfg.source.path = str(cand1)
                else:
                    cfg.source.path = spath
                cfg.source.url = ""
                cfg.source.loop = True
                cfg.source.fps = cfps

            eng = Engine(
                cfg,
                camera_id=cid,
                camera_name=cname,
                camera_pos=cpos,
                shared_model=self.shared_model,
                shared_plate=self.shared_plate,
                model_lock=self.model_lock,
                frame_provider=provider,
            )
            self.engines[cid] = eng

    def _fetch_cameras_from_laravel(self) -> list[dict] | None:
        url = "http://127.0.0.1:8002/api/telemetry/cameras"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AI-CCTV-MultiEngine/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    return data.get("cameras")
        except Exception:
            pass
        return None

    def start(self) -> None:
        for cid, eng in self.engines.items():
            eng.start()
        logger.info(f"MultiCameraManager dimulai ({len(self.engines)} engine kamera aktif)")

    def stop(self) -> None:
        for cid, eng in self.engines.items():
            eng.stop()
        for provider in self.shared_streams.values():
            provider.stop()
        logger.info("MultiCameraManager dihentikan")

    def get_engine(self, camera_id: int) -> Engine | None:
        return self.engines.get(camera_id, self.primary_engine)

    @property
    def primary_engine(self) -> Engine:
        if 1 in self.engines:
            return self.engines[1]
        if self.engines:
            return next(iter(self.engines.values()))
        raise RuntimeError("Tidak ada engine kamera terdaftar")
