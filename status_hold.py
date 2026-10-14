import cv2, sys
sys.path.insert(0,"src")
from excavator.config import load_config
from excavator.detector import Detector
cfg = load_config("config.excavator.yaml")
d = Detector(cfg.detector, cfg.zones, cfg.project_root)
cap = cv2.VideoCapture("INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4")
n=0; fresh=0; held=0; none=0; checked=0
while True:
    ok,f=cap.read()
    if not ok: break
    n+=1
    if n%5: continue
    r=d.detect(f); checked+=1
    if not r.ekskavator: none+=1; continue
    if any(e.komponen.get("ditahan") for e in r.ekskavator): held+=1
    else: fresh+=1
cap.release()
print(f"frame diperiksa     : {checked}")
print(f"  deteksi langsung  : {fresh} ({fresh/checked*100:.0f}%)")
print(f"  kotak ditahan     : {held} ({held/checked*100:.0f}%)")
print(f"  tidak ada sama sekali : {none} ({none/checked*100:.0f}%)")
