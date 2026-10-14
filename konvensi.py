from pathlib import Path
import cv2
import numpy as np

D = Path("EXCAVATOR MODEL/excavator.v3i.yolov8/valid/images")
L = Path("EXCAVATOR MODEL/excavator.v3i.yolov8/valid/labels")
NAMA = {0: "arm", 1: "boom", 2: "bucket"}
WARNA = {0: (0, 165, 255), 1: (255, 0, 255), 2: (0, 200, 0)}

files = sorted(D.glob("*.jpg"))[:4]
panel = []
for f in files:
    img = cv2.imread(str(f))
    h, w = img.shape[:2]
    for ln in (L / f"{f.stem}.txt").read_text(encoding="utf-8").splitlines():
        b = ln.split()
        if len(b) != 5:
            continue
        cid = int(b[0])
        cx, cy, bw, bh = [float(x) for x in b[1:]]
        x1 = int((cx - bw / 2) * w); y1 = int((cy - bh / 2) * h)
        x2 = int((cx + bw / 2) * w); y2 = int((cy + bh / 2) * h)
        cv2.rectangle(img, (x1, y1), (x2, y2), WARNA[cid], 3)
        cv2.putText(img, NAMA[cid], (x1, max(16, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, WARNA[cid], 3)
    img = cv2.resize(img, (480, 480))
    cv2.putText(img, f.name[:12], (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
    cv2.putText(img, f.name[:12], (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    panel.append(img)

out = Path("data/konvensi_arm_boom.jpg")
out.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(out), np.vstack([np.hstack(panel[:2]), np.hstack(panel[2:4])]),
            [cv2.IMWRITE_JPEG_QUALITY, 92])
print("->", out)
