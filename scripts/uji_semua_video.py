"""Jalankan engine pada tiap video referensi, laporkan hasil nyata."""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402

from excavator.activity import Fase  # noqa: E402
from excavator.config import load_config  # noqa: E402
from excavator.engine import Engine  # noqa: E402

VIDEO_DIR = PROJECT / "INGIN SEPERTI INI"
CFG = PROJECT / "config.excavator.yaml"


def jalankan(path: Path, durasi_maks: float = 45.0) -> dict:
    cfg = load_config(CFG)
    cfg.source.path = str(path.relative_to(PROJECT))
    cfg.source.loop = False

    engine = Engine(cfg)
    engine.start()

    awal = time.time()
    fase_ditemukan: dict[str, float] = {}
    frame_ada_truck = 0
    frame_total = 0
    conf_total = 0.0
    conf_tertinggi = 0.0
    motion_total = 0.0
    fase_terakhir = Fase.IDLE
    idx_terakhir = 0

    while time.time() - awal < durasi_maks:
        time.sleep(0.25)
        info = engine.frame_terbaru()
        if info is None or info.stamp is None:
            continue
        if engine.rid == idx_terakhir:
            continue
        idx_terakhir = engine.rid

        frame_total += 1
        if info.trucks:
            frame_ada_truck += 1
            c = info.trucks[0].conf
            conf_total += c
            conf_tertinggi = max(conf_tertinggi, c)

        snap = engine.machine.snapshot()
        f = snap["fase"]
        fase_ditemukan[f] = fase_ditemukan.get(f, 0.0) + 0.25
        motion_total += snap["zona_gali_motion"]
        fase_terakhir = Fase(f)

        # berhenti kalau video habis (loop=False)
        if engine.error and "berhenti" in str(engine.error):
            break

    stat = engine.machine.statistik
    hasil = {
        "file": path.name,
        "frame": engine.rid,
        "truck_frame": frame_ada_truck,
        "truck_persen": frame_ada_truck / max(1, frame_total) * 100,
        "conf_rata": conf_total / max(1, frame_ada_truck),
        "conf_max": conf_tertinggi,
        "motion_rata": motion_total / max(1, frame_total),
        "fase": fase_ditemukan,
        "siklus": stat.jumlah_siklus,
        "mengeruk": stat.durasi_mengeruk,
        "menuangkan": stat.durasi_menuangkan,
        "idle": stat.waktu_idle,
        "error": engine.error,
        "fase_akhir": fase_terakhir.value,
    }
    engine.stop()
    return hasil


video = sorted(VIDEO_DIR.glob("*.mp4"))
print(f"menguji {len(video)} video, maksimal 45 detik tiap video\n")

ringkas = []
for p in video:
    r = jalankan(p)
    ringkas.append(r)
    print("=" * 74)
    print(r["file"])
    print(f"  frame diproses   : {r['frame']}")
    print(f"  frame ada truck  : {r['truck_frame']}  ({r['truck_persen']:.0f}%)")
    print(f"  confidence truck : rata {r['conf_rata']:.3f}  maks {r['conf_max']:.3f}")
    print(f"  gerak zona gali  : rata {r['motion_rata']:.4f}")
    print(f"  fase terlihat    : {r['fase']}")
    print(f"  KPI              : siklus={r['siklus']}  mengeruk={r['mengeruk']:.1f}s "
          f"menuangkan={r['menuangkan']:.1f}s idle={r['idle']:.1f}s")
    print(f"  fase terakhir    : {r['fase_akhir']}")
    if r["error"]:
        print(f"  error            : {r['error']}")

print("\n" + "=" * 74)
print("RINGKASAN")
print("=" * 74)
print(f"{'video':<34}{'truck%':>8}{'conf':>8}{'siklus':>8}{'menuang':>10}")
for r in ringkas:
    print(f"{r['file'][-30:]:<34}{r['truck_persen']:>7.0f}%"
          f"{r['conf_rata']:>8.2f}{r['siklus']:>8d}{r['menuangkan']:>9.1f}s")