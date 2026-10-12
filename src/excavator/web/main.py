"""Aplikasi FastAPI. Menyatu API data dan stream MJPEG dalam satu port."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ..config import load_config
from ..engine import Engine
from .routes import router, set_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config(os.environ.get("EXCAVATOR_CONFIG"))
    engine = Engine(cfg)
    set_engine(engine)
    engine.start()
    app.state.engine = engine
    try:
        yield
    finally:
        engine.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Excavator Activity Engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Dashboard Laravel dilayani port berbeda (8002), jadi browser membuat
    # permintaan lintas origin. Tanpa ini semua fetch ditolak CORS dan KPI
    # di dashboard tetap kosong walau engine berjalan normal.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8002",
            "http://127.0.0.1:8002",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/stream")
    def stream() -> StreamingResponse:
        engine = getattr(app.state, "engine", None)
        if engine is None:
            raise HTTPException(status_code=503, detail="engine belum jalan")
        return StreamingResponse(
            engine.stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
        )

    return app


app = create_app()