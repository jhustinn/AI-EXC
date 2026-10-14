import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
from excavator.objek import set_ukuran_gambar
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; dibuat=0
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%17: continue
    h_,w_=f.shape[:2]; set_ukuran_gambar(w_,h_)
    r=d.detect(f)
    for e in r.ekskavator:
        if e.lutut is None or e.bucket is None: continue
        (bx,by),(sx,sy)=e.lengan; lx,ly=e.lutut
        # kotak deteksi asli, agar kelihatan di mana model benar-benar melihat
        cv2.rectangle(f,(int(e.bucket.x1),int(e.bucket.y1)),(int(e.bucket.x2),int(e.bucket.y2)),(0,255,0),2)
        cv2.rectangle(f,(int(e.badan.x1),int(e.badan.y1)),(int(e.badan.x2),int(e.badan.y2)),(255,80,80),2)
        cv2.line(f,(int(bx),int(by)),(int(lx),int(ly)),(255,0,255),3)
        cv2.line(f,(int(lx),int(ly)),(int(sx),int(sy)),(255,0,255),3)
        cv2.circle(f,(int(lx),int(ly)),6,(255,255,255),-1)
        cv2.putText(f,f"frame {n}",(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
        cv2.imwrite(f"data/cek_{n:04d}.jpg",f)
        dibuat+=1
        break
    if dibuat>=3: break
cap.release()
print("dibuat",dibuat)
