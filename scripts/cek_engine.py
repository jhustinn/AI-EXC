"""Cek import + jalankan engine sebentar, laporkan hasil nyata."""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

from excavator.config import load_config          # noqa: E402
from excavator.engine import Engine               # noqa: E402

print("import modul: OK")

cfg = load_config(PROJECT / "config.excavator.yaml")
print(f"unit      : {cfg.unit}")
print(f"sumber    : {cfg.source.kind} -> {cfg.source.path}")
print(f"kelas COCO: {cfg.detector.classes}")
print(f"zona gali : {cfg.zones.dig}")
print(f"port      : {cfg.server.port}")

engine = Engine(cfg)
print(f"kelas dideteksi model: {engine.detector.class_names}")

engine.start()
print("\nmenunggu 25 detik...\n")

seen_fases = {}
truck_frames = 0
total = 0
for i in range(50):
    time.sleep(0.5)
    total += 1
    info = engine.frame_terbaru()
    if info is None:
        continue
    if info.trucks:
        truck_frames += 1
    snap = engine.machine.snapshot()
    seen_fases[snap["fase"]] = seen_fases.get(snap["fase"], 0) + 1
    if i % 10 == 0:
        jpeg = len(info.jpeg)
        conf = info.trucks[0].conf if info.trucks else 0.0
        print(f"  frame#{engine.rid:4d} jpeg={jpeg:6d}B truck={len(info.trucks)} "
              f"conf={conf:.2f} fase={snap['fase']:10s} motion={snap['zona_gali_motion']:.4f}")

engine.stop()

print("\n" + "=" * 60)
print(f"error engine : {engine.error}")
print(f"frame diproses: {engine.rid}")
print(f"polls        : {total}, frame dengan truck: {truck_frames}")
print(f"fase terlihat: {seen_fases}")
print("KPI          :", engine.machine.snapshot()["kpi"])
print("=" * 60)