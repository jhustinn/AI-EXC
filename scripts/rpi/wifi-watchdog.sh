#!/usr/bin/env bash
# ==============================================================================
# HERA CCTV — Wi-Fi Auto-Reconnect Watchdog untuk Kabin Excavator
# Memastikan koneksi Wi-Fi ke MiFi/Router unit selalu pulih otomatis
# ==============================================================================

# Ambil IP Gateway (Router / Hotspot HP / MiFi)
GATEWAY_IP=$(ip route | grep default | awk '{print $3}' | head -n 1)

if [ -z "$GATEWAY_IP" ]; then
    # Jika tidak ada gateway, restart interface wlan0
    echo "[$(date)] Tidak ada gateway ditemukan. Me-restart wlan0..."
    sudo ip link set wlan0 down
    sleep 2
    sudo ip link set wlan0 up
    exit 1
fi

# Coba ping gateway 2 kali
if ! ping -q -c 2 -W 3 "$GATEWAY_IP" > /dev/null 2>&1; then
    echo "[$(date)] Gateway $GATEWAY_IP tidak merespon ping. Mencoba re-connect Wi-Fi..."
    # Re-associate dengan WPA Supplicant tanpa reboot
    sudo wpa_cli -i wlan0 reassociate > /dev/null 2>&1
    sleep 5

    # Jika masih belum merespon, reset interface wlan0
    if ! ping -q -c 2 -W 3 "$GATEWAY_IP" > /dev/null 2>&1; then
        echo "[$(date)] Masih gagal terhubung. Me-reset interface jaringan..."
        sudo ip link set wlan0 down
        sleep 2
        sudo ip link set wlan0 up
    fi
fi
