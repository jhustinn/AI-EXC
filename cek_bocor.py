import hashlib
from pathlib import Path
D = Path("datasets/alat_berat/images")
grup = {}
for split in ("train", "val"):
    for f in (D / split).glob("*.jpg"):
        nama = f.name.split("_", 1)[1] if "_" in f.name else f.name
        dasar = nama.split(".rf.")[0]
        if nama.startswith("man_"):
            continue
        grup.setdefault(dasar, set()).add(split)
bocor = {k: v for k, v in grup.items() if len(v) > 1}
print(f"kelompok unik: {len(grup)}")
print(f"BOCOR ke dua split: {len(bocor)}")
for k in list(bocor)[:5]:
    print("  ", k)
