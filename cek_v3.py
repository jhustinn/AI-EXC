import sys; sys.path.insert(0,"src")
from ultralytics import YOLO
m=YOLO("runs/alat_berat_v3/weights/best.pt")
r=m.val(data="datasets/alat_berat/data.yaml",split="val",workers=0,imgsz=512,batch=8,verbose=False)
for i,n in m.names.items():
    print(f"  {n:12s} mAP50={float(r.box.ap50[i]):.3f}")
