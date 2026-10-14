import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from ultralytics import YOLO
cfg = load_config("config.excavator.yaml")
m = YOLO("runs/alat_berat_v3/weights/best.pt")
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0
# frame 51 (17*3) = yang jadi skeleton_03
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n != 51: continue
    r=m.predict(f, conf=0.25, imgsz=640, device="0", verbose=False)[0]
    print("DETEKSI ASLI frame 51:")
    for box,cid,cf in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.cls.cpu().numpy(), r.boxes.conf.cpu().numpy()):
        nm=m.names[int(cid)]
        x1,y1,x2,y2=[float(v) for v in box]
        cx,cy=(x1+x2)/2,(y1+y2)/2
        area=((x2-x1)*(y2-y1))/(f.shape[0]*f.shape[1])
        print(f"  {nm:12s} conf={cf:.2f}  pusat=({cx:.0f},{cy:.0f})  {x1:.0f},{y1:.0f}-{x2:.0f},{y2:.0f}  luas={area*100:.1f}%")
    break
cap.release()
