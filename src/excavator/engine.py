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
    is_net_stream = sc.kind in ("rtsp", "http", "stream") or bool(sc.url and sc.url.startswith(("rtsp://", "http://", "https://")))
    if is_net_stream:
        stream_url = sc.url or sc.path
        if not stream_url:
            raise ValueError("source.url kosong untuk network stream")
        if sc.ffmpeg:
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise RuntimeError(f"tidak bisa membuka stream: {stream_url}")
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap
    path = cfg.resolve(sc.path)
    if not path.is_file():
        raise FileNotFoundError(f"video tidak ditemukan: {path}")
    return cv2.VideoCapture(str(path))


def _draw_badge(img: np.ndarray, text: str, pos: tuple[int, int],
                fg_col: tuple[int, int, int], bg_col: tuple[int, int, int] = (15, 23, 42),
                font_scale: float = 0.44, thickness: int = 1, pad: int = 4) -> None:
    x, y = pos
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    bx1 = x
    by1 = y - th - pad * 2
    bx2 = x + tw + pad * 2
    by2 = y + pad
    cv2.rectangle(img, (bx1, by1), (bx2, by2), bg_col, -1)
    cv2.rectangle(img, (bx1, by1), (bx2, by2), fg_col, 1)
    cv2.putText(img, text, (x + pad, y - pad), cv2.FONT_HERSHEY_SIMPLEX, font_scale, fg_col, thickness)


def _draw_corner_rect(img: np.ndarray, pt1: tuple[int, int], pt2: tuple[int, int],
                      color: tuple[int, int, int], thickness: int = 2, length: int = 25) -> None:
    x1, y1 = pt1
    x2, y2 = pt2
    # Sudut Kiri-Atas
    cv2.line(img, (x1, y1), (x1 + length, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + length), color, thickness)
    # Sudut Kanan-Atas
    cv2.line(img, (x2, y1), (x2 - length, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + length), color, thickness)
    # Sudut Kiri-Bawah
    cv2.line(img, (x1, y2), (x1 + length, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - length), color, thickness)
    # Sudut Kanan-Bawah
    cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - length), color, thickness)


class Engine:
    """Satu thread untuk semua frame; consumer ambil frame terakhir."""

    def __init__(self, cfg: Config,
                 camera_id: int = 1,
                 camera_name: str | None = None,
                 camera_pos: str | None = None,
                 shared_model=None,
                 shared_plate=None,
                 model_lock: threading.Lock | None = None,
                 frame_provider=None):
        self.cfg = cfg
        self.camera_id = camera_id
        self.camera_name = camera_name or f"CAM-{camera_id:02d}"
        self.camera_pos = camera_pos or "CCTV Feed"
        self.detector = Detector(cfg.detector, cfg.zones, cfg.project_root,
                                 shared_model=shared_model, shared_plate=shared_plate,
                                 model_lock=model_lock)
        self.machine = ActivityMachine(cfg.activity, cfg.zones)
        self.frame_provider = frame_provider
        self.frames: deque[FrameInfo] = deque(maxlen=2)
        self.rid = 0
        self.error: str | None = None
        self.frame_terakhir: datetime | None = None
        self.truck_ditahan: bool = False
        self.hasil = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

        # Asynchronous decoupled inference pipeline
        self._latest_hasil = None
        self._latest_fase: str = "idle"
        self._latest_motion: float = 0.0
        self._infer_lock = threading.Lock()
        self._pending_frame: np.ndarray | None = None
        self._infer_event = threading.Event()
        self._infer_thread: threading.Thread | None = None

    # ---------- kontrol ----------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._infer_thread = threading.Thread(
            target=self._infer_loop, daemon=True, name=f"infer-engine-{self.camera_id}"
        )
        self._infer_thread.start()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name=f"stream-engine-{self.camera_id}"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._infer_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        if self._infer_thread:
            self._infer_thread.join(timeout=3)

    # ---------- inference worker ----------

    def _infer_loop(self) -> None:
        """Worker inferensi GPU background non-blocking.
        
        Berjalan secara independen tanpa menahan atau memperlambat rendering video.
        """
        while not self._stop.is_set():
            self._infer_event.wait(0.04)
            self._infer_event.clear()
            if self._stop.is_set():
                break

            with self._infer_lock:
                frame_to_proc = self._pending_frame
                self._pending_frame = None

            if frame_to_proc is not None:
                try:
                    hasil = self.detector.detect(frame_to_proc)
                    status = self.machine.update(hasil, self.cfg)
                    with self._infer_lock:
                        self._latest_hasil = hasil
                        self._latest_fase = status.fase.value
                        self._latest_motion = hasil.dig_motion
                        self.truck_ditahan = hasil.ditahan
                        self.hasil = hasil
                except Exception as exc:
                    self.error = f"Infer error: {exc}"

    # ---------- loop render & stream ----------

    def _loop(self) -> None:
        # Set presisi timer Windows ke 1ms agar sleep FPS akurat
        try:
            import ctypes
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:
            pass

        target_fps = max(33.0, float(getattr(self.cfg.source, "fps", 33.0)))
        frame_interval = 1.0 / target_fps

        if self.frame_provider is not None:
            while not self._stop.is_set():
                t0 = time.perf_counter()
                frame_data = self.frame_provider.get_latest()
                if frame_data is not None:
                    _, frame = frame_data
                    try:
                        self._render_and_push(frame)
                    except Exception as exc:
                        self.error = f"{type(exc).__name__}: {exc}"
                dur = time.perf_counter() - t0
                jeda = frame_interval - dur
                if jeda > 0.001:
                    time.sleep(jeda)
                else:
                    time.sleep(0.001)
            return

        while not self._stop.is_set():
            try:
                cap = _buka(self.cfg)
            except Exception as exc:  # noqa: BLE001
                self.error = f"{type(exc).__name__}: {exc}"
                time.sleep(2)
                continue

            self.error = None
            self.detector.reset()

            while not self._stop.is_set():
                t0 = time.perf_counter()
                ok, frame = cap.read()
                if not ok:
                    if self.cfg.source.kind == "video" and self.cfg.source.loop:
                        seek_ok = cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        if not seek_ok:
                            cap.release()
                            cap = _buka(self.cfg)
                        self.detector.reset()
                        time.sleep(0.01)
                        continue
                    elif self.cfg.source.kind in ("rtsp", "http", "stream") or str(self.cfg.source.path).startswith(("http://", "https://", "rtsp://")):
                        self.error = "stream terputus, mencoba reconnect..."
                        time.sleep(1.0)
                        try:
                            cap.release()
                            cap = _buka(self.cfg)
                            self.error = None
                            continue
                        except Exception as rec_err:
                            self.error = f"reconnect gagal: {rec_err}"
                            continue
                    self.error = "sumber frame berhenti"
                    break

                try:
                    self._render_and_push(frame)
                except Exception as exc:
                    self.error = f"{type(exc).__name__}: {exc}"

                dur = time.perf_counter() - t0
                jeda = frame_interval - dur
                if jeda > 0.001:
                    time.sleep(jeda)
                else:
                    time.sleep(0.001)

            cap.release()
            if not self._stop.is_set():
                time.sleep(0.5)

    def _render_and_push(self, frame: np.ndarray) -> None:
        """Render HUD & bounding box cepat tanpa blocking inferensi GPU (30+ FPS)."""
        # 1. Kirim frame ke worker inferensi bila worker sedang idle
        with self._infer_lock:
            if self._pending_frame is None:
                self._pending_frame = frame.copy()
                self._infer_event.set()
            hasil = self._latest_hasil
            fase = self._latest_fase
            motion = self._latest_motion

        # 2. Gambar overlay dengan deteksi terbaru
        if hasil is not None:
            annot = self._anotasi(frame, hasil, fase, motion)
        else:
            annot = frame

        # 3. Optimasi resize bandwidth stream jika perlu
        target_w = getattr(self.cfg.server, "stream_width", 960)
        h_a, w_a = annot.shape[:2]
        if target_w and target_w < w_a:
            scale_stream = target_w / float(w_a)
            stream_frame = cv2.resize(annot, (target_w, int(h_a * scale_stream)), interpolation=cv2.INTER_AREA)
        else:
            stream_frame = annot

        # 4. Encode JPEG cepat (kualitas 68 untuk performa tinggi & FPS lancar)
        quality = min(70, max(55, getattr(self.cfg.server, "stream_quality", 68)))
        ok, buf = cv2.imencode(".jpg", stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            return

        with self._lock:
            self.rid += 1
            self.frame_terakhir = datetime.now()
            self.frames.append(FrameInfo(buf.tobytes(), self.frame_terakhir,
                                         hasil.objek if hasil else []))

    def _process(self, frame: np.ndarray) -> None:
        hasil = self.detector.detect(frame)
        status = self.machine.update(hasil, self.cfg)
        with self._infer_lock:
            self._latest_hasil = hasil
            self._latest_fase = status.fase.value
            self._latest_motion = hasil.dig_motion
            self.truck_ditahan = hasil.ditahan
            self.hasil = hasil
        annot = self._anotasi(frame, hasil, status.fase.value, hasil.dig_motion)
        target_w = getattr(self.cfg.server, "stream_width", 960)
        h_a, w_a = annot.shape[:2]
        if target_w and target_w < w_a:
            scale_stream = target_w / float(w_a)
            stream_frame = cv2.resize(annot, (target_w, int(h_a * scale_stream)), interpolation=cv2.INTER_AREA)
        else:
            stream_frame = annot

        ok, buf = cv2.imencode(".jpg", stream_frame,
                               [int(cv2.IMWRITE_JPEG_QUALITY),
                                getattr(self.cfg.server, "stream_quality", 68)])
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
        trucks = hasil.trucks

        # 1. Zona gali / Zona Pantau
        is_cabin = (getattr(self.cfg.detector, "view", "cabin") == "cabin")
        zx1, zy1, zx2, zy2 = self.cfg.zones.dig
        gx1, gy1 = int(zx1 * w), int(zy1 * h)
        gx2, gy2 = int(zx2 * w), int(zy2 * h)
        if is_cabin:
            _draw_corner_rect(vis, (gx1, gy1), (gx2, gy2), (59, 130, 246), thickness=2, length=35)
            _draw_badge(vis, "ZONA GALI", (gx1 + 14, max(22, gy2 - 14)), (59, 130, 246), font_scale=0.42)
        elif "haul" in self.camera_name.lower():
            _draw_corner_rect(vis, (gx1, gy1), (gx2, gy2), (14, 165, 233), thickness=2, length=35)
            _draw_badge(vis, "ZONA HAUL ROAD / DISPATCH", (gx1 + 14, max(22, gy2 - 14)), (14, 165, 233), font_scale=0.42)
        elif "stockpile" in self.camera_name.lower():
            _draw_corner_rect(vis, (gx1, gy1), (gx2, gy2), (245, 158, 11), thickness=2, length=35)
            _draw_badge(vis, "ZONA STOCKPILE SEAM 3", (gx1 + 14, max(22, gy2 - 14)), (245, 158, 11), font_scale=0.42)
        else:
            _draw_corner_rect(vis, (gx1, gy1), (gx2, gy2), (59, 130, 246), thickness=2, length=35)
            _draw_badge(vis, "ZONA OPERASIONAL PIT", (gx1 + 14, max(22, gy2 - 14)), (59, 130, 246), font_scale=0.42)

        # 2. Ekskavator: badan kendaraan + bucket + skeleton lengan (boom & arm)
        for e in hasil.ekskavator:
            # 2a. Kotak badan ekskavator (kabin & roda rantai)
            if e.badan is not None:
                sx1, sy1, sx2, sy2 = [int(v) for v in e.badan.bbox]
                # Jangan gambar kotak bila deteksi adalah kaca kabin sendiri yang menutupi layar (> 40% area)
                b_area = (sx2 - sx1) * (sy2 - sy1)
                is_fullscreen_cabin = (b_area / float(w * h) > 0.40)
                if not is_fullscreen_cabin:
                    cv2.rectangle(vis, (sx1, sy1), (sx2, sy2), (168, 85, 247), 2)
                    lbl_badan = f"EXCAVATOR {e.badan.conf:.2f} (DITAHAN)" if e.badan.ditahan else f"EXCAVATOR {e.badan.conf:.2f}"
                    _draw_badge(vis, lbl_badan, (sx1, max(22, sy1 - 6)), (168, 85, 247))

            # 2b. Kotak bucket (alat pengeruk bergigi)
            if e.bucket is not None:
                bx1, by1, bx2, by2 = [int(v) for v in e.bucket.bbox]
                cv2.rectangle(vis, (bx1, by1), (bx2, by2), (34, 197, 94), 2)
                lbl_bucket = f"BUCKET {e.bucket.conf:.2f} (DITAHAN)" if e.bucket.ditahan else f"BUCKET {e.bucket.conf:.2f}"
                _draw_badge(vis, lbl_bucket, (bx1, max(22, by1 - 6)), (34, 197, 94))

            # 2c. Skeleton anatomi: Base (pangkal) -> Lutut (Elbow) -> Wrist -> Tip
            # Hanya gambar skeleton bila bucket aktif terdeteksi (mencegah garis liar ke pohon/jendela)
            if e.lutut is not None and e.bucket is not None:
                base = e.base
                lutut = e.lutut
                wrist = e.wrist
                tip = e.tip

                # Ruas 1: BOOM (Pangkal kabin/body -> Siku/Elbow atas)
                if base is not None:
                    cv2.line(vis, (int(base[0]), int(base[1])), (int(lutut[0]), int(lutut[1])),
                             (168, 85, 247), 3)
                    cv2.circle(vis, (int(base[0]), int(base[1])), 6, (168, 85, 247), -1)
                    cv2.circle(vis, (int(base[0]), int(base[1])), 3, (255, 255, 255), -1)
                    _draw_badge(vis, "BOOM", (int((base[0] + lutut[0]) / 2), int((base[1] + lutut[1]) / 2)),
                                (168, 85, 247), font_scale=0.38, pad=2)

                # Ruas 2: ARM / STICK (Siku/Elbow atas -> Sendi pergelangan bucket)
                if wrist is not None:
                    cv2.line(vis, (int(lutut[0]), int(lutut[1])), (int(wrist[0]), int(wrist[1])),
                             (236, 72, 153), 3)
                    cv2.circle(vis, (int(wrist[0]), int(wrist[1])), 6, (34, 197, 94), -1)
                    cv2.circle(vis, (int(wrist[0]), int(wrist[1])), 3, (255, 255, 255), -1)
                    _draw_badge(vis, "ARM", (int((lutut[0] + wrist[0]) / 2), int((lutut[1] + wrist[1]) / 2)),
                                (236, 72, 153), font_scale=0.38, pad=2)

                # Ruas 3: BUCKET (Sendi pergelangan -> Ujung gigi)
                if wrist is not None and tip is not None:
                    cv2.line(vis, (int(wrist[0]), int(wrist[1])), (int(tip[0]), int(tip[1])),
                             (34, 197, 94), 2)
                    cv2.circle(vis, (int(tip[0]), int(tip[1])), 5, (34, 197, 94), -1)

                # Titik sendi siku/elbow (Lutut)
                cv2.circle(vis, (int(lutut[0]), int(lutut[1])), 7, (255, 255, 255), -1)
                cv2.circle(vis, (int(lutut[0]), int(lutut[1])), 7, (168, 85, 247), 2)

        # 3. Bucket mandiri
        for b in hasil.buckets:
            if any(e.bucket is b for e in hasil.ekskavator):
                continue
            cv2.rectangle(vis, (int(b.x1), int(b.y1)), (int(b.x2), int(b.y2)), (34, 197, 94), 2)
            lbl = f"BUCKET {b.conf:.2f} (DITAHAN)" if b.ditahan else f"BUCKET {b.conf:.2f}"
            _draw_badge(vis, lbl, (int(b.x1), max(22, int(b.y1) - 6)), (34, 197, 94))

        # 4. Plat nomor
        for p in hasil.plates:
            cv2.rectangle(vis, (int(p.x1), int(p.y1)), (int(p.x2), int(p.y2)), (14, 165, 233), 2)
            _draw_badge(vis, f"PLAT {p.conf:.2f}", (int(p.x1), max(22, int(p.y1) - 6)), (14, 165, 233), font_scale=0.40)

        # 5. Truck + Zona Tuang
        for i, t in enumerate(trucks):
            tx1, ty1, tx2, ty2 = int(t.x1), int(t.y1), int(t.x2), int(t.y2)
            cv2.rectangle(vis, (tx1, ty1), (tx2, ty2), (245, 158, 11), 2)
            label = f"TRUCK {t.conf:.2f} (DITAHAN)" if t.ditahan else f"TRUCK {t.conf:.2f}"
            _draw_badge(vis, label, (tx1, max(22, ty1 - 6)), (245, 158, 11))

            # Zona Tuang (di bagian bak dump truck)
            dx1, dy1, dx2, dy2 = [int(v) for v in t.dump_zone(self.cfg.zones)]
            cv2.rectangle(vis, (dx1, dy1), (dx2, dy2), (34, 197, 94), 2)
            if i == 0 or t.w >= 0.12 * w:
                # Badge diletakkan di dalam zona tuang bagian atas agar tidak bertubrukan dengan badge TRUCK
                _draw_badge(vis, "ZONA TUANG", (dx1 + 8, dy1 + 22), (34, 197, 94), font_scale=0.40)

        # 6. Glassmorphic HUD Panel (Pojok Kiri Atas)
        hud_w, hud_h = 350, 165
        hud_x, hud_y = 20, 20
        if hud_y + hud_h < h and hud_x + hud_w < w:
            sub = vis[hud_y:hud_y + hud_h, hud_x:hud_x + hud_w]
            dark_bg = np.full_like(sub, (15, 23, 42), dtype=np.uint8)
            vis[hud_y:hud_y + hud_h, hud_x:hud_x + hud_w] = cv2.addWeighted(sub, 0.25, dark_bg, 0.75, 0)
            cv2.rectangle(vis, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), (51, 65, 85), 1)

            # Header Kamera & Fase
            cam_code = f"CAM-{self.camera_id:02d}"
            fase_teks = f"{cam_code} | FASE: {FASE_LABEL.get(Fase(fase), fase).upper()}"
            (ftw, _), _ = cv2.getTextSize(fase_teks, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 2)
            badge_w = max(195, ftw + 32)
            cv2.rectangle(vis, (hud_x + 14, hud_y + 12), (hud_x + 14 + badge_w, hud_y + 38), (30, 41, 59), -1)
            cv2.rectangle(vis, (hud_x + 14, hud_y + 12), (hud_x + 20, hud_y + 38), warna, -1)
            cv2.putText(vis, fase_teks, (hud_x + 26, hud_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (241, 245, 249), 2)

            # Baris Status Telemetri
            eks = hasil.ekskavator[0] if hasil.ekskavator else None
            is_cabin = (getattr(self.cfg.detector, "view", "cabin") == "cabin")
            if is_cabin:
                badan_info = f"{self.cfg.unit} (Host)"
            else:
                n_eks = len(hasil.ekskavator)
                badan_info = f"{n_eks} Unit ({self.cfg.unit})" if n_eks > 0 else "Standby (Pit)"
            n_trucks = len(trucks)
            truck_info = f"{n_trucks} Unit Aktif" if n_trucks > 0 else "Mencari armada..."
            bucket_info = f"{eks.bucket.conf:.2f} (Aktif)" if (eks and eks.bucket is not None) else "Mencari (Di Pit)..."
            skel_info = "Aktif (Boom+Arm)" if (eks and eks.lutut is not None and eks.bucket is not None) else "Standby"

            rows = [
                ("Unit Alat", badan_info, (168, 85, 247)),
                ("Dump Truck", truck_info, (245, 158, 11)),
                ("Bucket", bucket_info, (34, 197, 94)),
                ("Skeleton", skel_info, (236, 72, 153) if (eks and eks.lutut is not None) else (148, 163, 184)),
            ]
            for i, (k, val, col) in enumerate(rows):
                ry = hud_y + 64 + i * 24
                cv2.circle(vis, (hud_x + 22, ry - 4), 4, col, -1)
                cv2.putText(vis, k, (hud_x + 36, ry), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (148, 163, 184), 1)
                cv2.putText(vis, val, (hud_x + 150, ry), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (241, 245, 249), 1)

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
                time.sleep(0.005)