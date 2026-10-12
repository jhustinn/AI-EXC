"""Label yang dibuat dengan membaca lembar kerja bergrid.

Semua kotak ditulis dalam koordinat normal 0-100 (x1, y1, x2, y2) hasil
pembacaan visual, lalu dikonversi ke format YOLO. Frame kosong sengaja
tidak diberi label - lebih baik tidak ada label daripada label salah.

Kelas: 0 = bucket, 1 = excavator
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

OUT = PROJECT / "datasets" / "excavator"

# stem -> {"bucket": [(x1,y1,x2,y2), ...], "excavator": [(...)]}
LABEL: dict[str, dict[str, list[tuple]]] = {}


def isi(stem: str, cls: str, *kotak: tuple[int, int, int, int]) -> None:
    LABEL.setdefault(stem, {}).setdefault(cls, []).extend(kotak)


# ---------------- lembar 01 : v1 POV kabin (hanya bucket terlihat) -------------
isi("v1_2026-10-10_at_10_00020", "bucket", (37, 30, 57, 58))
isi("v1_2026-10-10_at_10_00240", "bucket", (43, 40, 73, 66))
isi("v1_2026-10-10_at_10_00460", "bucket", (38, 31, 70, 53))
isi("v1_2026-10-10_at_10_00680", "bucket", (55, 28, 95, 48))
isi("v1_2026-10-10_at_10_00920", "bucket", (38, 25, 63, 53))
isi("v1_2026-10-10_at_10_01140", "bucket", (55, 22, 96, 48))

# ---------------- lembar 02 ---------------------------------------------------
isi("v1_2026-10-10_at_10_01360", "bucket", (30, 8, 62, 32))
isi("v1_2026-10-10_at_10_01580", "bucket", (45, 8, 73, 33))
isi("v1_2026-10-10_at_10_01840", "bucket", (25, 2, 58, 28))
isi("v2_2026-10-10_at_10_00020", "excavator", (0, 48, 88, 96))
isi("v2_2026-10-10_at_10_00020", "bucket", (86, 45, 100, 62))
isi("v2_2026-10-10_at_10_00260", "excavator", (0, 25, 78, 82))
isi("v2_2026-10-10_at_10_00260", "bucket", (62, 27, 80, 50))
isi("v2_2026-10-10_at_10_00520", "excavator", (72, 5, 100, 72))
isi("v2_2026-10-10_at_10_00520", "bucket", (88, 50, 100, 72))

# ---------------- lembar 03 : v2 external -------------------------------------
isi("v2_2026-10-10_at_10_00760", "excavator", (0, 14, 100, 72))
isi("v2_2026-10-10_at_10_00760", "bucket", (35, 42, 63, 69))
isi("v2_2026-10-10_at_10_01020", "bucket", (28, 33, 56, 52))
isi("v2_2026-10-10_at_10_01260", "excavator", (15, 28, 100, 92))
isi("v2_2026-10-10_at_10_01260", "bucket", (18, 33, 43, 48))
isi("v2_2026-10-10_at_10_01520", "excavator", (25, 24, 100, 92))
isi("v2_2026-10-10_at_10_01520", "bucket", (27, 30, 51, 45))
isi("v2_2026-10-10_at_10_01760", "excavator", (30, 30, 100, 88))
isi("v2_2026-10-10_at_10_01760", "bucket", (33, 32, 56, 48))
isi("v2_2026-10-10_at_10_02040", "excavator", (0, 0, 92, 84))

# ---------------- lembar 04 : v3 (hanya bucket, badan keluar frame) ------------
isi("v3_2026-10-10_at_10_00020", "bucket", (42, 31, 69, 58))
isi("v3_2026-10-10_at_10_00160", "bucket", (62, 28, 96, 58))
isi("v3_2026-10-10_at_10_00320", "bucket", (55, 42, 91, 68))
isi("v3_2026-10-10_at_10_00460", "bucket", (55, 41, 100, 62))
isi("v3_2026-10-10_at_10_00640", "bucket", (55, 25, 93, 45))
isi("v3_2026-10-10_at_10_00780", "bucket", (50, 20, 86, 40))

# ---------------- lembar 05 ---------------------------------------------------
isi("v3_2026-10-10_at_10_00940", "bucket", (47, 27, 79, 50))
isi("v3_2026-10-10_at_10_01080", "bucket", (52, 27, 83, 50))
isi("v3_2026-10-10_at_10_01260", "bucket", (48, 32, 78, 48))
# v3_...01520 tidak diberi label: adegan kosong, tidak ada bucket
isi("v4_2026-10-10_at_10_00020", "excavator", (0, 32, 16, 72))
isi("v4_2026-10-10_at_10_00260", "excavator", (0, 30, 19, 64))
isi("v4_2026-10-10_at_10_00540", "excavator", (0, 28, 20, 62))

# ---------------- lembar 06 : v4 ---------------------------------------------
isi("v4_2026-10-10_at_10_00780", "excavator", (0, 36, 22, 58))
isi("v4_2026-10-10_at_10_01060", "excavator", (68, 38, 100, 56))
isi("v4_2026-10-10_at_10_01320", "excavator", (66, 46, 100, 64))
isi("v4_2026-10-10_at_10_01580", "excavator", (14, 17, 100, 62))
isi("v4_2026-10-10_at_10_01580", "bucket", (75, 41, 96, 58))
isi("v4_2026-10-10_at_10_01840", "excavator", (68, 0, 100, 64))
isi("v4_2026-10-10_at_10_01840", "bucket", (72, 42, 100, 62))
# v4_...02120 kosong, tidak diberi label

# ================= BATCH 2 (lembar 101-107) =================================
# Frame yang sudah dilabeli di batch 1 sengaja dilewati agar tidak dobel.

# lembar 101 - v1 POV kabin
isi("v1_2026-10-10_at_10_00080", "bucket", (33, 35, 58, 58))
isi("v1_2026-10-10_at_10_00280", "bucket", (42, 40, 70, 62))
isi("v1_2026-10-10_at_10_00640", "bucket", (58, 28, 92, 48))
isi("v1_2026-10-10_at_10_00820", "bucket", (42, 32, 72, 50))
isi("v1_2026-10-10_at_10_00980", "bucket", (60, 28, 95, 48))

# lembar 102 - v1 lalu v2
isi("v1_2026-10-10_at_10_01220", "bucket", (33, 5, 62, 32))
isi("v1_2026-10-10_at_10_01380", "bucket", (42, 8, 72, 33))
isi("v1_2026-10-10_at_10_01560", "bucket", (55, 28, 85, 50))
isi("v1_2026-10-10_at_10_01740", "bucket", (58, 22, 88, 48))
isi("v2_2026-10-10_at_10_00060", "excavator", (0, 25, 82, 72))
isi("v2_2026-10-10_at_10_00060", "bucket", (65, 27, 82, 50))
isi("v2_2026-10-10_at_10_00280", "excavator", (58, 17, 100, 55))
isi("v2_2026-10-10_at_10_00280", "bucket", (78, 31, 100, 53))

# lembar 103 - v2 external
isi("v2_2026-10-10_at_10_00480", "excavator", (43, 0, 82, 60))
isi("v2_2026-10-10_at_10_00480", "bucket", (43, 36, 73, 59))
isi("v2_2026-10-10_at_10_00680", "excavator", (12, 0, 100, 74))
isi("v2_2026-10-10_at_10_00680", "bucket", (14, 46, 46, 71))
isi("v2_2026-10-10_at_10_00880", "excavator", (30, 14, 100, 72))
isi("v2_2026-10-10_at_10_00880", "bucket", (31, 43, 59, 63))
isi("v2_2026-10-10_at_10_01080", "excavator", (40, 22, 100, 92))
isi("v2_2026-10-10_at_10_01080", "bucket", (41, 44, 67, 63))
isi("v2_2026-10-10_at_10_01280", "excavator", (18, 17, 100, 93))
isi("v2_2026-10-10_at_10_01280", "bucket", (19, 39, 49, 56))
isi("v2_2026-10-10_at_10_01480", "excavator", (36, 22, 100, 92))
isi("v2_2026-10-10_at_10_01480", "bucket", (37, 39, 59, 53))

# lembar 104 - v2 akhir lalu v3
isi("v2_2026-10-10_at_10_01720", "excavator", (36, 0, 100, 50))
isi("v2_2026-10-10_at_10_01720", "bucket", (37, 27, 61, 49))
isi("v2_2026-10-10_at_10_01920", "excavator", (53, 0, 100, 47))
isi("v2_2026-10-10_at_10_01920", "bucket", (54, 21, 81, 46))
isi("v3_2026-10-10_at_10_00140", "excavator", (0, 0, 94, 64))
isi("v3_2026-10-10_at_10_00140", "bucket", (61, 41, 93, 63))
isi("v3_2026-10-10_at_10_00260", "excavator", (0, 0, 84, 80))
isi("v3_2026-10-10_at_10_00260", "bucket", (49, 54, 83, 79))
isi("v3_2026-10-10_at_10_00380", "excavator", (0, 0, 92, 74))
isi("v3_2026-10-10_at_10_00380", "bucket", (51, 47, 91, 73))

# lembar 105 - v3
isi("v3_2026-10-10_at_10_00520", "excavator", (0, 0, 74, 60))
isi("v3_2026-10-10_at_10_00520", "bucket", (37, 34, 73, 59))
isi("v3_2026-10-10_at_10_00760", "excavator", (0, 0, 82, 52))
isi("v3_2026-10-10_at_10_00760", "bucket", (47, 31, 81, 51))
isi("v3_2026-10-10_at_10_00880", "excavator", (0, 0, 84, 50))
isi("v3_2026-10-10_at_10_00880", "bucket", (51, 31, 83, 49))
isi("v3_2026-10-10_at_10_01160", "excavator", (0, 0, 90, 49))
isi("v3_2026-10-10_at_10_01160", "bucket", (57, 31, 89, 48))

# lembar 106 - v4 (ekskavator di tepi frame)
isi("v4_2026-10-10_at_10_00460", "excavator", (0, 38, 15, 64))
isi("v4_2026-10-10_at_10_00660", "excavator", (0, 36, 17, 64))
isi("v4_2026-10-10_at_10_00920", "excavator", (0, 37, 21, 63))
isi("v4_2026-10-10_at_10_01120", "excavator", (74, 40, 100, 64))

# lembar 107 - v4
isi("v4_2026-10-10_at_10_01740", "excavator", (40, 18, 97, 60))
isi("v4_2026-10-10_at_10_01960", "excavator", (6, 4, 100, 60))
isi("v4_2026-10-10_at_10_01960", "bucket", (77, 34, 100, 56))
# v4_01340 dan v4_01540 dilewati: ekskavator tidak terbaca jelas

KELAS_ID = {"bucket": 0, "excavator": 2}
# CATATAN: kelas 1 dipakai truck dari label otomatis COCO. Excavator WAJIB
# pakai id 2. Awalnya salah pakai id 1 sehingga label truck dan excavator
# tercampur dalam file yang sama.


def main() -> None:
    n_bucket = n_exc = n_frame = 0
    for stem, kelas in LABEL.items():
        # cari di train atau val. Dicek file GAMBAR, karena frame tanpa
        # truck tidak punya file label sama sekali.
        lbl = None
        for split in ("train", "val"):
            if (OUT / "images" / split / f"{stem}.jpg").exists():
                lbl = OUT / "labels" / split / f"{stem}.txt"
                break
        if lbl is None:
            print(f"  Lewati (gambar tidak ada): {stem}")
            continue

        baris: list[str] = []
        # pertahankan label truck otomatis yang sudah ada
        if lbl.exists():
            isi_lama = [ln for ln in lbl.read_text(encoding="utf-8").splitlines()
                        if ln.strip() and int(ln.split()[0]) == 1]
            baris.extend(isi_lama)

        for nama, kotak in kelas.items():
            cid = KELAS_ID[nama]
            for x1, y1, x2, y2 in kotak:
                cx = (x1 + x2) / 200.0
                cy = (y1 + y2) / 200.0
                bw = (x2 - x1) / 100.0
                bh = (y2 - y1) / 100.0
                if bw <= 0 or bh <= 0 or not (0 <= cx <= 1 and 0 <= cy <= 1):
                    continue
                baris.append(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                if nama == "bucket":
                    n_bucket += 1
                else:
                    n_exc += 1

        lbl.write_text("\n".join(baris) + "\n", encoding="utf-8")
        n_frame += 1

    print(f"frame diberi label : {n_frame}")
    print(f"kotak bucket       : {n_bucket}")
    print(f"kotak excavator    : {n_exc}")


if __name__ == "__main__":
    main()