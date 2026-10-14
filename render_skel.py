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
    h_,w_=f.shape[:2]
    set_ukuran_gambar(w_,h_)
    if n%17: continue
    r=d.detect(f)
    if not any(e.lutut for e in r.ekskavator): continue
    for e in r.ekskavator:
        if e.lutut is None: continue
        (bx,by),(sx,sy)=e.lengan
        lx,ly=e.lutut
        cv2.line(f,(int(bx),int(by)),(int(lx),int(ly)),(255,0,255),4)
        cv2.line(f,(int(lx),int(ly)),(int(sx),int(sy)),(255,0,255),4)
        cv2.circle(f,(int(lx),int(ly)),7,(255,255,255),-1)
        cv2.circle(f,(int(bx),int(by)),7,(0,255,0),-1)
        cv2.circle(f,(int(sx),int(sy)),7,(255,80,80),-1)
        cv2.putText(f,"bucket",(int(bx)-20,int(by)-12),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
        cv2.putText(f,"LUTUT(geometris)",(int(lx)-70,int(ly)-14),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,255,255),2)
        cv2.putText(f,"body",(int(sx)-20,int(sy)-12),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,80,80),2)
        cv2.imwrite(f"data/skeleton_{dibuat:02d}.jpg",f)
        dibuat+=1
        break
    if dibuat>=4: break
cap.release()
print("gambar dibuat:", dibuat)
