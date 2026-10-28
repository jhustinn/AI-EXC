import urllib.request
import time
import json

for i in range(15):
    try:
        res = urllib.request.urlopen("http://127.0.0.1:8010/api/status", timeout=5)
        d = json.loads(res.read().decode())
        tm = time.strftime("%H:%M:%S")
        fase = d.get("fase")
        label = d.get("fase_label")
        durasi = d.get("durasi_fase_detik")
        siklus = d.get("kpi", {}).get("jumlah_siklus", 0)
        t_conf = d.get("truck_confidence", 0.0)
        b_conf = d.get("bucket_confidence", 0.0)
        print(f"[{tm}] Fase: {fase} ({label}) | Durasi: {durasi}s | Siklus: {siklus} | Truck conf: {t_conf} | Bucket conf: {b_conf}")
    except Exception as e:
        print("Error:", e)
    time.sleep(2)
