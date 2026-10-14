import sys
sys.path.insert(0, "src")
import cv2
from pathlib import Path
from ultralytics import YOLO

m = YOLO("runs/alat_berat_v3/weights/best.pt")

def tampilkan(judul, files):
    print("=" * 58)
    print(judul)
    print("=" * 58)
    for f in files:
        img = cv2.imread(str(f))
        if img is None:
            continue
        res = m.predict(img, conf=0.20, imgsz=640, device="0", verbose=False)[0]
        if res.boxes is None:
            print(f"  {f.name[-28:]:30s} TIDAK ADA deteksi")
            continue
        ket = ", ".join(
            f"{m.names[int(c)]}={float(f2):.2f}"
            for c, f2 in zip(res.boxes.cls.cpu().numpy(),
                             res.boxes.conf.cpu().numpy()))
        print(f"  {f.name[-28:]:30s} {ket}")

# A. foto katalog Roboflow (kondisi yang dipelajari model)
valid = sorted(Path("EXCAVATOR MODEL/excavator.v3i.yolov8/valid/images").glob("*.jpg"))
tampilkan("A. FOTO ROBOFLOW (yang dipelajari model)", valid[:5])

# B. video Anda (kConditions yang mau dipakai)
DS = Path("datasets/excavator/images/train")
vid = [DS / f"{s}.jpg" for s in
 ["v2_2026-10-10_at_10_00260", "v2_2026-10-10_at_10_01080",
        "v4_2026-10-10_at_10_01740", "v1_2026-10-10_at_10_00240"]]
tampilkan("B. VIDEO ANDA (yang mau dipakai)", vid)
