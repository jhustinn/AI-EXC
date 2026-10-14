from pathlib import Path
LBL = Path("datasets/excavator/labels")
LABEL = {}
def isi(stem, **k):
    LABEL.setdefault(stem, {}).update(k)

isi("v1_2026-10-10_at_10_00040", bucket=[(40,40,63,63)], arm=[(46,0,78,42)])
isi("v1_2026-10-10_at_10_00420", bucket=[(62,45,92,69)], arm=[(55,0,88,47)])
isi("v1_2026-10-10_at_10_00780", bucket=[(55,27,83,53)], arm=[(48,0,80,30)])
isi("v1_2026-10-10_at_10_01240", bucket=[(62,27,93,53)], arm=[(55,0,85,30)])
isi("v1_2026-10-10_at_10_01640", bucket=[(50,34,76,56)], arm=[(45,0,72,37)])
isi("v1_2026-10-10_at_10_00600", bucket=[(69,37,96,59)], arm=[(58,0,88,40)])



# BATCH 2 - lembar baru_02, 6 frame POV kabin
isi("v1_2026-10-10_at_10_00260", bucket=[(38,48,60,68)], arm=[(45,0,80,50)])
isi("v1_2026-10-10_at_10_00620", bucket=[(68,48,90,68)], arm=[(60,0,90,50)])
isi("v1_2026-10-10_at_10_01040", bucket=[(33,40,58,62)], arm=[(40,0,75,42)])
isi("v1_2026-10-10_at_10_01460", bucket=[(55,32,78,52)], arm=[(48,0,80,34)])
isi("v1_2026-10-10_at_10_00100", bucket=[(40,55,62,75)], arm=[(46,0,80,57)])
isi("v1_2026-10-10_at_10_01300", bucket=[(70,42,92,60)], arm=[(62,0,92,44)])



# BATCH 3 - lembar baru_03, campuran 4 video
isi("v1_2026-10-10_at_10_00660", bucket=[(55,34,86,57)], arm=[(52,0,82,40)])
isi("v2_2026-10-10_at_10_00560", bucket=[(70,45,100,73)], arm=[(60,0,100,48)])
isi("v3_2026-10-10_at_10_00620", bucket=[(36,26,68,50)], arm=[(0,0,72,35)])
isi("v4_2026-10-10_at_10_00480", boom=[(0,38,36,68)], arm=[(0,0,30,45)])
isi("v1_2026-10-10_at_10_00720", bucket=[(55,33,90,57)], arm=[(52,0,86,40)])
isi("v2_2026-10-10_at_10_00640", bucket=[(60,46,94,72)], arm=[(66,0,100,50)])

CID = {"bucket":0,"truck":1,"excavator":2,"arm":3,"boom":4}
nf = 0; hitung = {}
for stem, kelas in LABEL.items():
    lbl = None
    for sp in ("train","val"):
        p = LBL / sp / f"{stem}.txt"
        if p.exists():
            lbl = p; break
    if lbl is None:
        print("  lewati", stem); continue
    baris = [x for x in lbl.read_text(encoding="utf-8").splitlines()
             if x.strip() and int(x.split()[0]) == 1]
    for nama, kotak in kelas.items():
        for x1,y1,x2,y2 in kotak:
            cx,cy = (x1+x2)/200.0, (y1+y2)/200.0
            bw,bh = (x2-x1)/100.0, (y2-y1)/100.0
            if bw<=0 or bh<=0: continue
            baris.append(f"{CID[nama]} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            hitung[nama] = hitung.get(nama,0)+1
    lbl.write_text("\n".join(baris)+"\n", encoding="utf-8")
    nf += 1
print("frame ditulis :", nf)
for k,v in sorted(hitung.items()):
    print(f"  {k:10s} {v:4d} kotak")
