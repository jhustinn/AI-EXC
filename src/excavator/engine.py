"""Loop utama: baca frame, deteksi truck, jalankan state machine, buat MJPEG."""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

from .activity import FASE_LABEL, ActivityMachine, Fase
from .config import Config
from .detector import Detector

# warna fase untuk overlay
WARNA_FASE = {
    "idle": (148, 163, 184),
    "mengangkat": (59, 130, 246),
    "mengeruk": (34, 197, 94),
    "memutar": (168, 85, 247),
    "menuangkan": (245, 158, 11),
    "kembali": (239, 68, 68),
}


@dataclass
class FrameInfo:
    """Satu frame yang sudah dianotasi, siap dikirim sebagai JPEG."""
    jpeg: bytes
    stamp: datetime
    trucks: list[Truck] = field(default_factory=list)


def _buka(cfg: Config) -> cv2.VideoCapture:
    sc = cfg.source
    if sc.kind == "rtsp":
        if not sc.url:
            raise ValueError("source.kind=rtsp tapi source.url kosong")
        if sc.ffmpeg:
            cap = cv2.VideoCapture(sc.url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                return cap
        cap = cv2.VideoCapture(sc.url)
        if not cap.isOpened():
            raise RuntimeError(f"tidak bisa membuka RTSP: {sc.url}")
        return cap
    path = cfg.resolve(sc.path)
    if not path.is_file():
        raise FileNotFoundError(f"video tidak ditemukan: {path}")
    return cv2.VideoCapture(str(path))


class Engine:
    """Satu thread untuk semua frame; consumer ambil frame terakhir."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.detector = Detector(cfg.detector, cfg.zones, cfg.project_root)
        self.machine = ActivityMachine(cfg.activity, cfg.zones)
        self.frames: deque[FrameInfo] = deque(maxlen=2)
        self.rid = 0
        self.error: str | None = None
        self.frame_terakhir: datetime | None = None
        self.truck_ditahan: bool = False
        self.hasil = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    # ---------- kontrol ----------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="excavator-engine")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    # ---------- loop ----------

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                cap = _buka(self.cfg)
            except Exception as exc:  # noqa: BLE001
                self.error = f"{type(exc).__name__}: {exc}"
                time.sleep(3)
                continue

            self.error = None
            self.detector.reset()
            target_fps = max(1, self.cfg.source.fps)

            while not self._stop.is_set():
                mulai = time.perf_counter()
                ok, frame = cap.read()
                if not ok:
                    if self.cfg.source.kind == "video" and self.cfg.source.loop:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.detector.reset()
                        continue
                    self.error = "sumber frame berhenti"
                    break
                self._process(frame)

                jeda = 1.0 / target_fps - (time.perf_counter() - mulai)
                if jeda > 0:
                    time.sleep(jeda)

            cap.release()
            if not self._stop.is_set():
                time.sleep(1)

    def _process(self, frame: np.ndarray) -> None:
        hasil = self.detector.detect(frame)
        status = self.machine.update(hasil, self.cfg)
        annot = self._anotasi(frame, hasil, status.fase.value, hasil.dig_motion)
        ok, buf = cv2.imencode(".jpg", annot,
                               [int(cv2.IMWRITE_JPEG_QUALITY),
                                self.cfg.server.stream_quality])
        if not ok:
            return
        with self._lock:
            self.rid += 1
            self.frame_terakhir = datetime.now()
            self.truck_ditahan = hasil.ditahan
            self.hasil = hasil
            self.frames.append(FrameInfo(buf.tobytes(), self.frame_terakhir,
                                         hasil.objek))

    # ---------- overlay ----------

    def _anotasi(self, frame: np.ndarray, hasil, fase: str,
                 motion: float) -> np.ndarray:
        vis = frame.copy()
        h, w = vis.shape[:2]
        warna = WARNA_FASE.get(fase, (255, 255, 255))
        skala = w / 640.0
        trucks = hasil.trucks

        # zona gali (tetap)
        x1, y1, x2, y2 = self.cfg.zones.dig
        cv2.rectangle(vis, (int(x1 * w), int(y1 * h)),
                      (int(x2 * w), int(y2 * h)), (59, 130, 246), 2)
        cv2.putText(vis, "ZONA GALI", (int(x1 * w) + 6, int(y1 * h) + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55 * skala,
                    (59, 130, 246), 2)

        # ekskavator: bucket + lengan penyambung + badan kendaraan
        for e in hasil.ekskavator:
            if e.komponen.get("badan"):
                cv2.line(vis, (int(e.lengan[0][0]), int(e.lengan[0][1])),
                         (int(e.lengan[1][0]), int(e.lengan[1][1])),
                         (168, 85, 247), 4)          # lengan/boom
                cv2.circle(vis, (int(e.badan.cx), int(e.badan.cy)),
                           6, (168, 85, 247), -1)
            bx1, by1, bx2, by2 = [int(v) for v in e.bucket.bbox]
            cv2.rectangle(vis, (bx1, by1), (bx2, by2), (168, 85, 247), 2)
            cv2.putText(vis, f"excavator {e.conf:.2f}", (bx1, max(16, by1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55 * skala, (168, 85, 247), 2)

        # bucket (dari kelas excavator juga sudah digambar di atas)
        for b in hasil.buckets:
            if any(e.bucket is b for e in hasil.ekskavator):
                continue
            cv2.rectangle(vis, (int(b.x1), int(b.y1)), (int(b.x2), int(b.y2)),
                          (34, 197, 94), 2)
            cv2.putText(vis, f"bucket {b.conf:.2f}", (int(b.x1), max(16, int(b.y1) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5 * skala, (34, 197, 94), 2)

        # plat nomor
        for p in hasil.plates:
            cv2.rectangle(vis, (int(p.x1), int(p.y1)), (int(p.x2), int(p.y2)),
                          (14, 165, 233), 2)
            cv2.putText(vis, f"plat {p.conf:.2f}", (int(p.x1), max(16, int(p.y1) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45 * skala, (14, 165, 233), 2)

        # truck + zona tuang
        for i, t in enumerate(trucks):
            if t.ditahan:
                # kotak ditahan dari frame sebelumnya, bukan hasil deteksi
                # frame ini - ditulis berbeda supaya tidak dikira bukti
                cv2.rectangle(vis, (int(t.x1), int(t.y1)), (int(t.x2), int(t.y2)),
                              (245, 158, 11), 2)
                tengah = (int((t.x1 + t.x2) / 2), int((t.y1 + t.y2) / 2))
                cv2.line(vis, (tengah[0] - 8, tengah[1]), (tengah[0] + 8, tengah[1]),
                         (245, 158, 11), 2)
                cv2.line(vis, (tengah[0], tengah[1] - 8), (tengah[0], tengah[1] + 8),
                         (245, 158, 11), 2)
                label = "truck (ditahan)"
            else:
                cv2.rectangle(vis, (int(t.x1), int(t.y1)), (int(t.x2), int(t.y2)),
                              (245, 158, 11), 2)
                label = f"truck {t.conf:.2f}"
            dx1, dy1, dx2, dy2 = [int(v) for v in t.dump_zone(self.cfg.zones)]
            cv2.rectangle(vis, (dx1, dy1), (dx2, dy2), (34, 197, 94), 2)
            cv2.putText(vis, label, (int(t.x1), max(16, int(t.y1) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5 * skala, (245, 158, 11), 2)
            if i == 0:
                cv2.putText(vis, "ZONA TUANG", (dx1, max(16, dy1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5 * skala,
                            (34, 197, 94), 2)

        # panel status
        pad = int(10 * skala)
        tinggi = int(112 * skala)
        cv2.rectangle(vis, (0, 0), (int(300 * skala), tinggi), (15, 23, 42), -1)
        eks = hasil.ekskavator[0] if hasil.ekskavator else None
        baris = [
            (f"FASE: {FASE_LABEL[Fase(fase)].upper()}", warna),
            (f"truck conf: {trucks[0].conf:.2f}" if trucks else "truck: tidak terdeteksi", (245, 158, 11)),
            (f"bucket: {eks.bucket.conf:.2f}" if eks else "bucket: tidak terdeteksi", (34, 197, 94)),
            (f"excavator: {eks.conf:.2f}" if eks else "excavator: tidak", (168, 85, 247)),
        ]
        for i, (teks, c) in enumerate(baris):
            cv2.putText(vis, teks, (pad, int((26 + i * 26) * skala)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55 * skala, c, 2)

        return vis

    # ---------- untuk consumer ----------

    def frame_terbaru(self) -> FrameInfo | None:
        with self._lock:
            return self.frames[-1] if self.frames else None

    def stream(self) -> Iterator[bytes]:
        """Generator MJPEG. Browser terhubung langsung, tidak lewat PHP."""
        terakhir: datetime | None = None
        while not self._stop.is_set():
            info = self.frame_terbaru()
            if info is not None and info.stamp != terakhir:
                terakhir = info.stamp
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n"
                       b"Content-Length: " + str(len(info.jpeg)).encode() +
                       b"\r\n\r\n" + info.jpeg + b"\r\n")
            else:
                time.sleep(1.0 / max(1, self.cfg.server.stream_fps))