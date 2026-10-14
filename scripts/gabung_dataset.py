"""Gabungkan tiga sumber label jadi satu dataset.

1. Dataset publik LibreYOLO/excavators-czvg9 (roboflow-100, CC BY 4.0)
   2234 frame dari video konstruksi. Kelas EXCAVATORS dan dump truck.
   Ini sumber terbesar dan paling dekat dengan domain video kita.

2. Dataset Robofflow excavator-5jscg v3 (CC BY 4.0, milik pengguna)
   120 frame dengan kelas arm, boom, bucket. Jumlahnya kecil dan sebagian
   besar foto katalog (background putih, merek Hyundai), tapi ini satu-
   satunya sumber yang menganotasi bucket, boom, dan arm - persis sinyal
   komposisi yang dibutuhkan untuk identitas ekskavator.

3. Label manual kita sendiri dari video referensi (67 frame).

Petakan kelas akhir:
  0 = excavator  <- EXCAVATORS (publik) + excavator (manual)
  1 = truck      <- dump truck (publik)  + truck (manual)
  2 = bucket     <- bucket (manual) + bucket (roboflow pengguna)
  3 = boom       <- boom (roboflow pengguna)
  4 = arm        <- arm (roboflow pengguna)
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
SRC_PUBLIK = PROJECT / "data" / "unduhan" / "excavators"
SRC_BAGIAN = PROJECT / "EXCAVATOR MODEL" / "excavator.v3i.yolov8"
SRC_MANUAL = PROJECT / "datasets" / "excavator"
DST = PROJECT / "datasets" / "alat_berat"

# publik -> akhir ; None berarti dibuang
PETAKAN_PUBLIK = {0: 0, 1: 1, 2: None}
# dataset bagian (arm=0, boom=1, bucket=2) -> akhir
PETAKAN_BAGIAN = {0: None, 1: None, 2: 2}
# manual (bucket=0, truck=1, excavator=2) -> akhir
PETAKAN_MANUAL = {0: 2, 1: 1, 2: 0}

_SPLIT_GRUP: dict = {}


def split_grup(dasar: str) -> str:
    """Satu gambar asli selalu dapat split yang sama, lintas folder."""
    if dasar not in _SPLIT_GRUP:
        h = int(hashlib.md5(dasar.encode()).hexdigest(), 16)
        _SPLIT_GRUP[dasar] = "train" if h % 10 < 8 else "val"
    return _SPLIT_GRUP[dasar]


KELAS = ["excavator", "truck", "bucket"]

# Bucket hanya ada dari label manual + dataset Roboflow pengguna (432 kotak)
# sedangkan excavator 1662. Boom dan arm juga tipis. Tanpa oversampling,
# model mengabaikan kelas tipis itu - padahal boom dan arm justru sinyal
# komposisi yang dibutuhkan. Frame yang memuat kelas tipis digandakan.
# CATATAN: kelas ini jadi SEJAK they've diulang, jadi hasilnya hanya
# indikasi arah, bukan angka最终 yang bisa dipertanggungjawabkan.
OVERSAMPLE_BUCKET = 8
OVERSAMPLE_TIPIS = 6          # untuk boom dan arm
KELAS_TIPIS = {2}       # bucket, boom, arm


def konversi(src_dir: Path, split_tujuan: str, peta: dict) -> tuple[int, int]:
    n_img = n_kotak = 0
    imgs = src_dir / "images"
    lbls = src_dir / "labels"
    if not imgs.is_dir():
        return 0, 0

    # Roboflow membuat 3 salinan per gambar asli (asli + 2 horizontal flip).
    # Versi lama memakai semuanya dan membagi acak, jadi gambar yang sama
    # bisa ada di train DAN val. Itu membuat mAP boom/arm meledak ke 0,99
    # padahal di video asli 0%. Di sini hanya satu salinan per gambar asli
    # yang dipakai, sehingga tidak ada gambar yang bisa bocor ke dua split.
    for img in sorted(imgs.glob("*.jpg")):
        dasar = img.name.split(".rf.")[0]
        if ".rf." in img.name:
            tujuan = split_grup(dasar)
        else:
            tujuan = split_tujuan
        lbl = lbls / f"{img.stem}.txt"
        if not lbl.exists():
            continue

        baris: list[str] = []
        for ln in lbl.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            bagian = ln.split()
            if len(bagian) != 5:
                continue
            baru = peta.get(int(bagian[0]), "SKIP")
            # peta memakai None ATAU "SKIP" untuk kelas yang dibuang
            if baru == "SKIP" or baru is None:
                continue
            baris.append(f"{baru} {bagian[1]} {bagian[2]} {bagian[3]} {bagian[4]}")
            n_kotak += 1

        if not baris:
            continue  # frame tanpa kelas yang kita pakai, dilewati

        (DST / "images" / split_tujuan).mkdir(parents=True, exist_ok=True)
        (DST / "labels" / split_tujuan).mkdir(parents=True, exist_ok=True)
        shutil.copy2(img, DST / "images" / split_tujuan / f"pub_{img.name}")
        (DST / "labels" / split_tujuan / f"pub_{img.stem}.txt").write_text(
            "\n".join(baris) + "\n", encoding="utf-8")
        n_img += 1
    return n_img, n_kotak


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    for split in ("train", "val"):
        (DST / "images" / split).mkdir(parents=True, exist_ok=True)
        (DST / "labels" / split).mkdir(parents=True, exist_ok=True)

    total = {"train": [0, 0], "val": [0, 0]}
    for publik_split, tujuan in (("train", "train"), ("valid", "val")):
        img, ktk = konversi(SRC_PUBLIK / publik_split, tujuan, PETAKAN_PUBLIK)
        total[tujuan][0] += img
        total[tujuan][1] += ktk
        print(f"publik  {publik_split:5s} -> {tujuan:5s}: {img} frame, {ktk} kotak")

    # dataset Roboflow milik pengguna: arm / boom / bucket.
    # Bagian train digandakan karena jumlahnya hanya 96 frame dan itu
    # satu-satunya sumber anotasi boom serta arm.
    if SRC_BAGIAN.is_dir():
        for bagi_split, tujuan in (("train", "train"), ("valid", "val")):
            img, ktk = konversi(SRC_BAGIAN / bagi_split, tujuan, PETAKAN_BAGIAN)
            total[tujuan][0] += img
            total[tujuan][1] += ktk
            print(f"bagian  {bagi_split:5s} -> {tujuan:5s}: {img} frame, {ktk} kotak")

            if bagi_split != "train":
                continue
            for rep in range(1, OVERSAMPLE_TIPIS):
                dipakai_ov: set = set()
                for lbl in sorted((SRC_BAGIAN / bagi_split / "labels").glob("*.txt")):
                    if lbl.name.split(".rf.")[0] in dipakai_ov:
                        continue
                    dipakai_ov.add(lbl.name.split(".rf.")[0])
                    isi = [ln for ln in lbl.read_text(encoding="utf-8").splitlines()
                           if ln.strip()]
                    baru = []
                    for ln in isi:
                        bagian = ln.split()
                        if len(bagian) != 5:
                            continue
                        kelas = PETAKAN_BAGIAN[int(bagian[0])]
                        if kelas is None:
                            continue  # kelas dibuang - JANGAN tulis "None"
                        baru.append(f"{kelas} "
                                    f"{bagian[1]} {bagian[2]} {bagian[3]} {bagian[4]}")
                    if not baru:
                        continue
                    img = SRC_BAGIAN / bagi_split / "images" / f"{lbl.stem}.jpg"
                    if not img.exists():
                        continue
                    shutil.copy2(img, DST / "images" / "train" / f"bg{rep}_{img.name}")
                    (DST / "labels" / "train" / f"bg{rep}_{lbl.stem}.txt").write_text(
                        "\n".join(baru) + "\n", encoding="utf-8")
                    total["train"][0] += 1
                    total["train"][1] += len(baru)
    else:
        print("bagian  TIDAK ADA - kelas boom dan arm akan kosong")

    # label manual, sudah dipisah train/val oleh pisah_val.py
    for split in ("train", "val"):
        folder = SRC_MANUAL / "labels" / split
        if not folder.is_dir():
            continue
        n = k = 0
        for lbl in sorted(folder.glob("*.txt")):
            isi = [ln for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()]
            baru: list[str] = []
            for ln in isi:
                bagian = ln.split()
                if len(bagian) != 5:
                    continue
                cid = PETAKAN_MANUAL.get(int(bagian[0]), "SKIP")
                if cid == "SKIP":
                    continue
                baru.append(f"{cid} {bagian[1]} {bagian[2]} {bagian[3]} {bagian[4]}")
                k += 1
            if not baru:
                continue
            img = SRC_MANUAL / "images" / split / f"{lbl.stem}.jpg"
            if not img.exists():
                continue
            shutil.copy2(img, DST / "images" / split / f"man_{img.name}")
            isi_kelas = {int(b.split()[0]) for b in baru if b.split()}
            target = DST / "labels" / split / f"man_{lbl.stem}.txt"
            target.write_text("\n".join(baru) + "\n", encoding="utf-8")
            n += 1

            # bucket ada di kelas 2 pada skema gabungan
            if split == "train" and 2 in isi_kelas:
                for rep in range(1, OVERSAMPLE_BUCKET):
                    shutil.copy2(
                        img,
                        DST / "images" / split / f"ov{rep}_{img.name}")
                    (DST / "labels" / split /
                     f"ov{rep}_{lbl.stem}.txt").write_text(
                        "\n".join(baru) + "\n", encoding="utf-8")
                    n += 1
                    k += sum(1 for b in baru if b.split()[0] == "2")
        total[split][0] += n
        total[split][1] += k
        print(f"manual {split:5s} -> {split:5s}: {n} frame, {k} kotak")

    # ringkasan per kelas
    from collections import Counter
    rusak: list[str] = []
    for split in ("train", "val"):
        c: Counter = Counter()
        for lbl in (DST / "labels" / split).glob("*.txt"):
            for ln in lbl.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    c[int(ln.split()[0])] += 1
                except ValueError:
                    rusak.append(f"{lbl.name}: {ln}")
                    continue
        print(f"\n{split}: {total[split][0]} frame, {total[split][1]} kotak")
        for i, nama in enumerate(KELAS):
            print(f"   {nama:12s} {c[i]:5d} kotak")

    (DST / "data.yaml").write_text(
        "# Gabungan 3 sumber (lisensi CC BY 4.0):\n"
        "#   1. LibreYOLO/excavators-czvg9 - video konstruksi, 2234 frame\n"
        "#   2. Roboflow excavator-5jscg v3 - arm/boom/bucket, 120 frame\n"
        "#   3. Label manual dari video referensi - 67 frame\n"
        f"path: {DST.as_posix()}\n"
        f"train: images/train\n"
        f"val: images/val\n\n"
        f"nc: {len(KELAS)}\n"
        f"names:\n"
        + "".join(f"  {n}: {nama}\n" for n, nama in enumerate(KELAS)).rstrip("\n"),
        encoding="utf-8",
    )
    print(f"\ndata.yaml -> {DST / 'data.yaml'}")
    if rusak:
        print(f"\nPERINGATAN: {len(rusak)} baris label rusak")
        for r in rusak[:5]:
            print(f"   {r}")
    else:
        print("\nverifikasi: tidak ada baris label rusak")


if __name__ == "__main__":
    main()
