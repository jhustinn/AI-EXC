"""Cek /stream: baca sampai magic byte JPEG benar-benar muncul."""
from __future__ import annotations

import socket
import sys
import time

HOST, PORT = "127.0.0.1", 8010

with socket.create_connection((HOST, PORT), timeout=15) as s:
    s.sendall(b"GET /stream HTTP/1.1\r\nHost: 127.0.0.1:8010\r\n"
              b"Accept: */*\r\n\r\n")
    s.settimeout(20)

    buf = b""
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            chunk = s.recv(8192)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
        if b"\xff\xd8\xff" in buf:
            break

head, _, body = buf.partition(b"\r\n\r\n")
status = head.split(b"\r\n", 1)[0].decode("latin-1", "replace")
print("status  :", status)
print("bytes   :", len(buf))
print("boundary:", b"--frame" in head)

jumlah = body.count(b"\xff\xd8\xff")
print("gambar JPEG diterima:", jumlah)
if jumlah:
    i = body.index(b"\xff\xd8\xff")
    print(" magic di offset", i)
    sys.exit(0)
print(" TIDAK ada JPEG dalam 20 detik")
sys.exit(1)