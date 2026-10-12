"""Tulis ROI meja hasil pengamatan snapshot, dengan backup.

ROI dihitung dari posisi orang & meja yang terlihat di frame, bukan tebakan
seperti sebelumnya. Tetap perlu dicek visual setelah ditulis.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

CONFIG = Path("config.cctv.yaml")

# (x1, y1, x2, y2) dalam koordinat relatif 0..1
ROIS = {
    "cctv-1": [
        # Meja 1: meja bulat putih + stool di kiri-tengah
        {"id": 1, "label": "Meja 1", "roi": [0.28, 0.38, 0.44, 0.80]},
        # Meja 2: bangku abu-abu memanjang di kanan meja bulat
        {"id": 2, "label": "Meja 2", "roi": [0.40, 0.28, 0.58, 0.82]},
    ],
    "cctv-2": [
        # Meja 1: konter kayu panjang di sisi kanan lorong
        {"id": 1, "label": "Meja 1", "roi": [0.54, 0.35, 0.88, 1.00]},
    ],
    "cctv-3": [],  # tangga / lorong tanpa meja kerja
    "cctv-4": [
        # Meja 1: kursi/beanbag di kiri bawah
        {"id": 1, "label": "Meja 1", "roi": [0.04, 0.60, 0.27, 1.00]},
        # Meja 2: meja kayu panjang di tengah
        {"id": 2, "label": "Meja 2", "roi": [0.27, 0.45, 0.55, 1.00]},
    ],
}


def main() -> int:
    raw = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    backup = CONFIG.with_suffix(".yaml.bak")

    print("sebelum:")
    for cam in raw.get("cameras", []):
        desks = cam.get("desks") or []
        detail = ", ".join(f"{d['label']}={d['roi']}" for d in desks) or "(tidak ada)"
        print(f"  {cam['id']:8s} {detail}")

    shutil.copy(CONFIG, backup)
    print(f"\nbackup: {backup}")

    for cam in raw.get("cameras", []):
        key = cam["id"]
        if key in ROIS:
            cam["desks"] = ROIS[key]
        for desk in cam.get("desks") or []:
            x1, y1, x2, y2 = desk["roi"]
            if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
                raise SystemExit(f"ROI tidak valid di {key}: {desk['roi']}")

    CONFIG.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    print("\nsesudah:")
    for cam in raw.get("cameras", []):
        for desk in cam.get("desks") or []:
            x1, y1, x2, y2 = desk["roi"]
            print(
                f"  {cam['id']:8s} {desk['label']:7s} "
                f"x {x1:.2f}-{x2:.2f}  y {y1:.2f}-{y2:.2f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())