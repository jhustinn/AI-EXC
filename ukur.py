import sys, time
sys.path.insert(0, "src")
from collections import Counter
import cv2
from ultralytics import YOLO

DATA = "datasets/alat_berat/data.yaml"
VID  = "INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4"
m = YOLO("runs/alat_berat_v3/weights/best.pt")

print("=" * 60)
print("1. mAP PER KELAS (validasi)")
print("=" * 60)
r = m.val(data=DATA, split="val", workers=0, imgsz=640, batch=8, verbose=False)
for i, n in m.names.items():
    print(f"  {n:12s} mAP50={float(r.box.ap50[i]):.3f}  mAP50-95={float(r.box.ap[i]):.3f}")

print()
print("=" * 60)
print("2. DETEKSI PER VIDEO (tiap 10 frame)")
print("=" * 60)
cap = cv2.VideoCapture(VID)
n = 0
per = Counter()
frame_ada = Counter()
best = {}
mulai = time.perf_counter()
while n < 240:
    ok, frame = cap.read()
    if not ok:
        break
    n += 1
    if n % 10:
        continue
    res = m.predict(frame, conf=0.35, imgsz=640, device="0", verbose=False)[0]
    if res.boxes is None:
        continue
    seen = set()
    for cid, cf in zip(res.boxes.cls.cpu().numpy(), res.boxes.conf.cpu().numpy()):
        nm = m.names[int(cid)]
        per[nm] += 1
        seen.add(nm)
        if float(cf) > best.get(nm, 0):
            best[nm] = float(cf)
    for s_ in seen:
        frame_ada[s_] += 1
cap.release()
nilai = max(1, n // 10)
print("kelas frame terdeteksi   conf maks")
print("-" * 44)
for k in m.names.values():
    print(f"  {k:10s}{frame_ada[k]/nilai*100:>15.0f}%{best.get(k,0):>11.2f}")
print(f"\n{nilai} frame dianalisa, {time.perf_counter()-mulai:.1f} detik")
