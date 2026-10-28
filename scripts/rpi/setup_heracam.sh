#!/usr/bin/env bash
# ==============================================================================
# HERA AI-CCTV — Raspberry Pi Zero W / WH Dashcam Auto-Installer
# PT Caritas Energi Indonesia — Sarolangun Pit Operations
# ==============================================================================
set -e

echo "========================================================"
echo "  HERA CCTV — Setup Edge Camera Broadcast (RPi Zero W)  "
echo "========================================================"

# 1. Update paket sistem
echo "[1/5] Memperbarui paket sistem Raspberry Pi OS..."
sudo apt update -y
sudo apt install -y ustreamer v4l-utils curl net-tools

# 2. Pastikan user masuk ke grup video
echo "[2/5] Menambahkan hak akses user ke perangkat kamera..."
sudo usermod -aG video $USER

# 3. Salin script watchdog WiFi (mencegah koneksi putus di pit tambang)
echo "[3/5] Mengatur Wi-Fi Auto-Reconnect Watchdog..."
sudo mkdir -p /opt/heracam
sudo cp wifi-watchdog.sh /opt/heracam/wifi-watchdog.sh
sudo chmod +x /opt/heracam/wifi-watchdog.sh

# Pasang cron job watchdog setiap 2 menit
(crontab -l 2>/dev/null | grep -v "wifi-watchdog.sh"; echo "*/2 * * * * /opt/heracam/wifi-watchdog.sh >/dev/null 2>&1") | crontab -

# 4. Pasang Systemd Service (Auto-start saat excavator dinyalakan)
echo "[4/5] Mengonfigurasi systemd service 'heracam'..."
sudo cat << 'EOF' > /etc/systemd/system/heracam.service
[Unit]
Description=HERA CCTV Excavator Dashcam Streamer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
# Menggunakan resolusi 1280x720 20 FPS dengan buffer hemat RAM
ExecStart=/usr/bin/ustreamer --device=/dev/video0 --resolution=1280x720 --desired-fps=20 --host=0.0.0.0 --port=8080 --drop-same-frames=30 --quality=80
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable heracam.service
sudo systemctl restart heracam.service

# 5. Informasi hasil instalasi
IP_ADDR=$(hostname -I | awk '{print $1}')
echo ""
echo "========================================================"
echo "  INSTALASI SELESAI & BERHASIL!                         "
echo "========================================================"
echo "Status Service   : $(systemctl is-active heracam.service)"
echo "IP Raspberry Pi  : $IP_ADDR"
echo "Stream URL       : http://$IP_ADDR:8080/stream"
echo "Hostname URL     : http://$(hostname).local:8080/stream"
echo "Snapshot URL     : http://$IP_ADDR:8080/snapshot"
echo "========================================================"
echo "Langkah selanjutnya di Dashboard HERA Laptop:"
echo "1. Buka Master Data > Kamera & Video"
echo "2. Masukkan URL: http://$IP_ADDR:8080/stream"
echo "========================================================"
