"""Deteksi dump truck memakai YOLO COCO + energi gerak pada zona gali."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .config import DetectorConfig, ZoneConfig


@dataclass
class Truck:
    """Satu truck terdeteksi, dalam koordinat piksel frame asli."""
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float

    @property
    def w(self) -> float:
        return self.x2 - self.x1

    @property
    def h(self) -> float:
        return self.y2 - self.y1

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def area(self) -> float:
        return self.w * self.h

    def dump_zone(self, zc: ZoneConfig) -> tuple[float, float, float, float]:
        """Zona tuang = pintu bak di bagian atas bbox truck."""
        top = self.y1 + self.h * zc.dump_top_ratio
        bottom = self.y1 + self.h * (zc.dump_top_ratio + zc.dump_height_ratio)
        return (self.x1, top, self.x2, min(bottom, self.y2))


@dataclass
class FrameResult:
    trucks: list[Truck] = field(default_factory=list)
    dig_motion: float = 0.0
    infer_ms: float = 0.0
    frame_shape: tuple[int, int] = (0, 0)


class Detector:
    """YOLO untuk truck, plus pengukuran gerak pada ROI zona gali."""

    def __init__(self, cfg: DetectorConfig, zones: ZoneConfig, root: Path):
        from ultralytics import YOLO

        model_path = Path(cfg.model)
        if not model_path.is_absolute():
            model_path = root / model_path
        self._model = YOLO(str(model_path))
        self._names = self._model.names

        wanted = {c.lower() for c in cfg.classes}
        self._class_ids = sorted(
            i for i, n in self._names.items() if n.lower() in wanted
        )
        if not self._class_ids:
            raise ValueError(
                f"tidak ada kelas COCO untuk {sorted(wanted)}; "
                f"kelas model: {sorted(self._names.values())}"
            )

        self.cfg = cfg
        self.zones = zones
        self._prev_gray: np.ndarray | None = None

    @property
    def class_names(self) -> list[str]:
        return [self._names[i] for i in self._class_ids]

    def detect(self, frame: np.ndarray) -> FrameResult:
        started = time.perf_counter()
        h, w = frame.shape[:2]
        result = FrameResult(frame_shape=(h, w))

        res = self._model.predict(
            frame,
            conf=self.cfg.confidence,
            iou=self.cfg.iou,
            imgsz=self.cfg.imgsz,
            device=self.cfg.device,
            classes=self._class_ids,
            verbose=False,
        )[0]

        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            for box, cf in zip(xyxy, confs):
                x1, y1, x2, y2 = [float(v) for v in box]
                if x2 <= x1 or y2 <= y1:
                    continue
                lebar = (x2 - x1) / w
                if not (self.cfg.min_width_ratio <= lebar <= self.cfg.max_width_ratio):
                    continue
                result.trucks.append(Truck(x1, y1, x2, y2, float(cf)))

        # truck terbesar dianggap target utama
        result.trucks.sort(key=lambda t: -t.area)

        result.dig_motion = self._gerak_di_zona_gali(frame)
        result.infer_ms = (time.perf_counter() - started) * 1000.0
        return result

    def _gerak_di_zona_gali(self, frame: np.ndarray) -> float:
        """Fraksi piksel di zona gali yang berubah sejak frame sebelumnya.

       inhos dipakai sebagai proksi aktivitas mengguk. Pada kamera di kabin
        seluruh bidang bergerak, jadi ambangnya dibuat longgar.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        h, w = gray.shape[:2]

        x1, y1, x2, y2 = self.zones.dig
        px1, py1 = int(max(0, x1 * w)), int(max(0, y1 * h))
        px2, py2 = int(min(w, x2 * w)), int(min(h, y2 * h))
        if px2 - px1 < 16 or py2 - py1 < 16:
            return 0.0

        roi = gray[py1:py2, px1:px2]

        if self._prev_gray is None:
            self._prev_gray = gray
            return 0.0

        prev_roi = self._prev_gray[py1:py2, px1:px2]
        diff = cv2.absdiff(roi, prev_roi)
        _, mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        gerak = float(np.count_nonzero(mask)) / float(mask.size)
        self._prev_gray = gray
        return gerak

    def reset(self) -> None:
        self._prev_gray = None