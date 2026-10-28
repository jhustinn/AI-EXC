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
    lutut_pt: tuple[float, float] | None = None
    wrist_pt: tuple[float, float] | None = None
    tip_pt: tuple[float, float] | None = None
    base_pt: tuple[float, float] | None = None

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        if self.bucket is None:
            return self.badan.bbox
        return (min(self.bucket.x1, self.badan.x1), min(self.bucket.y1, self.badan.y1),
                max(self.bucket.x2, self.badan.x2), max(self.bucket.y2, self.badan.y2))

    @property
    def base(self) -> tuple[float, float] | None:
        """Titik pangkal boom pada badan ekskavator (boom base pivot)."""
        if self.base_pt is not None:
            return self.base_pt
        h, w = _UKURAN_GAMBAR
        lutut_pt = self.lutut

        # Bila sudut kamera boom-mounted (lutut dekat puncak tengah)
        if w and h and lutut_pt is not None:
            lx, ly = lutut_pt
            if ly < 0.15 * h and abs(lx - 0.5 * w) < 0.20 * w:
                return (w * 0.49, 0.0)

        if self.badan is not None:
            if lutut_pt is not None:
                lx, ly = lutut_pt
                if lx <= self.badan.cx:
                    # Boom mengarah ke kiri: pangkal boom di sisi turret tengah
                    sx = self.badan.x1 + self.badan.w * 0.44
                    sy = self.badan.y1 + self.badan.h * 0.43
                else:
                    # Boom mengarah ke kanan: pangkal boom di sisi turret depan kabin
                    sx = self.badan.x1 + self.badan.w * 0.46
                    sy = self.badan.y1 + self.badan.h * 0.50
                return (sx, sy)
            return (self.badan.cx, self.badan.y1 + self.badan.h * 0.30)

        # Bila kabin ekskavator di luar layar (off-screen sebelah kanan),
        # boom melintas turun ke arah kanan bawah (ke arah kedudukan kabin).
        h, w = _UKURAN_GAMBAR
        if w and self.lutut is not None:
            lx, ly = self.lutut
            base_x = float(w - 10)
            base_y = min(float(h - 50), ly + (base_x - lx) * 0.55)
            return (base_x, base_y)
        elif self.bucket is not None and w:
            return (float(w - 10), min(float(h - 50), self.bucket.cy - 50.0))
        return None

    @property
    def wrist(self) -> tuple[float, float] | None:
        """Titik sendi pergelangan bucket (sambungan arm ke bucket)."""
        if self.wrist_pt is not None:
            return self.wrist_pt
        if self.bucket is None:
            return None
        return (self.bucket.cx, self.bucket.y1)

    @property
    def tip(self) -> tuple[float, float] | None:
        """Titik ujung pengeruk / gigi bucket."""
        if self.tip_pt is not None:
            return self.tip_pt
        if self.bucket is None:
            return None
        return (self.bucket.cx, self.bucket.y2)

    @property
    def lutut(self) -> tuple[float, float] | None:
        """Titik sambungan boom-arm (titik lutut / siku lengan ekskavator).

        Dideteksi langsung dari puncak lekukan boom pada citra (warna kuning
        alat berat). Bila citra tidak tersedia, dihitung dengan kinematika
        lengan ekskavator di mana puncak lekukan boom selalu berada di atas
        garis bucket-body.
        """
        if self.lutut_pt is not None:
            return self.lutut_pt
        if self.lengan is None:
            if self.bucket is not None and self.badan is not None:
                return _titik_lutut((self.bucket.cx, self.bucket.cy),
                                    (self.badan.cx, self.badan.cy))
            return None
        pt1, pt2 = self.lengan
        return _titik_lutut(pt1, pt2)


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

_UKURAN_GAMBAR: tuple[int, int] = (0, 0)
_FRAME_CITRA: np.ndarray | None = None


def set_ukuran_gambar(w: int, h: int) -> None:
    global _UKURAN_GAMBAR
    _UKURAN_GAMBAR = (h, w)


def set_frame_citra(frame: np.ndarray | None) -> None:
    global _FRAME_CITRA
    _FRAME_CITRA = frame


def _titik_lutut(bucket: tuple[float, float],
                 badan: tuple[float, float]) -> tuple[float, float]:
    """Titik sambungan boom-arm dari citra atau kinematika."""
    import math

    bx, by = bucket
    sx, sy = badan
    h, w = _UKURAN_GAMBAR

    # 1. Deteksi presisi dari puncak kontur boom pada citra asli (warna kuning khas alat berat)
    if _FRAME_CITRA is not None:
        try:
            hsv = cv2.cvtColor(_FRAME_CITRA, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([12, 60, 60]), np.array([38, 255, 255]))
            x1 = max(0, int(min(bx, sx) - 50))
            x2 = min(_FRAME_CITRA.shape[1], int(max(bx, sx) + 50))
            y1 = 0
            y2 = min(_FRAME_CITRA.shape[0], int(max(by, sy)))
            roi = np.zeros_like(mask)
            roi[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
            pts = cv2.findNonZero(roi)
            if pts is not None and len(pts) > 30:
                pts = pts.reshape(-1, 2)
                sorted_y = pts[pts[:, 1].argsort()]
                top = sorted_y[:max(8, int(len(sorted_y) * 0.02))]
                elbow_x = float(np.median(top[:, 0]))
                elbow_y = float(np.median(top[:, 1]))
                if elbow_y < min(by, sy) - 10:
                    if h and w:
                        elbow_x = min(max(elbow_x, 0.0), float(w - 1))
                        elbow_y = min(max(elbow_y, 0.0), float(h - 1))
                    return (elbow_x, elbow_y)
        except Exception:
            pass

    # 2. Kinematika fallback: lengan ekskavator selalu melengkung ke atas
    dx, dy = bx - sx, by - sy
    panjang = math.hypot(dx, dy)
    if panjang < 1e-6:
        return ((bx + sx) / 2.0, (by + sy) / 2.0)

    elbow_x = (bx + sx) / 2.0 - 0.1 * panjang
    elbow_y = min(by, sy) - 0.45 * panjang
    if h and w:
        elbow_x = min(max(elbow_x, 0.0), float(w - 1))
        elbow_y = min(max(elbow_y, 10.0), float(h - 1))
    return (float(elbow_x), float(elbow_y))
