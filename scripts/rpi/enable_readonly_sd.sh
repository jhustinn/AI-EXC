#!/usr/bin/env bash
# ==============================================================================
# HERA CCTV — Proteksi MicroSD Anti-Korup (Read-Only Root OverlayFS)
# Sangat krusial untuk alat berat tambang yang sering dimatikan via saklar aki
# ==============================================================================
set -e

echo "Mengaktifkan OverlayFS (Read-Only Filesystem) di Raspberry Pi OS..."
echo "Setelah ini, MicroSD aman dari kerusakan data walau listrik dimatikan mendadak."

sudo raspi-config nonint enable_overlayfs
sudo raspi-config nonint enable_bootro

echo "OverlayFS berhasil diaktifkan. Raspberry Pi perlu di-reboot."
read -p "Apakah Anda ingin reboot sekarang? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
