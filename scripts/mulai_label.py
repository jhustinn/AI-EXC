"""Buat lembar kerja bergrid untuk pelabelan manual oleh AI.

Setiap sel menampilkan satu frame dengan grid koordinat normal (0-100)
supaya kotak bisa dibaca langsung dari gambar.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import os  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

OUT = PROJECT / "datasets" / "excavator"
SHEET_DIR = PROJECT / "data" / "label_sheets"
SHEET_DIR.mkdir(parents=True, exist_ok=True)

PER_VIDEO = 10         # frame yang diambil dari tiap video
PER_SHEET = 6
COLS, ROWS = 2, 3
# batch menentukan frame mana yang diambil, supaya bisa menambah lembar
# tanpa menimpa yang sudah dilabeli
BATCH = int(os.environ.get("LABEL_BATCH", "0"))
CELL_W, CELL_H = 300, 533      # rasio 478x850 portrait


def dengan_grid(img: np.ndarray) -> np.ndarray:
    """Pasang grid koordinat 0-100 di atas gambar."""
    h, w = img.shape[:2]
    canvas = np.full((CELL_H, CELL_W + 34, 3), 20, dtype=np.uint8)
    small = cv2.resize(img, (CELL_W, CELL_H), interpolation=cv2.INTER_AREA)
    canvas[:, 34:] = small

    for u in range(0, 101, 10):
        x = int(u / 100 * CELL_W) + 34
        cv2.line(canvas, (x, 0), (x, CELL_H), (0, 0, 255) if u % 50 == 0 else (90, 90, 90), 1)
        cv2.putText(canvas, str(u), (x - 8, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                    (255, 255, 255), 1)
    for v in range(0, 101, 10):
        y = int(v / 100 * CELL_H)
        cv2.line(canvas, (34, y), (34 + CELL_W, y), (0, 0, 255) if v % 50 == 0 else (90, 90, 90), 1)
        cv2.putText(canvas, str(v), (2, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                    (255, 255, 255), 1)
    return canvas


def main() -> None:
    imgs = sorted((OUT / "images" / "train").glob("*.jpg"))
    # ambil tersebar merata dari keempat video
    per_video: dict[str, list[Path]] = {}
    for p in imgs:
        per_video.setdefault(p.stem.split("_")[0], []).append(p)

    dipilih: list[Path] = []
    for vid, lst in sorted(per_video.items()):
        # ambil potongan berbeda tiap batch supaya lembar tidak tumpang tindih
        n = min(PER_VIDEO, max(1, len(lst) // 3))
        awal = (BATCH * n) % len(lst)
        ambil = [(awal + int(i * len(lst) / n)) % len(lst) for i in range(n)]
        dipilih.extend(lst[i] for i in ambil)

    dipilih.sort(key=lambda p: p.stem)
    print(f"total frame dipilih: {len(dipilih)} "
          f"({ {k: len(v) for k, v in sorted(per_video.items())} })")

    for nomor in range(0, len(dipilih), PER_SHEET):
        bagian = dipilih[nomor:nomor + PER_SHEET]
        sel = []
        for i, p in enumerate(bagian):
            img = cv2.imread(str(p))
            sel.append((i, p, dengan_grid(img)))
        ch, cw = sel[0][2].shape[:2]
        sheet = np.full((ROWS * ch, COLS * cw, 3), 20, dtype=np.uint8)
        for k, (_, p, im) in enumerate(sel):
            r, c = divmod(k, COLS)
            sheet[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = im
        idx_ke = nomor // PER_SHEET + 1 + BATCH * 100
        nama = SHEET_DIR / f"lembar_{idx_ke:03d}.jpg"
        cv2.imwrite(str(nama), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
        # simpan daftar file supaya bisa dipetakan balik
        (SHEET_DIR / f"lembar_{idx_ke:03d}.txt").write_text(
            "\n".join(f"{i + 1}\t{p.stem}" for i, (_, p, _) in enumerate(sel)),
            encoding="utf-8")
        print(f"  {nama.name}: " + ", ".join(p.stem for _, p, _ in sel))


if __name__ == "__main__":
    main()