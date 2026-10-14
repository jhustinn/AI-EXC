import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector, _terlihat_langit
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; tot=0; sky=0; pair=0; frame_pair=0; checked=0
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%5: continue
    r=d.detect(f); checked+=1
    for o in r.buckets:
        tot+=1
        if _terlihat_langit(f,o.x1,o.y1,o.x2,o.y2): sky+=1
    if r.ekskavator:
        frame_pair+=1
        for e in r.ekskavator:
            if e.lengan is not None: pair+=1
cap.release()
print(f"frame diperiksa        : {checked}")
print(f"kotak bucket total     : {tot}")
print(f"  masih berisi langit  : {sky}  ({sky/max(1,tot)*100:.1f}%)")
print(f"frame dengan ekskavator: {frame_pair}/{checked} = {frame_pair/checked*100:.0f}%")
print(f"skeleton digambar      : {pair}")
