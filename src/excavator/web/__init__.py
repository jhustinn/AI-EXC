"""Paket web (FastAPI) untuk mesin ekskavator."""
from __future__ import annotations

from .routes import router, set_engine

__all__ = ["router", "set_engine"]