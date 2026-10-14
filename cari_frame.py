import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; cocok=[]
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%3: continue
    r=d.detect(f)
    for e in r.ekskavator:
        bc = e.bucket.conf if e.bucket is not None else 0.0
        if abs(e.conf-0.65)<0.02 and abs(bc-0.59)<0.03:
            h_,w_=f.shape[:2]
            cocok.append((n,e.conf,bc,e.badan.cy/h_,e.badan.x1/w_,e.badan.x2/w_,
                          e.bucket is not None, any(x.komponen.get("ditahan") for x in r.ekskavator)))
            break
    if len(cocok)>=8: break
cap.release()
print("frame  conf  buck  cy/h   x1/w  x2/w  adaBucket  ditahan")
for c in cocok:
    print(f"{c[0]:5d}  {c[1]:.2f}  {c[2]:.2f}  {c[3]:.2f}  {c[4]:.2f}  {c[5]:.2f}   {c[6]}   {c[7]}")
