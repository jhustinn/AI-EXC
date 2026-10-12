"""Endpoint FastAPI untuk dashboard Laravel."""
from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api", tags=["excavator"])

_engine = None


def set_engine(engine) -> None:
    global _engine
    _engine = engine


def _butuh_engine():
    if _engine is None:
        raise HTTPException(status_code=503, detail="engine belum jalan")
    return _engine


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