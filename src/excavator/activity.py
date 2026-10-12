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
from .detector import Truck


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

    @property
    def durasi_fase(self) -> float:
        return (datetime.now(timezone.utc) - self.since).total_seconds()


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
        self._tidak_tampak: datetime | None = None
        self._terakhir_aktivitas: datetime = datetime.now(timezone.utc)
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

    def _ganti_fase(self, fase: Fase, sekarang: datetime,
                    conf: float, motion: float) -> None:
        if fase == self.status.fase:
            return
        if self.aktif:
            self.aktif.selesai = sekarang
            self.aktif.truck_conf = conf
            self.aktif.motion = motion
            self._akumulasikan(self.aktif)
            self.riwayat.append(self.aktif)
        self._siklus_ke += 1
        self.aktif = EventAktivitas(
            mulai=sekarang, fase=fase, siklus=self._siklus_ke
        )
        self.status.fase = fase
        self.status.since = sekarang

    def _akumulasikan(self, ev: EventAktivitas) -> None:
        durasi = ev.durasi
        if ev.fase is Fase.MENGKERUK:
            self.statistik.durasi_mengeruk += durasi
        elif ev.fase is Fase.MENUANGKAN:
            self.statistik.durasi_menuangkan += durasi
        elif ev.fase is Fase.IDLE:
            self.statistik.waktu_idle += durasi

    # ---------- API utama ----------

    def update(self, trucks: list[Truck], motion: float,
               frame_shape: tuple[int, int]) -> Status:
        sekarang = datetime.now(timezone.utc)
        truck = trucks[0] if trucks else None
        conf = truck.conf if truck else 0.0

        if truck:
            diam = self._truck_diam(truck)
            self._tidak_tampak = None
            if diam:
                if self._mulai_diam is None:
                    self._mulai_diam = sekarang
            else:
                self._mulai_diam = None
        else:
            self._mulai_diam = None
            self._posisi_akhir = None
            if self._tidak_tampak is None:
                self._tidak_tampak = sekarang

        diam_cukup = (
            truck is not None
            and self._mulai_diam is not None
            and (sekarang - self._mulai_diam).total_seconds() >= self.cfg.dump_min_seconds
        )

        # -------- tentukan kandidat fase --------
        if diam_cukup:
            kandidat = Fase.MENUANGKAN
        elif truck and self.status.fase is Fase.MENUANGKAN:
            kandidat = Fase.KEMBALI
        elif truck:
            kandidat = Fase.MENGANGKAT
        elif motion >= self.zones.motion_threshold:
            kandidat = Fase.MENGKERUK
        else:
            kandidat = Fase.MEMUTAR

        ada_aktivitas = bool(truck) or motion >= self.zones.motion_threshold
        if ada_aktivitas:
            self._terakhir_aktivitas = sekarang
        elif (sekarang - self._terakhir_aktivitas).total_seconds() >= self.cfg.idle_seconds:
            kandidat = Fase.IDLE

        self._ganti_fase(kandidat, sekarang, conf, motion)

        # -------- akhir siklus saat truck pergi cukup lama --------
        if self._tidak_tampak is not None and \
                (sekarang - self._tidak_tampak).total_seconds() >= self.cfg.truck_gone_seconds:
            if self.aktif and self.aktif.fase is Fase.MENUANGKAN:
                self.statistik.jumlah_siklus += 1
                self.statistik.siklus_terakhir = self.aktif.mulai
                self.statistik.durasi_menuangkan = 0.0
            self._tidak_tampak = None

        # -------- publish status --------
        self.status.truck_conf = conf
        self.status.motion = motion
        self.status.sumber_sinyal = "truck" if truck else "zona_gali"

        h, w = frame_shape
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
                "zona_gali_motion": round(ev.motion, 4),
                "siklus": ev.siklus,
            })
        return hasil[:limit]

    def snapshot(self) -> dict:
        s = self.status
        return {
            "fase": s.fase.value,
            "fase_label": FASE_LABEL[s.fase],
            "durasi_fase_detik": round(s.durasi_fase, 1),
            "truck_confidence": round(s.truck_conf, 3),
            "zona_gali_motion": round(s.motion, 4),
            "sumber_sinyal": s.sumber_sinyal,
            "zona_tuang": list(s.zona_tuang) if s.zona_tuang else None,
            "zona_gali": list(s.zona_gali) if s.zona_gali else None,
            "kpi": {
                "durasi_mengeruk": round(self.statistik.durasi_mengeruk, 1),
                "durasi_menuangkan": round(self.statistik.durasi_menuangkan, 1),
                "jumlah_siklus": self.statistik.jumlah_siklus,
                "waktu_idle": round(self.statistik.waktu_idle, 1),
            },
        }