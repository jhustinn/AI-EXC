import cv2
import numpy as np

def solve_kinematics(frame, badan_box=None, bucket_box=None):
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Cat yellow mask
    mask = cv2.inRange(hsv, np.array([10, 40, 40]), np.array([40, 255, 255]))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    cnts, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    
    # Filter contours that belong to the excavator
    exc_cnts = [c for c in cnts if cv2.contourArea(c) > 500]
    if not exc_cnts:
        return None
    
    all_pts = np.vstack([c.reshape(-1, 2) for c in exc_cnts])
    
    # 1. Elbow (Lutut) = top-most yellow apex
    upper_pts = all_pts[(all_pts[:, 1] < 350) & (all_pts[:, 0] > 100)]
    if len(upper_pts) < 10:
        return None
    top_pts = upper_pts[upper_pts[:, 1].argsort()][:15]
    elbow_x = float(np.median(top_pts[:, 0]))
    elbow_y = float(np.median(top_pts[:, 1]))
    
    # 2. Base = boom mounting on excavator body
    if badan_box is not None:
        bx1, by1, bx2, by2 = badan_box
        base_x = bx2 - (bx2 - bx1) * 0.08 if elbow_x <= (bx1 + bx2)/2 else bx1 + (bx2 - bx1) * 0.70
        base_y = by1 + (by2 - by1) * 0.25
    else:
        base_x = min(w - 10, elbow_x + 120)
        base_y = elbow_y + 160
        
    # 3. Arm trajectory:
    # Yellow points belonging to arm: below elbow_y, extending towards bucket
    arm_pts = all_pts[(all_pts[:, 1] > elbow_y + 25) & (all_pts[:, 1] < 600)]
    arm_pts = arm_pts[arm_pts[:, 0] <= elbow_x + 40]
    arm_pts = arm_pts[(arm_pts[:, 0] >= 50) & (arm_pts[:, 1] <= 520)]
    
    wrist = None
    tip = None
    derived_bucket = None
    valid_bucket = False
    
    if bucket_box is not None:
        bkx1, bky1, bkx2, bky2 = bucket_box
        crop = frame[max(0, int(bky1)):min(h, int(bky2)), max(0, int(bkx1)):min(w, int(bkx2))]
        if crop.size > 0:
            c_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            c_mask = cv2.inRange(c_hsv, np.array([10, 40, 40]), np.array([40, 255, 255]))
            y_ratio = np.count_nonzero(c_mask) / c_mask.size
            if y_ratio >= 0.015 and (elbow_x - bkx2) > -80:
                valid_bucket = True
                wrist = ((bkx1 + bkx2)/2, bky1)
                tip = ((bkx1 + bkx2)/2, bky2)
                derived_bucket = bucket_box
    
    if not valid_bucket and len(arm_pts) >= 10:
        sorted_arm_y = arm_pts[arm_pts[:, 1].argsort()]
        lowest_cluster = sorted_arm_y[-max(8, int(len(sorted_arm_y) * 0.06)):]
        wrist_x = float(np.median(lowest_cluster[:, 0]))
        wrist_y = float(np.median(lowest_cluster[:, 1]))
        wrist = (wrist_x, wrist_y)
        
        dx = wrist_x - elbow_x
        dy = wrist_y - elbow_y
        dist = np.hypot(dx, dy)
        if dist > 1e-3:
            ux, uy = dx / dist, dy / dist
        else:
            ux, uy = -0.3, 0.95
        
        bucket_len = 65.0
        tip_x = wrist_x + ux * bucket_len * 0.6 - 15.0
        tip_y = wrist_y + uy * bucket_len
        tip = (tip_x, tip_y)
        
        bh = 75.0
        derived_bucket = (wrist_x - 55.0, wrist_y - 10.0, wrist_x + 35.0, wrist_y + bh)
        
    return {
        'base': (base_x, base_y),
        'lutut': (elbow_x, elbow_y),
        'wrist': wrist,
        'tip': tip,
        'bucket_box': derived_bucket,
        'is_derived': not valid_bucket
    }

cap = cv2.VideoCapture('INGIN SEPERTI INI/WhatsApp Video 2026-10-10 at 10.43.03 AM2.mp4')
for f_idx in [1000, 1500, 1510, 1520, 1600]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
    ret, frame = cap.read()
    res = solve_kinematics(frame)
    if res:
        print(f"Frame {f_idx}: Lutut={[round(x,1) for x in res['lutut']]}, Wrist={[round(x,1) for x in res['wrist']]}, Tip={[round(x,1) for x in res['tip']]}, BucketBox={[round(x,1) for x in res['bucket_box']]}")
