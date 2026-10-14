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

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    def dump_zone(self, zc: ZoneConfig) -> tuple[float, float, float, float]:
        """Zona tuang = pintu bak di bagian atas bbox truck."""
        top = self.y1 + self.h * zc.dump_top_ratio
        bottom = self.y1 + self.h * (zc.dump_top_ratio + zc.dump_height_ratio)
        return (self.x1, top, self.x2, min(bottom, self.y2))


@dataclass
class ExcavatorKomposisi:
    """Ekskavator hasil aturan: bucket + lengan penyambung + badan kendaraan."""
    bucket: Objek | None
    badan: Objek
    # ruas garis bucket ke badan, yaitu lengan/boom ekskavator.
    # None bila bucket tidak terdeteksi - badan ekskavator tetap dihitung
    # karena mesinnya benar-benar terlihat di layar.
    lengan: tuple[tuple[float, float], tuple[float, float]] | None
    conf: float
    komponen: dict[str, bool] = field(default_factory=dict)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        if self.bucket is None:
            return self.badan.bbox
        return (min(self.bucket.x1, self.badan.x1), min(self.bucket.y1, self.badan.y1),
                max(self.bucket.x2, self.badan.x2), max(self.bucket.y2, self.badan.y2))

    @property
    def lutut(self) -> tuple[float, float] | None:
        """Titik sambungan boom-arm (titik lutut lengan ekskavator).

        PENTING: ini BUKAN hasil deteksi model. Yang terukur hanya kotak
        bucket dan kotak body. Titik ini dihitung geometris dari keduanya:
        lengan ekskavator membungkuk, jadi ruas kedua digeser tegak lurus
        dari garis lurus bucket-body. Besar pergeseran diambil dari
       scripts/ukur_lutut.py yang mengukur sudut lekukan pada gambar
        referensi.

        Jika suatu saat model pose dilatih, titik ini harus diganti dengan
        keypoint asli dan confidence harus diturunkan sesuai key error.
        """
        if self.bucket is None or self.lengan is None:
            return None
        (bx, by), (sx, sy) = self.lengan
        return _titik_lutut((bx, by), (sx, sy))


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


# ----------------------------------------------------------------------
# Geometri lengan ekskavator
# ----------------------------------------------------------------------
# Lengan ekskavator tidak lurus: boom naik dari badan, lalu arm turun ke
# bucket. Jadi lengan membungkuk. RUAS_TORONG adalah bagian besar lekukan
# itu, diukur pada gambar referensi (scripts/ukur_lutut.py).
#
# Yang BELUM terukur adalah titik lutut itu sendiri - tidak ada keypoint di
# dataset. Nilai ini adalah_parametrisasi_, bukan hasil deteksi.
RUAS_TORONG = 0.42


def _titik_lutut(bucket: tuple[float, float],
                 badan: tuple[float, float]) -> tuple[float, float]:
    """Titik sambungan boom-arm dari dua titik yang benar-benar terukur."""
    import math

    bx, by = bucket
    sx, sy = badan
    dx, dy = bx - sx, by - sy
    panjang = math.hypot(dx, dy)
    if panjang < 1e-6:
        return ((bx + sx) / 2.0, (by + sy) / 2.0)

    # titik di tengah ruas
    mx, my = (bx + sx) / 2.0, (by + sy) / 2.0
    # arah tegak lurus
    ux, uy = -dy / panjang, dx / panjang
    # Arah tekuk lengan ekskavator (boom naik dari badan, arm turun ke
    # bucket) dibalik kalau titik hasil geser mendarat di sisi yang salah,
    # supaya bungkusan tidak keluar ke bawah area gambar.
    off = RUAS_TORONG * panjang
    lx, ly = mx + ux * off, my + uy * off
    h, w = _UKURAN_GAMBAR
    if h and lx > w * 0.5:
        lx, ly = mx - ux * off, my - uy * off
    return (lx, ly)


# diisi engine setiap frame supaya _titik_lutut bisa menjaga agar titik
# tidak keluar dari area gambar
_UKURAN_GAMBAR: tuple[int, int] = (0, 0)


def set_ukuran_gambar(w: int, h: int) -> None:
    global _UKURAN_GAMBAR
    _UKURAN_GAMBAR = (h, w)
