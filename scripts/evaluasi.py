"""Evaluasi model alat berat + uji nyata di video."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(r"E:\App\AI-CCTV")
sys.path.insert(0, str(PROJECT / "src"))

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

BEST = PROJECT / "runs" / "alat_berat_v1" / "weights" / "best.pt"
DATA = PROJECT / "datasets" / "excavator" / "data.yaml"

model = YOLO(str(BEST))
print("kelas model:", model.names)

print("\n" + "=" * 70)
print("EVALUASI DI VALIDASI")
print("=" * 70)
r = model.val(data=str(DATA), split="val", verbose=False)
for i, n in model.names.items():
    p = float(r.box.p[i])
    r50 = float(r.box.r50[i])
    print(f"  {n:12s} mAP50={p:.3f}   mAP50-95={r50:.3f}")

print()
print("=" * 70)
print("UJI NYATA DI VIDEO (bukan frame training)")
print("=" * 70)
SRC = PROJECT / "INGIN SEPERTI INI"
for path in sorted(SRC.glob("*.mp4")):
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    per: Counter = Counter()
    frame_ada: dict[str, int] = Counter()
    terbaik: dict[str, float] = {}
    n = 0
    for idx in range(0, total, 8):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        res = model.predict(frame, conf=0.30, imgsz=640, device="0", verbose=False)[0]
        n += 1
        if res.boxes is None:
            continue
        seen = set()
        for cid, cf in zip(res.boxes.cls.cpu().numpy(),
                           res.boxes.conf.cpu().numpy()):
            nm = model.names[int(cid)]
            per[nm] += 1
            seen.add(nm)
            if float(cf) > terbaik.get(nm, 0):
                terbaik[nm] = float(cf)
        for s in seen:
            frame_ada[s] += 1
    cap.release()
    print(f"\n{path.name}  ({n} frame)")
    for nm in ("bucket", "excavator", "truck"):
        if per[nm]:
            print(f"   {nm:12s} {per[nm]:4d} kotak | di "
                  f"{frame_ada[nm]:3d}/{n} frame | conf maks {terbaik[nm]:.2f}")
        else:
            print(f"   {nm:12s} TIDAK ADA")