import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector, _terlihat_langit
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; tot=0; lolos_langit=0; bucket_tetap=0
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%5: continue
    r=d.detect(f)
    for o in r.buckets:
        tot+=1
        if _terlihat_langit(f,o.x1,o.y1,o.x2,o.y2): lolos_langit+=1
    bucket_tetap += 1 if r.buckets else 0
cap.release()
nilai=max(1,2035//5)
print(f"kotak bucket SESUDAH penyaring : {tot}")
print(f"  ...yang masihcontains langit  : {lolos_langit}")
print(f"frame dengan bucket            : {bucket_tetap}/{nilai} = {bucket_tetap/nilai*100:.0f}%")
print()
print("sebelum: 241 kotak, 17 langit (7%)")
