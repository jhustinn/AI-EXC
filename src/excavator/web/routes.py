"""Endpoint FastAPI untuk dashboard Laravel."""
from __future__ import annotations

import asyncio
import json
import urllib.request
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api", tags=["excavator"])

_engine = None
_manager = None


def set_manager(manager) -> None:
    global _manager
    _manager = manager


def set_engine(engine) -> None:
    global _engine
    _engine = engine


def _butuh_engine():
    if _engine is None:
        raise HTTPException(status_code=503, detail="engine belum jalan")
    return _engine


@router.get("/status/{camera_id}")
def status_camera(camera_id: int) -> dict:
    """Status realtime per kamera spesifik."""
    if _manager is not None:
        engine = _manager.get_engine(camera_id)
    else:
        engine = _butuh_engine()
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Kamera {camera_id} tidak ditemukan")

    snap = engine.machine.snapshot()
    snap["engine"] = {
        "camera_id": getattr(engine, "camera_id", camera_id),
        "camera_name": getattr(engine, "camera_name", f"CAM-{camera_id:02d}"),
        "error": engine.error,
        "frame_total": engine.rid,
        "frame_terakhir": engine.frame_terakhir.isoformat() if engine.frame_terakhir else None,
        "kelas": engine.detector.class_names,
        "unit": engine.cfg.unit,
        "sumber": engine.cfg.source.kind,
        "truck_ditahan": engine.truck_ditahan,
    }
    return snap


@router.get("/status")
def status() -> dict:
    """Status realtime + KPI. Dipanggil Laravel lewat service class."""
    engine = _butuh_engine()
    snap = engine.machine.snapshot()
    snap["engine"] = {
        "error": engine.error,
        "frame_total": engine.rid,
        "frame_terakhir": engine.frame_terakhir.isoformat() if engine.frame_terakhir else None,
        "kelas": engine.detector.class_names,
        "unit": engine.cfg.unit,
        "sumber": engine.cfg.source.kind,
        # True berarti kotak truck bukan hasil deteksi frame ini, tapi kotak
        # yang ditahan karena confidence sempat anjlok. Harus disebut terbuka
        # supaya tidak dianggap bukti deteksi baru.
        "truck_ditahan": engine.truck_ditahan,
    }
    snap["catatan"] = (
        "Fase disimpulkan dari deteksi dump truck (COCO) dan energi gerak "
        "zona gali. Ukuran bucket belum dideteksi, jadi fase Menuangkan "
        "berarti truck diam - korelasi, bukan bukti bucket meng emptying."
    )
    return snap


@router.get("/riwayat")
def riwayat(limit: int = 50) -> dict:
    engine = _butuh_engine()
    return {"events": engine.machine.riwayat_dict(limit=max(1, min(limit, 200)))}


@router.get("/kpi")
def kpi() -> dict:
    engine = _butuh_engine()
    st = engine.machine.statistik
    return {
        "durasi_mengeruk_detik": round(st.durasi_mengeruk, 1),
        "durasi_menuangkan_detik": round(st.durasi_menuangkan, 1),
        "jumlah_siklus": st.jumlah_siklus,
        "waktu_idle_detik": round(st.waktu_idle, 1),
    }


@router.get("/profile/current")
def get_current_profile() -> dict:
    """Mengambil konfigurasi pola deteksi, trigger, dan zona ROI yang sedang aktif di Engine."""
    engine = _butuh_engine()
    return {
        "unit": engine.cfg.unit,
        "detector": {
            "confidence": engine.cfg.detector.confidence,
            "release_confidence": engine.cfg.detector.release_confidence,
            "truck_confidence": getattr(engine.cfg.detector, "truck_confidence", 0.35),
            "hold_seconds": engine.cfg.detector.hold_seconds,
            "min_width_ratio": engine.cfg.detector.min_width_ratio,
            "arm_confidence": getattr(engine.cfg.detector, "arm_confidence", 0.35),
            "arm_swing_threshold": getattr(engine.cfg.detector, "arm_swing_threshold", 0.05),
            "plate_confidence": engine.cfg.detector.plate_confidence,
        },
        "zones": {
            "dig": engine.cfg.zones.dig,
            "dump_top_ratio": engine.cfg.zones.dump_top_ratio,
            "dump_height_ratio": engine.cfg.zones.dump_height_ratio,
            "motion_threshold": engine.cfg.zones.motion_threshold,
        },
        "activity": {
            "dig_min_seconds": engine.cfg.activity.dig_min_seconds,
            "dump_min_seconds": engine.cfg.activity.dump_min_seconds,
            "phase_min_seconds": engine.cfg.activity.phase_min_seconds,
            "idle_seconds": engine.cfg.activity.idle_seconds,
            "bucket_low_ratio": engine.cfg.activity.bucket_low_ratio,
        },
    }


@router.post("/profile/apply")
def apply_profile_payload(profile: dict) -> dict:
    """Terapkan langsung profil deteksi dari payload JSON."""
    engine = _butuh_engine()
    engine.cfg.apply_profile(profile)
    return {
        "status": "applied",
        "message": "Pola deteksi & triggers berhasil diaplikasikan ke Engine",
        "profile": profile.get("kode_profil", "custom"),
    }


@router.post("/profile/sync")
def sync_profile_from_laravel(unit: str | None = None) -> dict:
    """Sinkronisasi pola deteksi langsung dari Laravel Telemetry Profile API."""
    engine = _butuh_engine()
    target_unit = unit or engine.cfg.unit
    url = f"http://127.0.0.1:8002/api/telemetry/profile/{target_unit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-CCTV-Engine/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                raise HTTPException(status_code=502, detail=f"Gagal mengambil profil dari Laravel: HTTP {response.status}")
            data = json.loads(response.read().decode())
            profile_data = data.get("profile", {})
            engine.cfg.apply_profile(profile_data)
            return {
                "status": "synced",
                "unit": target_unit,
                "profile_applied": profile_data.get("kode_profil", "unknown"),
                "nama": profile_data.get("nama", "unknown"),
            }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Koneksi ke Laravel gagal: {exc}")


@router.get("/health")
def health() -> dict:
    engine = _engine
    if engine is None:
        return {"status": "siap", "engine": False}
    return {
        "status": "ok" if engine.error is None else "degraded",
        "engine": True,
        "error": engine.error,
        "waktu": datetime.now().isoformat(timespec="seconds"),
    }
