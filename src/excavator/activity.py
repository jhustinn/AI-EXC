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

    # ---------- internal ----------

    def _truck_diam(self, truck: Truck) -> bool:
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
        gali_aktif = (bucket_ada and di_zona_gali and bucket_rendah) or (
            motion >= self.zones.motion_threshold and not bucket_ada
        )
        self.status.sumber_sinyal = "bucket" if bucket_ada else (
            "truck" if truck else "zona_gali"
        )

        if truck:
            diam = self._truck_diam(truck)
            if diam:
                if self._mulai_diam is None:
                    self._mulai_diam = sekarang
            else:
                self._mulai_diam = None
        else:
            self._mulai_diam = None
            self._posisi_akhir = None

        diam_cukup = (
            truck is not None
            and self._mulai_diam is not None
            and (sekarang - self._mulai_diam).total_seconds() >= self.cfg.dump_min_seconds
        )
        gali_aktif = motion >= self.zones.motion_threshold

        # -------- tentukan kandidat fase --------
        # Urutan penting. Excavator tetap bisa mengguk walau truck sudah
        # terparkir di tempat, jadi gerak di zona gali didahulukan. Menuangkan
        # baru/bootstrap kalau zona gali justru tenang.
        if gali_aktif:
            kandidat = Fase.MENGKERUK
        elif diam_cukup:
            kandidat = Fase.MENUANGKAN
        elif truck:
            kandidat = (Fase.KEMBALI if self.status.fase is Fase.MENUANGKAN
                        else Fase.MENGANGKAT)
        else:
            kandidat = Fase.MEMUTAR

        ada_aktivitas = bool(truck) or gali_aktif
        if ada_aktivitas:
            self._terakhir_aktivitas = sekarang
        elif (sekarang - self._terakhir_aktivitas).total_seconds() >= self.cfg.idle_seconds:
            kandidat = Fase.IDLE

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