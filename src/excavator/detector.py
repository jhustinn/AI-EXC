"""Mesin deteksi objek alat berat."""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from .config import DetectorConfig, ZoneConfig
from .objek import ExcavatorKomposisi, FrameResult, Objek

# jarak maksimum pusat bucket ke pusat badan agar dianggap satu mesin
JARAK_BUCKET_BADAN = 0.75
# bucket dianggap "di atas" bila pusatnya lebih tinggi dari badan
SELISIH_TINGGI_BUCKET = 0.05


class Detector:
    """Deteksi multi-kelas + aturan komposisional ekskavator."""

    def __init__(self, cfg: DetectorConfig, zones: ZoneConfig, root: Path):
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
                f"model {model_path.name} tidak punya kelas dari {sorted(wanted)}; "
                f"kelas yang ada: {sorted(self._names.values())}"
            )
        self._ids_urut = sorted(self._class_ids)

        self.cfg = cfg
        self.zones = zones
        self._prev_gray: np.ndarray | None = None
        self._hold: Objek | None = None
        self._hold_eks: ExcavatorKomposisi | None = None
        self._hold_eks_mulai: float | None = None
        self._hold_mulai: float | None = None

        # Model plat nomor terpisah (HuggingFace). Dimuat opsional supaya
        # engine tetap jalan kalau berkasnya tidak ada.
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

    @property
    def class_names(self) -> list[str]:
        return [self._names[i] for i in self._ids_urut]

    # ------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> FrameResult:
        mulai = time.perf_counter()
        h, w = frame.shape[:2]
        hasil = FrameResult(frame_shape=(h, w))

        res = self._model.predict(
            frame,
            conf=self.cfg.release_confidence,
            iou=self.cfg.iou,
            imgsz=self.cfg.imgsz,
            device=self.cfg.device,
            classes=self._ids_urut,
            verbose=False,
        )[0]

        kuat: list[Objek] = []
        lemah: list[Objek] = []
        if res.boxes is not None and len(res.boxes):
            xyxy = res.boxes.xyxy.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy()
            conf = res.boxes.conf.cpu().numpy()
            for box, c, cf in zip(xyxy, cls, conf):
                x1, y1, x2, y2 = [float(v) for v in box]
                if x2 <= x1 or y2 <= y1:
                    continue
                o = Objek(self._names[int(c)], x1, y1, x2, y2, float(cf))
                if o.kelas == "truck":
                    lebar = o.w / w
                    if not (self.cfg.min_width_ratio <= lebar <= self.cfg.max_width_ratio):
                        continue
                (kuat if o.conf >= self.cfg.confidence else lemah).append(o)

        # objek kecil seperti platnomor boleh confidence lebih rendah,
        # karena ukurannya kecil dan model cenderung tidak yakin
        for o in lemah:
            if o.kelas in self.cfg.low_conf_classes and o.conf >= self.cfg.low_conf_floor:
                kuat.append(o)

        # penahanan hanya untuk truck: dia target zona tuang dan ukurannya
        # besar, jadi stabil. Bucket kecil tidak ditahan karena posisinya
        # berubah cepat.
        truck_kuat = [o for o in kuat if o.kelas == "truck"]
        truck_lemah = [o for o in lemah if o.kelas == "truck"]
        lainnya = [o for o in kuat if o.kelas != "truck"]

        if truck_kuat:
            truck_kuat.sort(key=lambda o: -o.area)
            hasil.objek = lainnya + truck_kuat[:1]
            self._hold = truck_kuat[0]
            self._hold_mulai = time.monotonic()
        elif truck_lemah and self._hold is not None:
            truck_lemah.sort(key=lambda o: -o.area)
            t = truck_lemah[0]
            ditahan = Objek("truck", t.x1, t.y1, t.x2, t.y2, t.conf, ditahan=True)
            hasil.objek = lainnya + [ditahan]
            hasil.ditahan = True
            self._hold = ditahan
            self._hold_mulai = time.monotonic()
        elif self._hold is not None and self._hold_mulai is not None:
            umur = time.monotonic() - self._hold_mulai
            if umur <= self.cfg.hold_seconds:
                redup = max(0.0, self._hold.conf * (1.0 - umur / self.cfg.hold_seconds))
                ditahan = Objek("truck", self._hold.x1, self._hold.y1,
                                self._hold.x2, self._hold.y2, redup, ditahan=True)
                hasil.objek = lainnya + [ditahan]
                hasil.ditahan = True
            else:
                self._hold = None
                self._hold_mulai = None

        hasil.ekskavator = self._gabung_ekskavator(hasil.buckets, hasil.badan, w, h)
        hasil.ekskavator = self._tahan_ekskavator(hasil.ekskavator)
        hasil.objek.extend(self._deteksi_plat(frame))
        hasil.dig_motion = self._gerak_di_zona_gali(frame)
        hasil.infer_ms = (time.perf_counter() - mulai) * 1000.0
        return hasil

    # ------------------------------------------------------------------
    def _deteksi_plat(self, frame: np.ndarray) -> list[Objek]:
        """Plat nomor lewat model terpisah.

        Plat nyaris tidak terlihat di video referensi, jadi kelas ini tidak
        dilatih bersama model utama. Model publik dipakai apa adanya.
        """
        if self._plate is None:
            return []
        try:
            res = self._plate.predict(
                frame, conf=self.cfg.plate_confidence,
                imgsz=self.cfg.plate_imgsz,
                device=self.cfg.device, verbose=False,
            )[0]
        except Exception:  # noqa: BLE001
            return []
        if res.boxes is None or len(res.boxes) == 0:
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
        return hasil[:3]

    # ------------------------------------------------------------------
    def _gabung_ekskavator(self, buckets: list[Objek], badan: list[Objek],
                            w: int, h: int) -> list[ExcavatorKomposisi]:
        """Ekskavator = bucket + lengan penyambung + badan kendaraan.

        Model dilatih dengan label 'excavator' untuk badan saja. Kalau model
        gagal menemukan badan tapi bucket terlihat jelas, bucket + area
        tubuh mesin di bawahnya tetap dihitung sebagai ekskavator - dengan
        confidence lebih rendah karena tidak ada konfirmasi badan.
        """
        if not buckets and not badan:
            return []

        # Badan ekskavator yang terlihat jelas HARUS dihitung, walau bucket
        # tidak terdeteksi. Sebelumnya `if not buckets: return []` membuat
        # seluruh ekskavator hilang begitu bucket meleset - padahal badan
        # mesinnya ada di layar. Dilakukan di bawah, setelah pairing.

        # badan hasil deteksi langsung
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

            if pairing is not None:
                i, s, jarak = pairing
                dipakai.add(i)
                conf = round((b.conf * 0.55 + s.conf * 0.45) * (1.0 - jarak * 0.3), 4)
                hasil.append(ExcavatorKomposisi(
                    bucket=b, badan=s,
                    lengan=((s.cx, s.cy), (b.cx, b.cy)),
                    conf=conf,
                    komponen={"bucket": True, "lengan": True, "badan": True},
                ))
            else:
                # hanya bucket: ekskavator belum bisa dipastikan
                hasil.append(ExcavatorKomposisi(
                    bucket=b, badan=b,
                    lengan=((b.cx, b.cy), (b.cx, b.cy)),
                    conf=round(b.conf * 0.5, 4),
                    komponen={"bucket": True, "lengan": False, "badan": False},
                ))

        # Badan yang tersisa (terlihat, tapi tidak punya bucket yang terpasang).
        # HANYA bila tidak ada bucket sama sekali di frame ini. Kalau bucket
        # ada, badan sisa sudah terwakili oleh ekskavator hasil pairing di atas
        # - menghitung lagi akan membuat satu mesin appear dua kali.
        for i, s in enumerate(kandidat_badan):
            if s is None or i in dipakai or buckets:
                continue
            # confident sedikit diturunkan: tidak ada konfirmasi bucket
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
        """Penahanan sementara untuk ekskavator.

        Truck punya hold dan hasilnya konsisten 100%. Ekskavator tidak punya,
        padahal形状 badannya besar dan stabil - hanya bucket yang kecil dan
        sering meleset. Tanpa hold, satu frame gagal langsung menghapus mesin
        yang jelas ada di layar (terukur: 63 flicker dalam 2035 frame).

        Confidence diturunkan bertahap selama masa tahan, jadi kotak yang
        ditahan tidak pernah diklaim sama dengan deteksi segar.
        """
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
        )]

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
        if self._prev_gray is None:
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