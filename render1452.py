import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n!=1452: continue
    r=d.detect(f)
    print("SEMUA DETEKSI frame 1452:")
    for o in r.objek:
        x1,y1,x2,y2=[int(v) for v in o.bbox]
        print(f"  {o.kelas:12s} conf={o.conf:.2f} ditahan={o.ditahan}  {x1},{y1}-{x2},{y2}")
    for o in r.buckets:
        x1,y1,x2,y2=[int(v) for v in o.bbox]
        cv2.rectangle(f,(x1,y1),(x2,y2),(0,255,0),3)
        cv2.putText(f,f"BUCKET {o.conf:.2f}",(x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)
    for o in r.badan:
        x1,y1,x2,y2=[int(v) for v in o.bbox]
        cv2.rectangle(f,(x1,y1),(x2,y2),(255,0,255),3)
        cv2.putText(f,f"BODY {o.conf:.2f}",(x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,0,255),2)
    cv2.imwrite("data/salah_1452.jpg",f)
    break
cap.release()
