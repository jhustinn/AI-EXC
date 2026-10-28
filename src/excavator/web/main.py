"""Aplikasi FastAPI. Menyatu API data dan stream MJPEG multi-kamera dalam satu port."""
from __future__ import annotations

import json
import os
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ..config import load_config
from ..multi_engine import MultiCameraManager
from .routes import router, set_engine, set_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config(os.environ.get("EXCAVATOR_CONFIG"))

    # Coba sinkronisasi profil aktif dari Laravel jika master data tersedia
    try:
        url = f"http://127.0.0.1:8002/api/telemetry/profile/{cfg.unit}"
        req = urllib.request.Request(url, headers={"User-Agent": "AI-CCTV-Engine/1.0"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                if "profile" in data:
                    cfg.apply_profile(data["profile"])
    except Exception:
        pass

    manager = MultiCameraManager(cfg)
    set_engine(manager.primary_engine)
    set_manager(manager)
    manager.start()
    app.state.multi_engine = manager
    app.state.engine = manager.primary_engine
    try:
        yield
    finally:
        manager.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Excavator Activity Multi-Camera Engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Dashboard Laravel dilayani port berbeda (8002), jadi browser membuat
    # permintaan lintas origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8002",
            "http://127.0.0.1:8002",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/stream")
    def stream_primary() -> StreamingResponse:
        """Stream MJPEG untuk kamera utama (CAM-01 / backward compatibility)."""
        engine = getattr(app.state, "engine", None)
        if engine is None:
            raise HTTPException(status_code=503, detail="engine belum jalan")
        return StreamingResponse(
            engine.stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
        )

    @app.get("/stream/{camera_id}")
    def stream_camera(camera_id: int) -> StreamingResponse:
        """Stream MJPEG real-time per kamera dengan visual AI & HUD overlays."""
        manager: MultiCameraManager | None = getattr(app.state, "multi_engine", None)
        if manager is None:
            engine = getattr(app.state, "engine", None)
        else:
            engine = manager.get_engine(camera_id)
        if engine is None:
            raise HTTPException(status_code=404, detail=f"Kamera {camera_id} tidak ditemukan")
        return StreamingResponse(
            engine.stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
        )

    return app


app = create_app()
