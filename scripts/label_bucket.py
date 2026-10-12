"""Alat pelabeli bucket: kotak kasar -> SAM mengencangkan -> simpan YOLO.

Jalankan:
    .venv\\Scripts\\python.exe scripts\\label_bucket.py
Lalu buka http://127.0.0.1:8011

Alur di browser:
    drag di gambar  -> kotak kasar
    tekan S          -> SAM mengencangkan ke bucket
    tekan Enter      -> simpan & frame berikutnya
    tekan D          -> lewati tanpa label
    tekan Backspace  -> undo
"""
from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

PROJECT = Path(r"E:\App\AI-CCTV")
OUT = PROJECT / "datasets" / "excavator"
TMP = PROJECT / "data" / "label_tmp"
TMP.mkdir(parents=True, exist_ok=True)

KELAS = {"bucket": 0, "truck": 1}

_lock = threading.Lock()
_state: dict = {"items": [], "idx": 0, "sam": None}


def sam_model():
    """Muat SAM sekali, dipakai bersama antar request."""
    if _state["sam"] is None:
        from ultralytics import SAM
        _state["sam"] = SAM("sam2.1_b.pt")
    return _state["sam"]


def daftar_file() -> list[dict]:
    """Semua frame + label truck yang sudah ada, untuk dianotasi bucket."""
    hasil: list[dict] = []
    for split in ("train", "val"):
        for img in sorted((OUT / "images" / split).glob("*.jpg")):
            lbl = OUT / "labels" / split / f"{img.stem}.txt"
            truck = []
            if lbl.exists():
                for line in lbl.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    cid, cx, cy, bw, bh = line.split()
                    if int(cid) == 1:
                        truck.append([float(v) for v in (cx, cy, bw, bh)])
            hasil.append({
                "id": f"{split}/{img.stem}",
                "split": split,
                "file": img.name,
                "truck": truck,
                "path": str(img),
            })
    return hasil


HTML = """<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<title>Pelabeli Bucket</title>
<style>
 body{margin:0;font-family:"Segoe UI",sans-serif;background:#0f172a;color:#e2e8f0;
      display:flex;flex-direction:column;height:100vh}
 header{padding:8px 14px;background:#1e293b;display:flex;gap:18px;align-items:center;
        font-size:13px;flex-wrap:wrap}
 b{color:#38bdf8}
 #wrap{flex:1;display:grid;place-items:center;overflow:hidden;position:relative}
 #img{max-width:100%;max-height:100%;cursor:crosshair}
 .box{position:absolute;border:3px solid #22c55e;pointer-events:none}
 .box.truck{border-color:#f59e0b}
 .box.truck::after{content:'truck';position:absolute;top:-20px;left:0;color:#f59e0b;
                   font-size:12px;font-weight:bold}
 .box.bucket::after{content:'bucket';position:absolute;top:-20px;left:0;
                     color:#22c55e;font-size:12px;font-weight:bold}
 footer{padding:8px 14px;background:#1e293b;font-size:12px;color:#94a3b8}
 kbd{background:#334155;padding:1px 6px;border-radius:4px;color:#e2e8f0}
 #msg{margin-left:auto;color:#f59e0b}
</style></head><body>
<header>
  <span>Frame <b id="pos">0</b> / <b id="tot">0</b></span>
  <span><kbd>drag</kbd> kotak kasar</span>
  <span><kbd>S</kbd> SAM kekencangkan</span>
  <span><kbd>Enter</kbd> simpan &amp; lanjut</span>
  <span><kbd>D</kbd> lewati</span>
  <span><kbd>U</kbd> undo</span>
  <span><kbd>Del</kbd> kosongkan</span>
  <span id="msg"></span>
</header>
<div id="wrap"><img id="img"><div id="layer"></div></div>
<footer>Kotak hijau digambar manusia, oranye = truck dari COCO. Tekan S agar SAM mengencangkan.</footer>
<script>
let items=[], idx=0, bucket=null, drew=null, scale=1, ox=0, oy=0;

async function muat(){
  const s = await fetch('/api/state'); const d = await s.json();
  items = d.items; idx = d.idx;
  document.getElementById('tot').textContent = items.length;
  tampil();
}

function tampil(){
  if(idx>=items.length){
    document.getElementById('img').src='';
    document.getElementById('layer').innerHTML='';
    document.getElementById('msg').textContent='SELESAI - semua frame diproses';
    return;
  }
  const it = items[idx];
  bucket = null; drew = null;
  document.getElementById('pos').textContent = idx+1;
  document.getElementById('msg').textContent='';
  const im = document.getElementById('img');
  im.onload = ()=>{
    const r = im.getBoundingClientRect(), w = im.naturalWidth, h = im.naturalHeight;
    scale = r.width/w;
    const L = document.getElementById('layer');
    L.style.cssText = 'position:absolute;left:'+r.left+'px;top:'+r.top+
                      ';width:'+r.width+'px;height:'+r.height+'px';
    L.innerHTML='';
    it.truck.forEach(t=>kotak(t[0]-t[2]/2,t[1]-t[3]/2,t[0]+t[2]/2,t[1]+t[3]/2,'truck'));
  };
  im.src='/gambar?id='+encodeURIComponent(it.id)+'&split='+it.split;
}

function kotak(x1,y1,x2,y2,kelas){
  const d=document.createElement('div');
  d.className='box '+kelas;
  d.style.left=Math.min(x1,x2)*scale+'px';
  d.style.top=Math.min(y1,y2)*scale+'px';
  d.style.width=Math.abs(x2-x1)*scale+'px';
  d.style.height=Math.abs(y2-y1)*scale+'px';
  document.getElementById('layer').appendChild(d);
}

document.getElementById('img').addEventListener('mousedown',e=>{
  const r=e.target.getBoundingClientRect();
  drew={x1:(e.clientX-r.left)/scale, y1:(e.clientY-r.top)/scale, x2:0, y2:0};
  drew.el = kotak(drew.x1,drew.y1,drew.x1,drew.y1,'bucket');
});
document.addEventListener('mousemove',e=>{
  if(!drew) return;
  const r=document.getElementById('img').getBoundingClientRect();
  drew.x2=(e.clientX-r.left)/scale; drew.y2=(e.clientY-r.top)/scale;
  drew.el.style.left=Math.min(drew.x1,drew.x2)*scale+'px';
  drew.el.style.top=Math.min(drew.y1,drew.y2)*scale+'px';
  drew.el.style.width=Math.abs(drew.x2-drew.x1)*scale+'px';
  drew.el.style.height=Math.abs(drew.y2-drew.y1)*scale+'px';
});
document.addEventListener('mouseup',()=>{
  if(!drew) return;
  if(Math.abs(drew.x2-drew.x1)*scale>8 && Math.abs(drew.y2-drew.y1)*scale>8)
    bucket=[drew.x1,drew.y1,drew.x2,drew.y2];
  drew=null;
});

document.addEventListener('keydown',async e=>{
  if(e.key==='s'||e.key==='S'){
    if(!bucket){document.getElementById('msg').textContent='belum ada kotak';return;}
    document.getElementById('msg').textContent='SAM berjalan...';
    const r=await fetch('/api/snap',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id:items[idx].id,split:items[idx].split,box:bucket})});
    const d=await r.json();
    if(d.error){document.getElementById('msg').textContent='SAM gagal: '+d.error;return;}
    document.querySelectorAll('.box.bucket').forEach(e=>e.remove());
    bucket=d.box;
    kotak(bucket[0],bucket[1],bucket[2],bucket[3],'bucket');
    document.getElementById('msg').textContent='SAM ok';
  }
  else if(e.key==='Enter'){ simpan(bucket); }
  else if(e.key==='d'||e.key==='D'){ simpan(null); }
  else if(e.key==='Delete'){
    document.querySelectorAll('.box.bucket').forEach(e=>e.remove());
    bucket=null; document.getElementById('msg').textContent='dikosongkan';
  }
  else if(e.key==='u'||e.key==='U'){ tampil(); }
});

async function simpan(b){
  if(idx>=items.length) return;
  const it=items[idx];
  await fetch('/api/simpan',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:it.id,split:it.split,box:b})});
  idx++; tampil();
}

window.onload=muat;
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # bisukan
        pass

    def _kirim(self, kode, tipe, isi: bytes):
        self.send_response(kode)
        self.send_header("Content-Type", tipe)
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        self.wfile.write(isi)

    def do_GET(self):
        ruta = urlparse(self.path).path
        if ruta in ("/", "/index.html"):
            self._kirim(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
        elif ruta == "/api/state":
            if not _state["items"]:
                _state["items"] = daftar_file()
                _state["idx"] = 0
            body = json.dumps({"items": _state["items"],
                               "idx": _state["idx"]}).encode("utf-8")
            self._kirim(200, "application/json", body)
        elif ruta == "/gambar":
            import urllib.parse as up
            q = up.parse_qs(urlparse(self.path).query)
            item = next((i for i in _state["items"] if i["id"] == q.get("id", [""])[0]), None)
            if not item:
                self._kirim(404, "text/plain", b"tidak ditemukan")
                return
            data = Path(item["path"]).read_bytes()
            self._kirim(200, "image/jpeg", data)
        else:
            self._kirim(404, "text/plain", b"tidak ditemukan")

    def do_POST(self):
        import urllib.parse as up
        from urllib.request import Request as UReq, urlopen
        panjang = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(panjang) or b"{}")
        q = up.parse_qs(urlparse(self.path).query)
        item = next((i for i in _state["items"] if i["id"] == payload.get("id")), None)

        if self.path.startswith("/api/snap"):
            if item is None:
                self._kirim(200, "application/json", json.dumps({"error": "frame hilang"}).encode())
                return
            try:
                import cv2
                import numpy as np
                img = cv2.imread(item["path"])
                h, w = img.shape[:2]
                x1, y1, x2, y2 = [float(v) for v in payload["box"]]
                with _lock:
                    model = sam_model()
                    res = model.predict(img, bboxes=[[x1, y1, x2, y2]], verbose=False)[0]
                if res.boxes is None or len(res.boxes) == 0:
                    self._kirim(200, "application/json",
                                json.dumps({"error": "tidak ada mask"}).encode())
                    return
                b = [float(v) for v in res.boxes.xyxy.cpu().numpy()[0]]
                b[0] = max(0.0, min(b[0], w)); b[1] = max(0.0, min(b[1], h))
                b[2] = max(0.0, min(b[2], w)); b[3] = max(0.0, min(b[3], h))
                self._kirim(200, "application/json", json.dumps({"box": b}).encode())
            except Exception as exc:  # noqa: BLE001
                self._kirim(200, "application/json",
                            json.dumps({"error": f"{type(exc).__name__}: {exc}"}).encode())

        elif self.path.startswith("/api/simpan"):
            if item is None:
                self._kirim(200, "application/json", b'{"ok":false}')
                return
            lbl = OUT / "labels" / item["split"] / f"{Path(item['id']).name}.txt"
            baris = []
            for t in item["truck"]:
                baris.append(f"1 {t[0]:.6f} {t[1]:.6f} {t[2]:.6f} {t[3]:.6f}")
            box = payload.get("box")
            if box:
                import cv2
                img = cv2.imread(item["path"])
                h, w = img.shape[:2]
                x1, y1, x2, y2 = [float(v) for v in box]
                cx, cy = ((x1 + x2) / 2) / w, ((y1 + y2) / 2) / h
                bw, bh = (x2 - x1) / w, (y2 - y1) / h
                baris.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            lbl.parent.mkdir(parents=True, exist_ok=True)
            lbl.write_text("\n".join(baris) + ("\n" if baris else ""), encoding="utf-8")
            self._kirim(200, "application/json", b'{"ok":true}')


def main():
    srv = HTTPServer(("127.0.0.1", 8011), Handler)
    n = len(daftar_file())
    print(f"alat pelabeli siap - {n} frame menunggu")
    print("buka http://127.0.0.1:8011")
    webbrowser.open("http://127.0.0.1:8011")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()