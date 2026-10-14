import cv2, sys, numpy as np
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; tot=0; kosong=0

def nonsky(img, box):
    x1,y1,x2,y2=[int(v) for v in box]
    x1,y1=max(0,x1),max(0,y1); x2,y2=min(img.shape[1],x2),min(img.shape[0],y2)
    if x2-x1<8 or y2-y1<8: return False
    crop=img[y1:y2,x1:x2].astype(np.float32)
    b,g,r=crop[...,0].mean(),crop[...,1].mean(),crop[...,2].mean()
    mx=max(b,g,r); mn=min(b,g,r)
    sat=(mx-mn)/max(1.0,mx)
    return not (b>r+18 and b>120 and sat<0.30)   # langit: biru, cerah, jenuh rendah
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%5: continue
    r=d.detect(f)
    for o in r.buckets:
        tot+=1
        if not nonsky(f,o.bbox): kosong+=1
cap.release()
print(f"kotak bucket yang dianalisis : {tot}")
print(f"  ...yang isinya langit/kosong: {kosong} ({kosong/max(1,tot)*100:.0f}%)")
print()
print("patokan: bucket excavator SELALU kuning/oram/coklat (tanah, logam),")
print("tidak pernah biru langit")

