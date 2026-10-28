"""State machine aktivitas alat berat.

CATATAN JUJUR:
  Ukuran bucket belum dideteksi, jadi fase tidak bisa diamati langsung.
  Fase di sini disimpulkan dari dua sinyal yang memang terukur:

    - dump truck terdeteksi (COCO, confidence nyata)
    - energi gerak pada zona gali

  "Menuangkan" berarti truck diam di tempat selama beberapa waktu. Itu
  korelasi, bukan bukti bucket benar-benar meng emptying truck. Angka
  confidence yang ditampilkan adalah confidence deteksi truck, bukan
  kepastian aktivitas.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .config import ActivityConfig, ZoneConfig
from .objek import Objek


class Fase(str, Enum):
    IDLE = "idle"
    MENGANGKAT = "mengangkat"
    MENGKERUK = "mengeruk"
    MEMUTAR = "memutar"
    MENUANGKAN = "menuangkan"
    KEMBALI = "kembali"


FASE_LABEL = {
    Fase.IDLE: "Idle",
    Fase.MENGANGKAT: "Mengangkat",
    Fase.MENGKERUK: "Mengeruk",
    Fase.MEMUTAR: "Memutar",
    Fase.MENUANGKAN: "Menuangkan",
    Fase.KEMBALI: "Kembali",
}


@dataclass
class EventAktivitas:
    mulai: datetime
    selesai: datetime | None = None
    fase: Fase = Fase.IDLE
    truck_conf: float = 0.0
    motion: float = 0.0
    bucket_conf: float = 0.0
    excavator_conf: float = 0.0
    siklus: int = 0

    @property
    def durasi(self) -> float:
        akhir = self.selesai or datetime.now(timezone.utc)
        return max(0.0, (akhir - self.mulai).total_seconds())


@dataclass
class Statistik:
    durasi_mengeruk: float = 0.0
    durasi_menuangkan: float = 0.0
    jumlah_siklus: int = 0
    waktu_idle: float = 0.0
    siklus_terakhir: datetime | None = None


@dataclass
class Status:
    fase: Fase = Fase.IDLE
    sejak: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    truck_conf: float = 0.0
    motion: float = 0.0
    zona_tuang: tuple[float, float, float, float] | None = None
    zona_gali: tuple[float, float, float, float] | None = None
    sumber_sinyal: str = "truck"
    # sinyal dari model kustom
    bucket_conf: float = 0.0
    bucket_di_zona_gali: bool = False
    bucket_posisi: float | None = None   # 0 = atas frame, 1 = bawah
    ekskavator_conf: float = 0.0
    plate_conf: float = 0.0

    @property
    def durasi_fase(self) -> float:
        return (datetime.now(timezone.utc) - self.sejak).total_seconds()


class ActivityMachine:
    """Mengubah (truck terdeteksi, energi gerak) menjadi fase dan KPI."""

    # Grace period: truck boleh hilang sebanyak ini detik tanpa mereset
    # timer "diam". Confidence truck berayun liar (0.15-0.94 antar frame
    # bersebelahan), jadi satu-dua frame tanpa deteksi seharusnya tidak
    # menghapus fakta bahwa truck memang sedang parkir di situ.
    _TRUCK_GRACE_SECONDS = 3.0

    def __init__(self, cfg: ActivityConfig, zones: ZoneConfig):
        self.cfg = cfg
        self.zones = zones
        self.status = Status()
        self.statistik = Statistik()
        self.riwayat: deque[EventAktivitas] = deque(maxlen=400)
        self.aktif: EventAktivitas | None = None

        self._mulai_diam: datetime | None = None
        self._posisi_akhir: tuple[float, float] | None = None
        self._terakhir_aktivitas: datetime = datetime.now(timezone.utc)
        self._kandidat: Fase | None = None
        self._kandidat_mulai: datetime = datetime.now(timezone.utc)
        self._siklus_ke = 0
        # Waktu terakhir truck benar-benar terdeteksi, untuk grace period.
        self._truck_terakhir_terlihat: datetime | None = None
        # Simpan posisi truck terakhir supaya bisa menghitung diam walau
        # truck sempat hilang sebentar (confidence anjlok 1-2 frame).
        self._truck_terakhir_box: tuple[float, float, float, float] | None = None

    # ---------- internal ----------

    def _truck_diam(self, truck: Objek) -> bool:
        """Dua pembacaan berturut dengan posisi mirip berarti truck diam."""
        if self._posisi_akhir is None:
            self._posisi_akhir = (truck.cx, truck.cy)
            return False
        dx = abs(truck.cx - self._posisi_akhir[0])
        dy = abs(truck.cy - self._posisi_akhir[1])
        self._posisi_akhir = (truck.cx, truck.cy)
        lebar = max(1.0, truck.w)
        return (dx / lebar) < 0.06 and (dy / lebar) < 0.06

    def _stabil(self, kandidat: Fase, sekarang: datetime) -> Fase:
        """Debounce: kandidat fase harus bertahan awhile sebelum diterima.

        Tanpa ini fase bergetar tiap frame dan jumlah siklus jadi tidak
        masuk akal karena sinyal gerak zona gali bising.
        """
        if kandidat == self.status.fase:
            self._kandidat = None
            return self.status.fase
        if kandidat != self._kandidat:
            self._kandidat = kandidat
            self._kandidat_mulai = sekarang
            return self.status.fase
        cukup = (sekarang - self._kandidat_mulai).total_seconds() >= self.cfg.phase_min_seconds
        return kandidat if cukup else self.status.fase

    def _ganti_fase(self, fase: Fase, sekarang: datetime,
                    conf: float, motion: float, hasil=None) -> None:
        if fase == self.status.fase:
            return
        if self.aktif:
            self.aktif.selesai = sekarang
            self.aktif.truck_conf = conf
            self.aktif.motion = motion
            if hasil is not None:
                self.aktif.bucket_conf = (hasil.buckets[0].conf
                                           if hasil.buckets else 0.0)
                self.aktif.excavator_conf = (hasil.ekskavator[0].conf
                                             if hasil.ekskavator else 0.0)
            self._akumulasikan(self.aktif)
            self.riwayat.append(self.aktif)
            # Satu siklus = satu fase Menuangkan yang selesai dan bertahan
            # cukup lama. Truck TIDAK perlu hilang di antaranya, karena truck
            # di lapangan tetap diparkir selama satu siklus dimuat.
            if (self.aktif.fase is Fase.MENUANGKAN
                    and self.aktif.durasi >= self.cfg.dump_min_seconds):
                self.statistik.jumlah_siklus += 1
                self.statistik.siklus_terakhir = self.aktif.mulai
        self._siklus_ke += 1
        self.aktif = EventAktivitas(
            mulai=sekarang, fase=fase, siklus=self._siklus_ke
        )
        self.status.fase = fase
        self.status.sejak = sekarang

    def _akumulasikan(self, ev: EventAktivitas) -> None:
        durasi = ev.durasi
        if ev.fase is Fase.MENGKERUK:
            self.statistik.durasi_mengeruk += durasi
        elif ev.fase is Fase.MENUANGKAN:
            self.statistik.durasi_menuangkan += durasi
        elif ev.fase is Fase.IDLE:
            self.statistik.waktu_idle += durasi

    # ---------- API utama ----------

    def update(self, hasil, cfg) -> Status:
        """Terima FrameResult lengkap.

        Sinyal utama Mengeruk sekarang ADALAH bucket: bucket yang berada
        di zona gali dan tinggi rendah berarti excavator sedang mengguk.
        Dulu fase ini hanya ditebak dari energi gerak, yang tidak bisa
        membedakan mengguk dari gerak kamera.
        """
        sekarang = datetime.now(timezone.utc)
        trucks = hasil.trucks
        truck = trucks[0] if trucks else None
        conf = truck.conf if truck else 0.0
        motion = hasil.dig_motion
        h, w = hasil.frame_shape

        # ---- posisi bucket ----
        bucket = hasil.buckets[0] if hasil.buckets else None
        di_zona_gali = False
        bucket_rendah = False
        rasio_tinggi = 0.0
        if bucket is not None and h:
            zx1, zy1, zx2, zy2 = self.zones.dig
            cxm, cym = bucket.cx / w, bucket.cy / h
            di_zona_gali = zx1 <= cxm <= zx2 and zy1 <= cym <= zy2
            # posisi vertikal bucket dalam frame, 0 = atas, 1 = bawah
            rasio_tinggi = bucket.cy / h
            bucket_rendah = rasio_tinggi >= self.cfg.bucket_low_ratio
            self.status.bucket_di_zona_gali = di_zona_gali

        bucket_ada = bucket is not None
        self.status.sumber_sinyal = "bucket" if bucket_ada else (
            "truck" if truck else "zona_gali"
        )

        # Cek apakah excavator dalam Mode Boom POV / video portrait dashcam
        is_boom_pov = (bucket is not None and bucket.y1 > h * 0.60 and bucket.w > w * 0.50) or (w < h)

        # ----------------------------------------------------------
        # Logika truck diam DENGAN GRACE PERIOD
        # ----------------------------------------------------------
        # Pada Dashcam POV kamera ikut berputar bersama kabin/house, jadi truck hilang segera saat swing.
        grace_seconds = 0.6 if is_boom_pov else self._TRUCK_GRACE_SECONDS
        truck_hadir = truck is not None  # terdeteksi frame ini

        if truck_hadir:
            self._truck_terakhir_terlihat = sekarang
            self._truck_terakhir_box = truck.bbox
            diam = self._truck_diam(truck)
            if diam:
                if self._mulai_diam is None:
                    self._mulai_diam = sekarang
            else:
                self._mulai_diam = None
        else:
            # Truck hilang frame ini — cek apakah masih dalam grace period
            if self._truck_terakhir_terlihat is not None:
                hilang_detik = (sekarang - self._truck_terakhir_terlihat).total_seconds()
                if hilang_detik > grace_seconds:
                    # Benar-benar hilang — reset semua
                    self._mulai_diam = None
                    self._posisi_akhir = None
                    self._truck_terakhir_terlihat = None
                    self._truck_terakhir_box = None
            else:
                self._mulai_diam = None
                self._posisi_akhir = None

        # "truck_aktif" = truck terdeteksi sekarang ATAU masih dalam grace period
        truck_aktif = truck_hadir or (
            self._truck_terakhir_terlihat is not None
            and (sekarang - self._truck_terakhir_terlihat).total_seconds() <= grace_seconds
        )

        diam_cukup = (
            truck_aktif
            and self._mulai_diam is not None
            and (sekarang - self._mulai_diam).total_seconds() >= self.cfg.dump_min_seconds
        )

        # -------------------------------------------------------------
        # Deteksi Fase Berbasis Kinematika & Geometri Nyata (Mengeruk & Menuangkan)
        # -------------------------------------------------------------
        eks = hasil.ekskavator[0] if hasil.ekskavator else None

        target_b_cx = bucket.cx if bucket is not None else (eks.wrist[0] if (eks and eks.wrist) else None)
        target_b_cy = bucket.cy if bucket is not None else (eks.wrist[1] if (eks and eks.wrist) else None)

        is_dumping = False
        is_digging = False

        # Cek apakah excavator dalam Mode Boom POV (kamera kabin menatap langsung pit galian / portrait dashcam)
        is_boom_pov = (bucket is not None and bucket.y1 > h * 0.60 and bucket.w > w * 0.50) or (w < h)

        # 1. Evaluasi MENUANGKAN (Dumping ke bak dump truck aktif)
        has_left_truck = False
        has_right_truck = False

        if is_boom_pov:
            # Pada Dashcam Cabin / Boom POV:
            # Bila dump truck hadir di depan kabin / boom -> fase dumping (MENUANGKAN)
            if truck_aktif or (truck is not None):
                is_dumping = True
            else:
                # Bila dump truck tidak ada (menghadap ke area pit galian gelap)
                is_digging = True
        elif target_b_cx is not None and target_b_cy is not None:
            trucks_ref = list(trucks) if trucks else []
            if not trucks_ref and truck_aktif and self._truck_terakhir_box is not None:
                bx = self._truck_terakhir_box
                trucks_ref = [Objek("truck", bx[0], bx[1], bx[2], bx[3], 0.0)]

            # Klasifikasikan truk kerja aktif (diabaikan jika truk kecil di kejauhan)
            truk_kerja = [t for t in trucks_ref if t.w >= 0.11 * w]
            has_left_truck = any(t.cx < 0.50 * w for t in truk_kerja)
            has_right_truck = any(t.cx >= 0.50 * w for t in truk_kerja)

            # A. Cek apakah bucket berada di atas bak dump truck kerja yang terdeteksi
            for t in truk_kerja:
                margin_x = max(60.0, t.w * 0.25)
                # Bucket harus berada di koridor bak truk dan tidak di bawah roda
                if (t.x1 - margin_x <= target_b_cx <= t.x2 + margin_x) and (target_b_cy <= t.y2 + 40.0):
                    is_dumping = True
                    break

            # B. Fallback zona tuang HANYA jika memang ada truk kerja di sisi tersebut
            if not is_dumping:
                if has_left_truck and (0.16 * w <= target_b_cx <= 0.48 * w) and (0.15 * h <= target_b_cy <= 0.65 * h):
                    is_dumping = True
                elif has_right_truck and (target_b_cx >= 0.70 * w) and (0.25 * h <= target_b_cy <= 0.85 * h):
                    is_dumping = True

        # 2. Evaluasi MENGERUK (Digging di pit galian / tebing / tumpukan material)
        if not is_dumping:
            if is_boom_pov:
                is_digging = True
            elif target_b_cx is not None and target_b_cy is not None:
                # Pengerukan: bucket berada di dasar/tanah (y >= 0.50*h) ATAU di dinding tebing kiri
                if target_b_cy >= 0.50 * h:
                    if has_right_truck and not has_left_truck:
                        # Jika truk di kanan, semua aktivitas di kiri & tengah (x < 0.68*w) adalah pengerukan
                        if target_b_cx < 0.68 * w:
                            is_digging = True
                    elif has_left_truck:
                        # Jika truk di kiri, pengerukan di tebing kiri (x < 0.16*w) atau dasar pit dalam
                        if target_b_cx < 0.16 * w or target_b_cy >= 0.70 * h or target_b_cx >= 0.55 * w:
                            is_digging = True
                    else:
                        is_digging = True
                elif target_b_cx < 0.16 * w:
                    # Dinding tebing galian kiri atas
                    is_digging = True
                elif motion >= self.zones.motion_threshold:
                    is_digging = True

        # 3. Klasifikasi Urutan Fase Siklus
        if is_dumping:
            kandidat = Fase.MENUANGKAN
            self._terakhir_aktivitas = sekarang
        elif is_digging:
            kandidat = Fase.MENGKERUK
            self._terakhir_aktivitas = sekarang
        elif target_b_cx is not None and target_b_cy is not None:
            if self.status.fase is Fase.MENUANGKAN:
                kandidat = Fase.KEMBALI
            elif self.status.fase is Fase.KEMBALI:
                if target_b_cx < 0.50 * w:
                    kandidat = Fase.MENGKERUK if (target_b_cy >= 0.38 * h or motion >= self.zones.motion_threshold) else Fase.KEMBALI
                else:
                    kandidat = Fase.KEMBALI
            elif self.status.fase in (Fase.MENGKERUK, Fase.MENGANGKAT):
                if target_b_cy < 0.38 * h and target_b_cx < 0.52 * w:
                    kandidat = Fase.MENGANGKAT
                else:
                    kandidat = Fase.MEMUTAR
            else:
                kandidat = Fase.MEMUTAR
            self._terakhir_aktivitas = sekarang
        else:
            if (sekarang - self._terakhir_aktivitas).total_seconds() >= self.cfg.idle_seconds:
                kandidat = Fase.IDLE
            else:
                kandidat = Fase.MEMUTAR

        self._ganti_fase(self._stabil(kandidat, sekarang), sekarang, conf, motion, hasil)

        # -------- publish status --------
        self.status.truck_conf = conf
        self.status.motion = motion
        self.status.bucket_conf = bucket.conf if bucket else 0.0
        self.status.ekskavator_conf = (hasil.ekskavator[0].conf
                                       if hasil.ekskavator else 0.0)
        self.status.bucket_posisi = rasio_tinggi if bucket else None
        self.status.plate_conf = (hasil.plates[0].conf if hasil.plates else 0.0)

        x1, y1, x2, y2 = self.zones.dig
        self.status.zona_gali = (x1 * w, y1 * h, x2 * w, y2 * h)
        self.status.zona_tuang = truck.dump_zone(self.zones) if truck else None
        return self.status

    def riwayat_dict(self, limit: int = 50) -> list[dict]:
        hasil = []
        for ev in reversed(self.riwayat):
            hasil.append({
                "mulai": ev.mulai.isoformat(),
                "selesai": ev.selesai.isoformat() if ev.selesai else None,
                "durasi": round(ev.durasi, 1),
                "fase": ev.fase.value,
                "fase_label": FASE_LABEL[ev.fase],
                "truck_confidence": round(ev.truck_conf, 3),
                "bucket_confidence": round(ev.bucket_conf, 3),
                "excavator_confidence": round(ev.excavator_conf, 3),
                "zona_gali_motion": round(ev.motion, 4),
                "siklus": ev.siklus,
            })
        return hasil[:limit]

    def snapshot(self) -> dict:
        s = self.status
        # Fase yang sedang berjalan ikut dihitung, kalau tidak dashboard
        # akan menampilkan 0 sementara statusnya sudah "Menuangkan 29 detik".
        berjalan_mengeruk = 0.0
        berjalan_menuang = 0.0
        berjalan_idle = 0.0
        if self.aktif:
            d = self.aktif.durasi
            if self.aktif.fase is Fase.MENGKERUK:
                berjalan_mengeruk = d
            elif self.aktif.fase is Fase.MENUANGKAN:
                berjalan_menuang = d
            elif self.aktif.fase is Fase.IDLE:
                berjalan_idle = d

        return {
            "fase": s.fase.value,
            "fase_label": FASE_LABEL[s.fase],
            "durasi_fase_detik": round(s.durasi_fase, 1),
            "truck_confidence": round(s.truck_conf, 3),
            "zona_gali_motion": round(s.motion, 4),
            "sumber_sinyal": s.sumber_sinyal,
            "bucket_confidence": round(s.bucket_conf, 3),
            "bucket_di_zona_gali": s.bucket_di_zona_gali,
            "bucket_posisi": round(s.bucket_posisi, 3) if s.bucket_posisi is not None else None,
            "excavator_confidence": round(s.ekskavator_conf, 3),
            "plate_confidence": round(s.plate_conf, 3),
            "zona_tuang": list(s.zona_tuang) if s.zona_tuang else None,
            "zona_gali": list(s.zona_gali) if s.zona_gali else None,
            "kpi": {
                "durasi_mengeruk": round(self.statistik.durasi_mengeruk + berjalan_mengeruk, 1),
                "durasi_menuangkan": round(self.statistik.durasi_menuangkan + berjalan_menuang, 1),
                "jumlah_siklus": self.statistik.jumlah_siklus,
                "waktu_idle": round(self.statistik.waktu_idle + berjalan_idle, 1),
            },
        }