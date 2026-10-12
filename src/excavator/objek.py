"""Deteksi objek alat berat: bucket, ekskavator, dump truck, plat nomor.

Model dilatih sendiri (runs/alat_berat_v1/weights/best.pt) untuk kelas
bucket dan excavator. Truck tetap terbaca karena sekalian dilatih dari
label otomatis YOLO COCO.

Ekskavator tidak diasumsikan selalu muncul sebagai satu kotak utuh.
Ada aturan komposisional: sebuah ekskavator dihitung bila bucket, lengan
penyambung, dan badan kendaraan ketiganya ada - itu persis yang diminta.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .config import DetectorConfig, ZoneConfig


@dataclass
class Objek:
    """Satu objek terdeteksi dalam koordinat piksel frame asli."""
    kelas: str
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float
    # True kalau kotak ini bukan hasil deteksi frame ini, melainkan kotak
    # yang ditahan karena confidence sempat anjlok.
    ditahan: bool = False

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

    def ke_yolo(self) -> tuple[float, float, float, float]:
        return (self.cx, self.cy, self.w, self.h)

    def dump_zone(self, zc: ZoneConfig) -> tuple[float, float, float, float]:
        """Zona tuang = pintu bak di bagian atas bbox truck."""
        top = self.y1 + self.h * zc.dump_top_ratio
        bottom = self.y1 + self.h * (zc.dump_top_ratio + zc.dump_height_ratio)
        return (self.x1, top, self.x2, min(bottom, self.y2))


@dataclass
class ExcavatorKomposisi:
    """Ekskavator hasil aturan: bucket + lengan penyambung + badan kendaraan."""
    bucket: Objek
    badan: Objek
    # ruas garis_bucket ke badan, yaitu lengan/boom ekskavator
    lengan: tuple[tuple[float, float], tuple[float, float]]
    conf: float
    komponen: dict[str, bool] = field(default_factory=dict)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (min(self.bucket.x1, self.badan.x1), min(self.bucket.y1, self.badan.y1),
                max(self.bucket.x2, self.badan.x2), max(self.bucket.y2, self.badan.y2))


@dataclass
class FrameResult:
    objek: list[Objek] = field(default_factory=list)
    ekskavator: list[ExcavatorKomposisi] = field(default_factory=list)
    dig_motion: float = 0.0
    infer_ms: float = 0.0
    frame_shape: tuple[int, int] = (0, 0)
    ditahan: bool = False

    # -- pintasan --
    @property
    def trucks(self) -> list[Objek]:
        return [o for o in self.objek if o.kelas == "truck"]

    @property
    def buckets(self) -> list[Objek]:
        return [o for o in self.objek if o.kelas == "bucket"]

    @property
    def badan(self) -> list[Objek]:
        return [o for o in self.objek if o.kelas == "excavator"]

    @property
    def plates(self) -> list[Objek]:
        return [o for o in self.objek if o.kelas == "plate"]