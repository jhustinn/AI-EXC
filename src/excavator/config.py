"""Konfigurasi mesin deteksi aktivitas alat berat."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SourceConfig:
    """Sumber frame: file video (uji) atau kamera RTSP (produksi)."""
    kind: str = "video"                 # video | rtsp
    path: str = ""                      # untuk kind=video
    url: str = ""                       # untuk kind=rtsp
    loop: bool = True                   # ulang video dari awal
    width: int = 1280
    height: int = 720
    fps: int = 30
    ffmpeg: bool = True                 # pakai FFmpeg backend (dikamera RTMP)


@dataclass
class DetectorConfig:
    model: str = "yolov8n.pt"
    confidence: float = 0.35
    # Ambang pelepasan. Ambul confidence turun masih diterima selama kotak
    # ditahan, supaya truck tidak berkedip hilang-hilang di frame bersebelahan.
    release_confidence: float = 0.20
    iou: float = 0.5
    device: str = "0"
    imgsz: int = 640
    # Lama kotak ditahan setelah deteksi hilang. Confidence truck di video
    # berayun 0,15-0,94 antar frame, jadi tanpa ini dashboard berkedip.
    hold_seconds: float = 1.5
    # Kalau kotak ditahan lebih dari ini, tandai sebagai ekstrapolasi.
    hold_mark_seconds: float = 0.8
    # kelas COCO yang dianggap sebagai dump truck
    classes: list[str] = field(default_factory=lambda: ["truck"])
    min_width_ratio: float = 0.15       # abaikan truck kecil di kejauhan
    max_width_ratio: float = 1.0


@dataclass
class ZoneConfig:
    """Zona gali (tetap) dan zona tuang (dinamis dari truck)."""
    # normalized [x1, y1, x2, y2] terhadap ukuran frame
    dig: list[float] = field(default_factory=lambda: [0.10, 0.45, 0.90, 0.98])
    # bagian atas bak truck yang menjadi zona tuang
    dump_top_ratio: float = 0.15        # 15% teratas bbox truck = pintu bak
    dump_height_ratio: float = 0.60
    motion_threshold: float = 0.012     # energi gerak di zona gali


@dataclass
class ActivityConfig:
    """Aturan state machine aktivitas."""
    phase_min_seconds: float = 2.0      # kandidat fase harus bertahan ini dulu
    dump_min_seconds: float = 2.5       # truck diam minimal ini -> dianggap menuang
    dig_min_seconds: float = 3.0        # gerak di zona gali minimal ini -> mengguk
    idle_seconds: float = 5.0           # tanpa aktivitas selama ini -> idle


@dataclass
class StoreConfig:
    dsn: str = ""                       # PostgreSQL, opsional
    table_events: str = "activity_events"
    table_cycles: str = "activity_cycles"


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8010
    stream_fps: int = 12
    stream_quality: int = 72
    stream_width: int = 720


@dataclass
class Config:
    source: SourceConfig = field(default_factory=SourceConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    zones: ZoneConfig = field(default_factory=ZoneConfig)
    activity: ActivityConfig = field(default_factory=ActivityConfig)
    store: StoreConfig = field(default_factory=StoreConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    timezone: str = "Asia/Jakarta"
    unit: str = "EXC-07"
    project_root: Path = field(default_factory=lambda: Path.cwd())

    def resolve(self, value: str) -> Path:
        p = Path(value)
        return p if p.is_absolute() else self.project_root / p


def _build(cls, data: dict[str, Any] | None):
    if not data:
        return cls()
    known = {f for f in cls.__dataclass_fields__}
    return cls(**{k: v for k, v in data.items() if k in known})


def load_config(path: str | os.PathLike | None = None) -> Config:
    """Baca YAML; setiap bagian opsional jadi default."""
    raw: dict[str, Any] = {}
    cfg_file = None
    if path:
        cfg_file = Path(path)
    else:
        env = os.environ.get("EXCAVATOR_CONFIG")
        if env:
            cfg_file = Path(env)
        else:
            for cand in (Path.cwd() / "config.excavator.yaml",
                         Path(__file__).resolve().parents[2] / "config.excavator.yaml"):
                if cand.is_file():
                    cfg_file = cand
                    break
    if cfg_file and cfg_file.is_file():
        raw = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}

    cfg = Config(
        source=_build(SourceConfig, raw.get("source")),
        detector=_build(DetectorConfig, raw.get("detector")),
        zones=_build(ZoneConfig, raw.get("zones")),
        activity=_build(ActivityConfig, raw.get("activity")),
        store=_build(StoreConfig, raw.get("store")),
        server=_build(ServerConfig, raw.get("server")),
        timezone=raw.get("timezone", "Asia/Jakarta"),
        unit=raw.get("unit", "EXC-07"),
    )
    cfg.project_root = (cfg_file.parent if cfg_file else Path.cwd())
    # DSN boleh datang dari environment supaya tidak ikut ter-commit
    cfg.store.dsn = os.environ.get("EXCAVATOR_DSN", cfg.store.dsn)
    return cfg