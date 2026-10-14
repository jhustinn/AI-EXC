import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
def _bertumpuk(a, b):
    x1=max(a.x1,b.x1); y1=max(a.y1,b.y1); x2=min(a.x2,b.x2); y2=min(a.y2,b.y2)
    if x2<=x1 or y2<=y1: return 0.0
    return ((x2-x1)*(y2-y1))/max(1.0,a.area)
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; tot=0; salah=0; iou_list=[]
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%5: continue
    r=d.detect(f)
    trucks=[o for o in r.objek if o.kelas=="truck"]
    if not trucks: continue
    t=max(trucks,key=lambda o:o.area)
    for b in r.badan:
        tot+=1
        # berapa bagian dari kotak "excavator" yang berada DI DALAM kotak truck
        iou=_bertumpuk(b,t)
        iou_list.append(iou)
        if iou>0.5: salah+=1
cap.release()
import statistics
print(f"kotak kelas 'excavator' yang dianalisis : {tot}")
print(f"  ...yang 50%+ berada di dalam kotak truck: {salah} ({salah/max(1,tot)*100:.0f}%)")
print(f"  tumpang tindih median                  : {statistics.median(iou_list):.2f}")
print(f"  tumpang tindih maks                    : {max(iou_list):.2f}")
