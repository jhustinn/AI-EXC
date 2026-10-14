import cv2, sys, math
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
from excavator.objek import set_ukuran_gambar
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; tot=0; dalam=0; sudut=[]
while True:
    ok,f=cap.read()
    if not ok: break
    h_,w_ = f.shape[:2]
    set_ukuran_gambar(w_,h_)
    h=d.detect(f)
    if not h.ekskavator: continue
    n+=1
    for e in h.ekskavator:
        if e.lengan is None or e.lutut is None: continue
        tot+=1
        lx,ly = e.lutut
        if 0<=lx<=w_ and 0<=ly<=h_: dalam+=1
        (bx,by),(sx,sy)=e.lengan
        a=math.degrees(math.atan2(by-ly,bx-lx))
        b=math.degrees(math.atan2(sy-ly,sx-lx))
        d2=abs((a-b+180)%360-180)
        sudut.append(min(d2,360-d2))
cap.release()
import statistics
print(f"pasangan bucket+body : {tot}")
print(f"titik lutut di dalam gambar : {dalam} ({dalam/max(1,tot)*100:.0f}%)")
if sudut:
    print(f"sudut belok lengan (median) : {statistics.median(sudut):.0f} derajat")
    print(f"sudut belok (min - maks)    : {min(sudut):.0f} - {max(sudut):.0f}")
    print()
    print("referensi lengan ekskavator nyata: ~90-120 derajat")
