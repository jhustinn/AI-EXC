"""Mesin deteksi objek alat berat."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .config import DetectorConfig, ZoneConfig
from .objek import (
    ExcavatorKomposisi,
    FrameResult,
    Objek,
    set_frame_citra,
    set_ukuran_gambar,
)

# jarak maksimum pusat bucket ke pusat badan agar dianggap satu mesin
JARAK_BUCKET_BADAN = 0.75
# bucket dianggap "di atas" bila pusatnya lebih tinggi dari badan
SELISIH_TINGGI_BUCKET = 0.05


# ----------------------------------------------------------------------
# Penyaring kotak yang isinya langit
# ----------------------------------------------------------------------
# Bucket ekskavator SELALU kuning/oram/coklat: logam dan tanah. Tidak pernah
# biru langit. Kotak yang isinya langit adalah false positive - di frame
# 1452 model memberi conf 0,59 ke kotak berisi aspal dan pohon di antara dua
# ekskavator, lalu skeleton digambar dari titik yang salah itu.
#
# Diukur (ukur_kosong.py): 17 dari 241 kotak bucket (7%) berisi langit.
# Ambang dipilih longgar supaya hanya warna langit yang ditolak.


def _terlihat_langit(gambar, x1, y1, x2, y2) -> bool:
    """True bila isi kotak didominasi langit-langit."""
    h, w = gambar.shape[:2]
    xa, ya = max(0, int(x1)), max(0, int(y1))
    xb, yb = min(w, int(x2)), min(h, int(y2))
    if xb - xa < 8 or yb - ya < 8:
        return False
    crop = gambar[ya:yb, xa:xb].astype("float32")
    b, g, r = crop[..., 0].mean(), crop[..., 1].mean(), crop[..., 2].mean()
    mx, mn = max(b, g, r), min(b, g, r)
    jenuh = (mx - mn) / max(1.0, mx)
    return b > r + 15 and b > 110 and jenuh < 0.32


def _rasio_hijau_bak(frame: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> float:
    """Mengukur proporsi warna hijau toska khas bak dump truck."""
    h, w = frame.shape[:2]
    crop = frame[max(0, int(y1)):min(h, int(y2)), max(0, int(x1)):min(w, int(x2))]
    if crop.size == 0:
        return 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([100, 255, 255]))
    return float(np.count_nonzero(mask)) / float(mask.size)


def _rasio_kuning_cat(frame: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> float:
    """Mengukur proporsi warna kuning khas cat alat berat (Caterpillar/Komatsu)."""
    h, w = frame.shape[:2]
    crop = frame[max(0, int(y1)):min(h, int(y2)), max(0, int(x1)):min(w, int(x2))]
    if crop.size == 0:
        return 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([10, 40, 40]), np.array([40, 255, 255]))
    return float(np.count_nonzero(mask)) / float(mask.size)


def _kinematika_lengan(frame: np.ndarray,
                       trucks: list[Objek] | None = None,
                       badan_box: tuple[float, float, float, float] | None = None,
                       is_cabin_view: bool = False
                       ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float, float, float], bool] | None:
    """Menghitung posisi sendi elbow (lutut), wrist, tip, dan derived bucket box secara akurat dan sangat cepat.

    Mendukung dua orientasi kerja:
    1. Boom-Mounted / Cabin POV: kamera terpasang di boom menghadap ke bawah arah arm & pit galian.
    2. Profile / External View: tampak luar ekskavator CAT 395 dengan boom melengkung tinggi.

    Returns:
        (lutut, wrist, tip, derived_bucket_box, is_boom_pov)
    """
    h, w = frame.shape[:2]

    # Cek apakah Boom POV: kamera tepat di kabin/boom menghadap ke depan/bawah
    is_boom_pov = is_cabin_view or (w < h) or (badan_box is not None and (badan_box[2] - badan_box[0]) > 0.70 * w and (badan_box[3] - badan_box[1]) > 0.60 * h)

    if is_boom_pov:
        truck_ref = trucks[0] if (trucks and len(trucks) > 0) else None
        if truck_ref is not None:
            top_y = max(h * 0.42, min(h * 0.70, truck_ref.y1))
            bx1 = max(0.0, w * 0.22)
            by1 = max(0.0, top_y - 45.0)
            bx2 = min(float(w), w * 0.78)
            by2 = min(float(h), top_y + 45.0)
            derived_bucket = (bx1, by1, bx2, by2)

            lutut = (w * 0.49, h * 0.05)
            wrist = (w * 0.49, by1 + 15.0)
            tip = (w * 0.49, by2 - 10.0)
        else:
            bx1 = max(0.0, w * 0.18)
            by1 = max(0.0, h * 0.65)
            bx2 = min(float(w), w * 0.82)
            by2 = min(float(h), h * 0.90)
            derived_bucket = (bx1, by1, bx2, by2)

            lutut = (w * 0.49, h * 0.05)
            wrist = (w * 0.49, h * 0.68)
            tip = (w * 0.49, h * 0.88)
        return lutut, wrist, tip, derived_bucket, True

    # Profile / External View: Downscale 4x untuk operasi OpenCV super enteng (< 5 ms di 1080p)
    scale = 0.25
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]

    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([12, 45, 40]), np.array([38, 255, 255]))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cnts, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    large_cnts = [c for c in cnts if cv2.contourArea(c) > 200]
    if not large_cnts:
        return None

    large_cnts.sort(key=cv2.contourArea, reverse=True)
    c0 = large_cnts[0]
    c0_pts = c0.reshape(-1, 2)

    # 1. Elbow (Puncak Boom): titik teratas lengkungan boom di sepertiga/setengah atas frame
    top_candidates = c0_pts[c0_pts[:, 1] < sh * 0.40]
    if len(top_candidates) < 5:
        top_candidates = c0_pts[c0_pts[:, 1] < sh * 0.60]
    if len(top_candidates) < 3:
        return None

    top_sorted = top_candidates[top_candidates[:, 1].argsort()]
    top_10 = top_sorted[:min(10, len(top_sorted))]
    el_xs = float(np.median(top_10[:, 0]))
    el_ys = float(np.median(top_10[:, 1]))

    inv_s = 1.0 / scale
    elbow_x = el_xs * inv_s
    elbow_y = el_ys * inv_s
    lutut = (elbow_x, elbow_y)

    # 2. Tentukan arah jangkauan arm (KIRI vs KANAN)
    arm_ke_kanan = False
    if badan_box is not None:
        badan_cx = (badan_box[0] + badan_box[2]) / 2.0
        arm_ke_kanan = (elbow_x > badan_cx + 40.0)
    else:
        arm_ke_kanan = (elbow_x > w * 0.55)

    # 3. Stick & Wrist: titik pada kontur ekskavator yang menjulur keluar dari siku boom
    # Mengambil langsung dari kontur c0 memastikan tidak ada gangguan tebing/batu di luar ekskavator
    # Batas jangkauan horizontal fisik stick ekskavator CAT 395 (maksimum 90 px skala kecil = 360 px pada 1080p)
    max_arm_reach_x = int(90 * (w / 1920.0))
    if arm_ke_kanan:
        stick_candidates = c0_pts[
            (c0_pts[:, 0] >= el_xs - 15) &
            (c0_pts[:, 0] <= el_xs + max_arm_reach_x) &
            (c0_pts[:, 1] > el_ys + 10) &
            (c0_pts[:, 1] <= sh * 0.95)
        ]
    else:
        stick_candidates = c0_pts[
            (c0_pts[:, 0] >= el_xs - max_arm_reach_x) &
            (c0_pts[:, 0] <= el_xs + 25) &
            (c0_pts[:, 1] > el_ys + 10) &
            (c0_pts[:, 1] <= sh * 0.95)
        ]

    if len(stick_candidates) >= 5:
        dist = np.linalg.norm(stick_candidates - np.array([el_xs, el_ys]), axis=1)
        # Ambil titik terjauh pada cabang stick dari siku
        furthest = stick_candidates[dist.argsort()[::-1][:8]]
        wr_xs = float(np.median(furthest[:, 0]))
        wr_ys = float(np.median(furthest[:, 1]))
        wrist_x = wr_xs * inv_s
        wrist_y = wr_ys * inv_s
    else:
        arm_len = 360.0 * (h / 1080.0)
        wrist_x = elbow_x + (0.35 * arm_len if arm_ke_kanan else -0.35 * arm_len)
        wrist_y = elbow_y + 0.85 * arm_len

    wrist = (wrist_x, wrist_y)

    # 4. Tip (Ujung gigi bucket) & Derived Bucket Bounding Box
    tip_dx = (35.0 if arm_ke_kanan else -35.0) * (w / 1920.0)
    tip_dy = 95.0 * (h / 1080.0)
    tip = (wrist_x + tip_dx, wrist_y + tip_dy)

    bx1 = max(0.0, min(wrist[0], tip[0]) - 85.0 * (w / 1920.0))
    by1 = max(0.0, min(wrist[1], tip[1]) - 35.0 * (h / 1080.0))
    bx2 = min(float(w), max(wrist[0], tip[0]) + 85.0 * (w / 1920.0))
    by2 = min(float(h), max(wrist[1], tip[1]) + 75.0 * (h / 1080.0))
    derived_bucket_box = (bx1, by1, bx2, by2)

    return lutut, wrist, tip, derived_bucket_box, False

@dataclass
class TruckTrack:
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float
    last_seen: float
    hits: int = 1

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    @property
    def area(self) -> float:
        return (self.x2 - self.x1) * (self.y2 - self.y1)

class Detector:
    """Deteksi multi-kelas + aturan komposisional ekskavator."""

    def __init__(self, cfg: DetectorConfig, zones: ZoneConfig, root: Path,
                 shared_model=None, shared_plate=None, model_lock: threading.Lock | None = None):
        self._model_lock = model_lock if model_lock is not None else threading.Lock()

        if shared_model is not None:
            self._model = shared_model
            self._names = self._model.names
        else:
            from ultralytics import YOLO

            model_path = Path(cfg.model)
            if not model_path.is_absolute():
                model_path = root / model_path
            if not model_path.is_file():
                raise FileNotFoundError(f"model tidak ditemukan: {model_path}")
            self._model = YOLO(str(model_path))
            self._names = self._model.names

        wanted = {c.lower() for c in cfg.classes}
        self._class_ids = {i for i, n in self._names.items() if n.lower() in wanted}
        if not self._class_ids:
            raise ValueError(
                f"model tidak punya kelas dari {sorted(wanted)}; "
                f"kelas yang ada: {sorted(self._names.values())}"
            )
        self._ids_urut = sorted(self._class_ids)

        self.cfg = cfg
        self.zones = zones
        self._prev_gray: np.ndarray | None = None
        self._hold: Objek | None = None
        self._truck_tracks: list[TruckTrack] = []
        self._hold_mulai: float | None = None
        self._hold_eks: ExcavatorKomposisi | None = None
        self._hold_eks_mulai: float | None = None
        self._hold_bucket: Objek | None = None
        self._hold_bucket_mulai: float | None = None
        self._hold_badan: Objek | None = None
        self._hold_badan_mulai: float | None = None

        # Temporal smoothers untuk anti-flicker
        self._smooth_exc_box: np.ndarray | None = None
        self._smooth_bucket_box: np.ndarray | None = None
        self._smooth_base: np.ndarray | None = None
        self._smooth_lutut: np.ndarray | None = None
        self._smooth_wrist: np.ndarray | None = None
        self._smooth_tip: np.ndarray | None = None

        # Model plat nomor terpisah (HuggingFace). Dimuat opsional supaya
        # engine tetap jalan kalau berkasnya tidak ada.
        if shared_plate is not None:
            self._plate = shared_plate
        else:
            self._plate = None
            if cfg.plate_model:
                p = Path(cfg.plate_model)
                if not p.is_absolute():
                    p = root / p
                if p.is_file():
                    from ultralytics import YOLO
                    self._plate = YOLO(str(p))
                else:
                    self._plate = None

    def _smooth_point(self, prev: np.ndarray | None, current: tuple[float, float], alpha: float = 0.30, max_step: float = 20.0) -> tuple[float, float]:
        if prev is None:
            return current
        cur = np.array(current, dtype=float)
        diff = cur - prev
        dist = float(np.linalg.norm(diff))
        if dist > max_step:
            cur = prev + (diff / dist) * max_step
        res = alpha * cur + (1.0 - alpha) * prev
        return (float(res[0]), float(res[1]))

    def _smooth_bbox(self, prev: np.ndarray | None, current: tuple[float, float, float, float], alpha: float = 0.25, max_step: float = 25.0) -> tuple[float, float, float, float]:
        if prev is None:
            return current
        cur = np.array(current, dtype=float)
        diff = cur - prev
        for i in range(4):
            if abs(diff[i]) > max_step:
                diff[i] = np.sign(diff[i]) * max_step
        res = alpha * (prev + diff) + (1.0 - alpha) * prev
        return (float(res[0]), float(res[1]), float(res[2]), float(res[3]))

    @property
    def class_names(self) -> list[str]:
        return [self._names[i] for i in self._ids_urut]

    # ------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> FrameResult:
        mulai = time.perf_counter()
        h, w = frame.shape[:2]
        set_ukuran_gambar(w, h)
        set_frame_citra(frame)
        hasil = FrameResult(frame_shape=(h, w))

        is_portrait = (w < h)
        is_cabin = (getattr(self.cfg, "view", "cabin") == "cabin")
        res_bench = None
        res_pit = None
        px1, py1 = 0, 0
        cx1, cy1 = 0, 0

        if not is_portrait:
            batch_inputs = [frame]
            if not is_cabin:
                # Focused patch loading bench dump truck di samping ekskavator (hanya untuk CCTV profil eksternal)
                cy1, cy2 = int(0.46 * h), int(0.82 * h)
                cx1, cx2 = int(0.14 * w), int(0.48 * w)
                bench_crop = frame[cy1:cy2, cx1:cx2]
                batch_inputs.append(bench_crop)
            else:
                # Focused patch pit galian & bucket di depan kaca kabin ekskavator
                py1, py2 = int(0.32 * h), int(0.98 * h)
                px1, px2 = int(0.30 * w), int(0.85 * w)
                pit_crop = frame[py1:py2, px1:px2]
                batch_inputs.append(pit_crop)

            # Inferensi batched sekaligus dalam 1 tensor batch GPU
            with self._model_lock:
                results = self._model.predict(
                    batch_inputs,
                    conf=self.cfg.release_confidence,
                    iou=self.cfg.iou,
                    imgsz=self.cfg.imgsz,
                    device=self.cfg.device,
                    classes=self._ids_urut,
                    verbose=False,
                )
            res = results[0]
            if not is_cabin:
                res_bench = results[1]
                res_pit = None
            else:
                res_bench = None
                res_pit = results[1]
        else:
            with self._model_lock:
                results = self._model.predict(
                    frame,
                    conf=self.cfg.release_confidence,
                    iou=self.cfg.iou,
                    imgsz=self.cfg.imgsz,
                    device=self.cfg.device,
                    classes=self._ids_urut,
                    verbose=False,
                )
            res = results[0]
            res_bench = None
            res_pit = None

        semua_objek: list[Objek] = []
        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy()
            conf = res.boxes.conf.cpu().numpy()
            for box, c, cf in zip(xyxy, cls, conf):
                x1, y1, x2, y2 = [float(v) for v in box]
                if x2 <= x1 or y2 <= y1:
                    continue
                nm = self._names[int(c)]
                o = Objek(nm, x1, y1, x2, y2, float(cf))
                semua_objek.append(o)

        # Proyeksikan deteksi truk dari bench crop ke koordinat frame utuh
        if res_bench is not None and res_bench.boxes is not None and len(res_bench.boxes):
            b_xyxy = res_bench.boxes.xyxy.cpu().numpy()
            b_cls = res_bench.boxes.cls.cpu().numpy()
            b_conf = res_bench.boxes.conf.cpu().numpy()
            for box, c, cf in zip(b_xyxy, b_cls, b_conf):
                nm = self._names[int(c)]
                if nm == "truck" and float(cf) >= self.cfg.confidence:
                    gx1 = float(box[0] + cx1)
                    gy1 = float(box[1] + cy1)
                    gx2 = float(box[2] + cx1)
                    gy2 = float(box[3] + cy1)
                    gw = gx2 - gx1
                    gh = gy2 - gy1
                    if gw >= 0.15 * w and gh >= 0.10 * h and (gw / max(1.0, gh)) >= 0.65:
                        semua_objek.append(Objek("truck", gx1, gy1, gx2, gy2, float(cf)))

        # Proyeksikan deteksi bucket dan truck dari pit crop ke koordinat frame utuh (khusus cabin POV)
        if res_pit is not None and res_pit.boxes is not None and len(res_pit.boxes):
            p_xyxy = res_pit.boxes.xyxy.cpu().numpy()
            p_cls = res_pit.boxes.cls.cpu().numpy()
            p_conf = res_pit.boxes.conf.cpu().numpy()
            for box, c, cf in zip(p_xyxy, p_cls, p_conf):
                nm = self._names[int(c)]
                gx1 = float(box[0] + px1)
                gy1 = float(box[1] + py1)
                gx2 = float(box[2] + px1)
                gy2 = float(box[3] + py1)
                gw = gx2 - gx1
                gh = gy2 - gy1
                # Tolak jika berada di sisi spion/pilar kiri kabin (gx1 < 0.28 * w)
                if gx2 <= 0.28 * w or gx1 < 0.26 * w:
                    continue
                if nm == "truck" and float(cf) >= self.cfg.release_confidence:
                    if gw >= 0.16 * w and gh >= 0.10 * h:
                        semua_objek.append(Objek("truck", gx1, gy1, gx2, gy2, float(cf)))
                elif nm == "excavator" and float(cf) >= self.cfg.release_confidence:
                    # Di sudut pandang kabin (dashcam), deteksi struktur di pit galian adalah bagian boom/arm/bucket
                    if gy1 < 0.45 * h and gh < 0.50 * h:
                        semua_objek.append(Objek("bucket", gx1, gy1, gx2, gy2, float(cf)))
                elif nm == "bucket" and float(cf) >= self.cfg.release_confidence:
                    if gw >= 0.10 * w and gh >= 0.08 * h:
                        semua_objek.append(Objek("bucket", gx1, gy1, gx2, gy2, float(cf)))

        # Filter cabin mirror & identifikasi arm/bucket pada frame utuh (khusus cabin view)
        if is_cabin:
            truck_proposals = [t for t in semua_objek if t.kelas == "truck"]
            cabin_filtered: list[Objek] = []
            for o in semua_objek:
                # Tolak false positive excavator/truk di spion dan pilar kiri kaca kabin (x < 0.28 * w)
                if (o.cx < 0.28 * w or o.x2 < 0.26 * w) and o.kelas in ["excavator", "truck"]:
                    continue
                # Di sudut pandang kabin, jika model mendeteksi struktur ekskavator di area depan:
                if o.kelas == "excavator" and 0.28 * w <= o.cx <= 0.88 * w and o.y2 >= 0.35 * h:
                    tumpang_truk = any(
                        self._iou(o, tr) > 0.25 or (o.x1 >= tr.x1 - 25 and o.x2 <= tr.x2 + 25 and o.y2 >= tr.y1)
                        for tr in truck_proposals
                    )
                    if tumpang_truk:
                        # Bila bertumpuk dengan truk:
                        # Bagian atas bak truk adalah bucket yang sedang menuang
                        if o.y1 < 0.38 * h and (o.y2 - o.y1) < 0.55 * h:
                            cabin_filtered.append(Objek("bucket", o.x1, o.y1, o.x2, o.y2, o.conf))
                        # Kotak yang menutupi bagian bawah adalah badan truk (sudah diwakili oleh truck)
                    else:
                        # Tidak bertumpuk dengan truk: jangan ubah seluruh kaca kabin menjadi bucket!
                        # Hanya jadikan bucket jika tingginya wajar (< 0.40 * h)
                        if (o.y2 - o.y1) < 0.40 * h:
                            cabin_filtered.append(Objek("bucket", o.x1, o.y1, o.x2, o.y2, o.conf))
                else:
                    cabin_filtered.append(o)
            semua_objek = cabin_filtered

        # Gabungkan proposal bucket yang tumpang tindih dari full-frame & pit patch
        raw_buckets_list = [o for o in semua_objek if o.kelas == "bucket"]
        merged_buckets: list[Objek] = []
        for b in sorted(raw_buckets_list, key=lambda x: -x.conf):
            overlapped = False
            for i, m in enumerate(merged_buckets):
                if self._iou(b, m) > 0.30:
                    nx1 = min(b.x1, m.x1)
                    ny1 = min(b.y1, m.y1)
                    nx2 = max(b.x2, m.x2)
                    ny2 = max(b.y2, m.y2)
                    nconf = max(b.conf, m.conf)
                    merged_buckets[i] = Objek("bucket", nx1, ny1, nx2, ny2, nconf)
                    overlapped = True
                    break
            if not overlapped:
                merged_buckets.append(b)

        non_buckets = [o for o in semua_objek if o.kelas != "bucket"]
        semua_objek = non_buckets + merged_buckets

        # Gabungkan proposal truk yang tumpang tindih dari full-frame & bench patch
        raw_trucks_list = [o for o in semua_objek if o.kelas == "truck"]
        merged_trucks: list[Objek] = []
        for t in sorted(raw_trucks_list, key=lambda x: -x.conf):
            overlapped = False
            for i, m in enumerate(merged_trucks):
                if self._iou(t, m) > 0.35:
                    nx1 = min(t.x1, m.x1)
                    ny1 = min(t.y1, m.y1)
                    nx2 = max(t.x2, m.x2)
                    ny2 = max(t.y2, m.y2)
                    nconf = max(t.conf, m.conf)
                    merged_trucks[i] = Objek("truck", nx1, ny1, nx2, ny2, nconf)
                    overlapped = True
                    break
            if not overlapped:
                merged_trucks.append(t)

        non_trucks = [o for o in semua_objek if o.kelas != "truck"]
        semua_objek = non_trucks + merged_trucks

        # Disambiguasi truck vs excavator:
        # Gunakan True IoU (bukan rasio penahanan), agar truk di bawah boom tidak terhapus
        raw_trucks = [o for o in semua_objek if o.kelas == "truck"]
        raw_exc = [o for o in semua_objek if o.kelas == "excavator"]

        filtered_objek: list[Objek] = []
        for o in semua_objek:
            if o.kelas == "truck":
                # Hanya tolak bila bertumpukan sangat tinggi (> 0.65 True IoU) dengan excavator yang jauh lebih yakin
                conflict = any(self._iou(o, e) > 0.65 and e.conf > o.conf + 0.25 for e in raw_exc)
                if not conflict:
                    filtered_objek.append(o)
            elif o.kelas == "excavator":
                # Tolak bila kotak excavator bertumpukan > 0.65 True IoU dengan truk yang lebih yakin
                conflict = any(self._iou(o, t) > 0.65 and t.conf >= o.conf for t in raw_trucks)
                if not conflict:
                    filtered_objek.append(o)
            else:
                filtered_objek.append(o)
        semua_objek = filtered_objek

        # 1. Multi-Truck Tracking dengan Konfirmasi Hits dan Filter False Positive
        truck_kandidat = [o for o in semua_objek if o.kelas == "truck"]
        sekarang_t = time.monotonic()
        updated_tracks: list[TruckTrack] = []
        unmatched = list(truck_kandidat)

        for tr in self._truck_tracks:
            best_cand = None
            best_iou = 0.0
            tr_obj = Objek("truck", tr.x1, tr.y1, tr.x2, tr.y2, tr.conf)
            for cand in unmatched:
                iou = self._iou(tr_obj, cand)
                if iou > best_iou and iou > 0.20:
                    best_iou = iou
                    best_cand = cand

            if best_cand is not None:
                tr.x1 = tr.x1 * 0.70 + best_cand.x1 * 0.30
                tr.y1 = tr.y1 * 0.70 + best_cand.y1 * 0.30
                tr.x2 = tr.x2 * 0.70 + best_cand.x2 * 0.30
                tr.y2 = tr.y2 * 0.70 + best_cand.y2 * 0.30
                tr.conf = max(best_cand.conf, tr.conf * 0.90)
                tr.last_seen = sekarang_t
                tr.hits += 1
                updated_tracks.append(tr)
                unmatched.remove(best_cand)
            else:
                umur = sekarang_t - tr.last_seen
                max_hold = 0.6 if is_portrait else self.cfg.hold_seconds
                # HANYA tahan track yang sudah terkonfirmasi minimal 2 frame (bukan noise 1 frame)
                if tr.hits >= 2 and umur <= max_hold:
                    redup = tr.conf * (1.0 - (umur / max_hold) * 0.60)
                    if redup >= self.cfg.release_confidence:
                        tr.conf = redup
                        updated_tracks.append(tr)

        # Hanya inisialisasi track baru jika confidence CUKUP TINGGI (>= self.cfg.confidence)
        # dan dimensi proporsional (bukan tiang jendela sempit)
        for cand in unmatched:
            w_c = cand.x2 - cand.x1
            h_c = cand.y2 - cand.y1
            min_c = self.cfg.release_confidence if (w_c >= 0.16 * w and h_c >= 0.12 * h) else self.cfg.confidence
            if cand.conf >= min_c and w_c >= 0.12 * w and h_c >= 0.08 * h and (w_c / max(1.0, h_c) >= 0.60):
                updated_tracks.append(TruckTrack(cand.x1, cand.y1, cand.x2, cand.y2, cand.conf, sekarang_t, hits=1))

        self._truck_tracks = updated_tracks

        # Masukkan HANYA truk yang terkonfirmasi (hits >= 2 atau confidence tinggi >= 0.40)
        # Di sudut pandang kabin dashcam, operator hanya mengisi 1 dump truck aktif di depan kaca kabin.
        # Pada profil CCTV luar, izinkan hingga 2 truk.
        max_trucks = 1 if is_cabin else 2
        # Di kabin, pastikan pusat truk berada di area bukaan kaca depan (bukan di pintu kaca samping sopir)
        confirmed_tracks = [
            tr for tr in sorted(self._truck_tracks, key=lambda t: -t.area)
            if (tr.hits >= 2 or tr.conf >= 0.40) and tr.conf >= self.cfg.release_confidence
            and (not is_cabin or ((tr.x1 + tr.x2) * 0.5 >= 0.28 * w))
        ]

        for tr in confirmed_tracks[:max_trucks]:
            is_held = (sekarang_t - tr.last_seen > 0.25)
            t_obj = Objek("truck", tr.x1, tr.y1, tr.x2, tr.y2, tr.conf, ditahan=is_held)
            if not any(self._iou(o, t_obj) > 0.50 for o in hasil.objek if o.kelas == "truck"):
                hasil.objek.append(t_obj)

        if any(o.ditahan for o in hasil.objek if o.kelas == "truck"):
            hasil.ditahan = True

        # 2. Kelompokkan BADAN EXCAVATOR
        # Cari excavator utama (alat berat primer). Di sudut pandang kabin (dashcam),
        # host machine adalah EXC-07 tempat kamera terpasang, bukan objek luar di spion.
        is_cabin = (getattr(self.cfg, "view", "cabin") == "cabin")
        exc_kandidat = [
            o for o in semua_objek
            if o.kelas == "excavator" and o.conf >= self.cfg.confidence
            and not is_cabin
        ]
        primary_exc = None
        if exc_kandidat:
            # Utamakan excavator yang besar (luas area) atau berada di tengah
            e_best = max(exc_kandidat, key=lambda e: e.conf * 0.4 + (e.area / (w * h)) * 0.6)
            # Smooth bounding box agar stabil dan tidak melompat ratusan piksel
            sb = self._smooth_bbox(self._smooth_exc_box, e_best.bbox, alpha=0.35, max_step=35.0)
            self._smooth_exc_box = np.array(sb, dtype=float)
            e_best.x1, e_best.y1, e_best.x2, e_best.y2 = sb
            hasil.objek.append(e_best)
            self._hold_badan = e_best
            self._hold_badan_mulai = time.monotonic()
            primary_exc = e_best
        elif self._hold_badan is not None and self._hold_badan_mulai is not None:
            umur_e = time.monotonic() - self._hold_badan_mulai
            if umur_e <= self.cfg.eks_hold_seconds:
                redup_e = max(0.0, self._hold_badan.conf * (1.0 - umur_e / self.cfg.eks_hold_seconds))
                e_ditahan = Objek("excavator", self._hold_badan.x1, self._hold_badan.y1,
                                  self._hold_badan.x2, self._hold_badan.y2, redup_e, ditahan=True)
                hasil.objek.append(e_ditahan)
                primary_exc = e_ditahan
            else:
                self._hold_badan = None
                self._hold_badan_mulai = None

        # 3. Kinematika & Kelompokkan BUCKET
        semua_trucks = [o for o in hasil.objek if o.kelas == "truck"]
        raw_b_box = primary_exc.bbox if primary_exc else None
        kin = None
        is_cabin = (getattr(self.cfg, "view", "cabin") == "cabin")
        kin_res = _kinematika_lengan(frame, trucks=semua_trucks, badan_box=raw_b_box, is_cabin_view=is_cabin)
        if kin_res is not None:
            raw_lutut, raw_wrist, raw_tip, raw_d_box, is_boom_pov = kin_res
            # Jika ada lompatan besar (scene change atau video loop), reset smoothers agar tidak ada lag
            if self._smooth_lutut is not None:
                jump_lutut = np.linalg.norm(np.array(raw_lutut) - self._smooth_lutut)
                jump_wrist = np.linalg.norm(np.array(raw_wrist) - self._smooth_wrist) if self._smooth_wrist is not None else 0.0
                if jump_lutut > 180.0 or jump_wrist > 200.0:
                    self._smooth_lutut = None
                    self._smooth_wrist = None
                    self._smooth_tip = None
                    self._smooth_bucket_box = None
            s_lutut = self._smooth_point(self._smooth_lutut, raw_lutut, alpha=0.35, max_step=35.0)
            self._smooth_lutut = np.array(s_lutut, dtype=float)

            s_wrist = self._smooth_point(self._smooth_wrist, raw_wrist, alpha=0.35, max_step=35.0)
            self._smooth_wrist = np.array(s_wrist, dtype=float)

            s_tip = self._smooth_point(self._smooth_tip, raw_tip, alpha=0.35, max_step=35.0)
            self._smooth_tip = np.array(s_tip, dtype=float)

            s_d_box = self._smooth_bbox(getattr(self, "_smooth_kin_bucket_box", None), raw_d_box, alpha=0.35, max_step=35.0)
            self._smooth_kin_bucket_box = np.array(s_d_box, dtype=float)

            kin = (s_lutut, s_wrist, s_tip, s_d_box)

        bucket_kandidat = [
            o for o in semua_objek
            if o.kelas == "bucket" and not _terlihat_langit(frame, o.x1, o.y1, o.x2, o.y2)
        ]
        bucket_kuat = [o for o in bucket_kandidat if o.conf >= self.cfg.release_confidence]

        if bucket_kuat:
            b_best = max(bucket_kuat, key=lambda b: b.conf)
            sb = self._smooth_bbox(self._smooth_bucket_box, b_best.bbox, alpha=0.30, max_step=25.0)
            self._smooth_bucket_box = np.array(sb, dtype=float)
            b_best.x1, b_best.y1, b_best.x2, b_best.y2 = sb
            hasil.objek.append(b_best)
            self._hold_bucket = b_best
            self._hold_bucket_mulai = time.monotonic()
        elif kin is not None:
            # Kamera kabin (dashcam) atau eksternal: turunkan posisi bucket dari kinematika boom & bak truk
            _, _, _, d_box = kin
            b_kin = Objek("bucket", d_box[0], d_box[1], d_box[2], d_box[3], 0.70)
            tumpang_truk = any(self._bertumpuk(b_kin, t) > 0.40 for t in semua_trucks) if not is_cabin else False
            if not tumpang_truk:
                hasil.objek.append(b_kin)
                self._hold_bucket = b_kin
                self._hold_bucket_mulai = time.monotonic()
        elif self._hold_bucket is not None and self._hold_bucket_mulai is not None:
            umur_b = time.monotonic() - self._hold_bucket_mulai
            if umur_b <= 1.0:
                redup_b = max(0.0, self._hold_bucket.conf * (1.0 - umur_b / 1.0))
                if redup_b >= self.cfg.release_confidence:
                    b_ditahan = Objek("bucket", self._hold_bucket.x1, self._hold_bucket.y1,
                                      self._hold_bucket.x2, self._hold_bucket.y2, redup_b, ditahan=True)
                    hasil.objek.append(b_ditahan)
                else:
                    self._hold_bucket = None
                    self._hold_bucket_mulai = None
            else:
                self._hold_bucket = None
                self._hold_bucket_mulai = None

        hasil.ekskavator = self._gabung_ekskavator(hasil.buckets, hasil.badan, w, h, frame=frame, hasil_ref=hasil, kin=kin)
        hasil.ekskavator = self._tahan_ekskavator(hasil.ekskavator)
        hasil.objek.extend(self._deteksi_plat(frame))
        hasil.dig_motion = self._gerak_di_zona_gali(frame)
        hasil.infer_ms = (time.perf_counter() - mulai) * 1000.0
        return hasil


# ------------------------------------------------------------------
    def _deteksi_plat(self, frame: np.ndarray) -> list[Objek]:
        """Plat nomor lewat model terpisah (di-throttle setiap 10 frame untuk efisiensi)."""
        if self._plate is None:
            return []
        
        self._plate_cnt = getattr(self, "_plate_cnt", 0) + 1
        if self._plate_cnt % 10 != 0 and hasattr(self, "_cached_plates"):
            return self._cached_plates

        try:
            with self._model_lock:
                res = self._plate.predict(
                    frame, conf=self.cfg.plate_confidence,
                    imgsz=self.cfg.plate_imgsz,
                    device=self.cfg.device, verbose=False,
                )[0]
        except Exception:  # noqa: BLE001
            return []
        if res.boxes is None or len(res.boxes) == 0:
            self._cached_plates = []
            return []

        hasil: list[Objek] = []
        for box, cf in zip(res.boxes.xyxy.cpu().numpy(),
                           res.boxes.conf.cpu().numpy()):
            x1, y1, x2, y2 = [float(v) for v in box]
            if x2 <= x1 or y2 <= y1:
                continue
            hasil.append(Objek("plate", x1, y1, x2, y2, float(cf)))
        # plat paling yakin dulu
        hasil.sort(key=lambda o: -o.conf)
        self._cached_plates = hasil[:3]
        return self._cached_plates


    # ------------------------------------------------------------------
    def _gabung_ekskavator(self, buckets: list[Objek], badan: list[Objek],
                            w: int, h: int, frame: np.ndarray | None = None,
                            hasil_ref: FrameResult | None = None,
                            kin: tuple | None = None) -> list[ExcavatorKomposisi]:
        """Ekskavator = bucket + lengan penyambung + badan kendaraan.

        Model dilatih dengan label 'excavator' untuk badan saja. Bila model
        gagal mendeteksi bucket (atau bucket terhalang bak truk), kinematika
        lengan fisik mengekstrak posisi siku (elbow), pergelangan (wrist),
        dan scoop bucket secara langsung dari kontur alat berat.
        """
        is_cabin = (getattr(self.cfg, "view", "cabin") == "cabin")
        if not buckets and not badan:
            if is_cabin and kin is not None:
                _, _, _, d_box = kin
                b_kin = Objek("bucket", d_box[0], d_box[1], d_box[2], d_box[3], 0.70)
                buckets = [b_kin]
                if hasil_ref is not None and not any(o.kelas == "bucket" for o in hasil_ref.objek):
                    hasil_ref.objek.append(b_kin)
            else:
                return []

        if kin is None and frame is not None:
            trucks_ref = hasil_ref.trucks if hasil_ref is not None else None
            badan_box_ref = badan[0].bbox if badan else None
            kin = _kinematika_lengan(frame, trucks=trucks_ref, badan_box=badan_box_ref)
        is_cabin = (getattr(self.cfg, "view", "cabin") == "cabin")
        kandidat_badan: list[Objek | None] = list(badan)
        hasil: list[ExcavatorKomposisi] = []
        dipakai: set[int] = set()

        for b in sorted(buckets, key=lambda o: -o.conf):
            pairing = None
            for i, s in enumerate(kandidat_badan):
                if s is None or i in dipakai:
                    continue
                jarak = ((b.cx - s.cx) / w) ** 2 + ((b.cy - s.cy) / h) ** 2
                if jarak ** 0.5 <= JARAK_BUCKET_BADAN:
                    pairing = (i, s, jarak ** 0.5)
                    break

            l_pt = kin[0] if kin else None
            if kin is not None:
                w_pt = kin[1]
                t_pt = kin[2]
            else:
                w_pt = (b.cx, b.y1)
                t_pt = (b.cx, b.y2)

            if pairing is not None:
                i, s, jarak = pairing
                dipakai.add(i)
                conf = round((b.conf * 0.55 + s.conf * 0.45) * (1.0 - jarak * 0.3), 4)
                if l_pt is not None and l_pt[0] <= s.cx:
                    raw_base = (s.x1 + s.w * 0.44, s.y1 + s.h * 0.43)
                else:
                    raw_base = (s.x1 + s.w * 0.46, s.y1 + s.h * 0.50)
                s_base = self._smooth_point(self._smooth_base, raw_base, alpha=0.30, max_step=15.0)
                self._smooth_base = np.array(s_base, dtype=float)
                hasil.append(ExcavatorKomposisi(
                    bucket=b, badan=s,
                    lengan=((s.cx, s.cy), (b.cx, b.cy)),
                    conf=conf,
                    komponen={"bucket": True, "lengan": True, "badan": True},
                    lutut_pt=l_pt, wrist_pt=w_pt, tip_pt=t_pt,
                    base_pt=s_base,
                ))
            else:
                if is_cabin:
                    # Di sudut pandang kabin, lengan terhubung dari pangkal boom atas ke bucket
                    base_pt = (w * 0.49, h * 0.05)
                    elbow_pt = (w * 0.49, h * 0.25)
                    wrist_pt = (b.cx, b.y1)
                    tip_pt = (b.cx, max(b.y1 + 10.0, b.y2 - 10.0))
                    hasil.append(ExcavatorKomposisi(
                        bucket=b, badan=None,
                        lengan=(base_pt, (b.cx, b.cy)),
                        conf=b.conf,
                        komponen={"bucket": True, "lengan": True, "badan": True},
                        lutut_pt=elbow_pt, wrist_pt=wrist_pt, tip_pt=tip_pt,
                        base_pt=base_pt,
                    ))
                else:
                    badan_ref = self._hold_badan if self._hold_badan is not None else None
                    s_base = None
                    if badan_ref is not None:
                        if l_pt is not None and l_pt[0] <= badan_ref.cx:
                            raw_base = (badan_ref.x1 + badan_ref.w * 0.44, badan_ref.y1 + badan_ref.h * 0.43)
                        else:
                            raw_base = (badan_ref.x1 + badan_ref.w * 0.46, badan_ref.y1 + badan_ref.h * 0.50)
                        s_base = self._smooth_point(self._smooth_base, raw_base, alpha=0.30, max_step=15.0)
                        self._smooth_base = np.array(s_base, dtype=float)
                    lengan_ref = ((badan_ref.cx, badan_ref.cy), (b.cx, b.cy)) if badan_ref is not None else None
                    hasil.append(ExcavatorKomposisi(
                        bucket=b, badan=badan_ref,
                        lengan=lengan_ref,
                        conf=round(b.conf * 0.5, 4),
                        komponen={"bucket": True, "lengan": badan_ref is not None, "badan": badan_ref is not None},
                        lutut_pt=l_pt, wrist_pt=w_pt, tip_pt=t_pt,
                        base_pt=s_base,
                    ))

        # Badan yang tersisa (terlihat, tapi tidak punya bucket hasil deteksi YOLO)
        is_cabin = (getattr(self.cfg, "view", "cabin") == "cabin")
        for i, s in enumerate(kandidat_badan):
            if s is None or i in dipakai:
                continue
            if kin is not None:
                lutut, wrist, tip, d_box = kin
                if s is not None:
                    if lutut[0] <= s.cx:
                        raw_base = (s.x1 + s.w * 0.44, s.y1 + s.h * 0.43)
                    else:
                        raw_base = (s.x1 + s.w * 0.46, s.y1 + s.h * 0.50)
                    s_base = self._smooth_point(self._smooth_base, raw_base, alpha=0.30, max_step=15.0)
                    self._smooth_base = np.array(s_base, dtype=float)
                    lengan_ref = ((s.cx, s.cy), (d_box[0], d_box[1]))
                else:
                    s_base = (w * 0.49, h * 0.05)
                    lengan_ref = (s_base, ((d_box[0] + d_box[2]) / 2, (d_box[1] + d_box[3]) / 2))
                b_syn = Objek("bucket", d_box[0], d_box[1], d_box[2], d_box[3], 0.70)
                if hasil_ref is not None and not any(o.kelas == "bucket" for o in hasil_ref.objek):
                    hasil_ref.objek.append(b_syn)
                hasil.append(ExcavatorKomposisi(
                    bucket=b_syn, badan=s,
                    lengan=lengan_ref,
                    conf=0.70 if s is None else round(s.conf * 0.80, 4),
                    komponen={"bucket": True, "lengan": True, "badan": s is not None},
                    lutut_pt=lutut, wrist_pt=wrist, tip_pt=tip,
                    base_pt=s_base,
                ))
            else:
                hasil.append(ExcavatorKomposisi(
                    bucket=None, badan=s,
                    lengan=None,
                    conf=round(s.conf * 0.75, 4),
                    komponen={"bucket": False, "lengan": False, "badan": True},
                ))
        return hasil

    # ------------------------------------------------------------------
    def _tahan_ekskavator(
            self, hasil: list[ExcavatorKomposisi]) -> list[ExcavatorKomposisi]:
        """Penahanan sementara untuk ekskavator."""
        now = time.monotonic()
        if hasil:
            self._hold_eks = max(hasil, key=lambda e: e.conf)
            self._hold_eks_mulai = now
            return hasil

        if self._hold_eks is None or self._hold_eks_mulai is None:
            return []
        umur = now - self._hold_eks_mulai
        if umur > self.cfg.eks_hold_seconds:
            self._hold_eks = None
            self._hold_eks_mulai = None
            return []

        sisa = 1.0 - umur / self.cfg.eks_hold_seconds
        e = self._hold_eks
        return [ExcavatorKomposisi(
            bucket=e.bucket, badan=e.badan, lengan=e.lengan,
            conf=round(e.conf * 0.6 * sisa, 4),
            komponen={**e.komponen, "ditahan": True},
            lutut_pt=e.lutut_pt, wrist_pt=e.wrist_pt, tip_pt=e.tip_pt,
            base_pt=e.base_pt,
        )]

    @staticmethod
    def _iou(a: Objek, b: Objek) -> float:
        """True Intersection over Union (IoU) between two bounding boxes (0.0 to 1.0)."""
        x1 = max(a.x1, b.x1); y1 = max(a.y1, b.y1)
        x2 = min(a.x2, b.x2); y2 = min(a.y2, b.y2)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        inter = (x2 - x1) * (y2 - y1)
        union = a.area + b.area - inter
        return inter / max(1.0, union)

    @staticmethod
    def _bertumpuk(a: Objek, b: Objek) -> bool:
        """Berapa besar kotak a berada di dalam kotak b (0-1)."""
        x1 = max(a.x1, b.x1); y1 = max(a.y1, b.y1)
        x2 = min(a.x2, b.x2); y2 = min(a.y2, b.y2)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        return ((x2 - x1) * (y2 - y1)) / max(1.0, a.area)

    # ------------------------------------------------------------------
    def _gerak_di_zona_gali(self, frame: np.ndarray) -> float:
        """Fraksi piksel di zona gali yang berubah sejak frame sebelumnya."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        h, w = gray.shape[:2]

        x1, y1, x2, y2 = self.zones.dig
        px1, py1 = int(max(0, x1 * w)), int(max(0, y1 * h))
        px2, py2 = int(min(w, x2 * w)), int(min(h, y2 * h))
        if px2 - px1 < 16 or py2 - py1 < 16:
            return 0.0

        roi = gray[py1:py2, px1:px2]
        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            self._prev_gray = gray
            return 0.0

        diff = cv2.absdiff(roi, self._prev_gray[py1:py2, px1:px2])
        _, mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        gerak = float(np.count_nonzero(mask)) / float(mask.size)
        self._prev_gray = gray
        return gerak

    def reset(self) -> None:
        self._prev_gray = None
        self._hold = None
        self._hold_mulai = None
        self._hold_eks = None
        self._hold_eks_mulai = None
        self._hold_badan = None
        self._hold_badan_mulai = None
        self._hold_bucket = None
        self._hold_bucket_mulai = None
        self._smooth_exc_box = None
        self._smooth_bucket_box = None
        self._smooth_base = None
        self._smooth_lutut = None
        self._smooth_wrist = None
        self._smooth_tip = None