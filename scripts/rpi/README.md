# Panduan Pemasangan Raspberry Pi Zero W / WH sebagai Dashcam HERA AI-CCTV

Modul ini berisi paket skrip siap pakai untuk mengubah **Raspberry Pi Zero W / WH** menjadi kamera CCTV/dashcam kabin alat berat tambang (*Excavator Fleet*) yang terhubung ke server HERA.

---

## 🚀 Fitur Utama
1. **Ultra-Low Latency Streaming (~100-150 ms):** Menggunakan `ustreamer` berbasis C native dengan akselerasi perangkat keras V4L2.
2. **Auto-Boot Service:** Kamera langsung memancar dalam waktu ~25 detik begitu mesin unit / kontak alat berat dinyalakan.
3. **Wi-Fi Auto-Reconnect Watchdog:** Skrip otomatis mendeteksi jika koneksi terputus di dalam pit tambang dan me-reconnect tanpa perlu restart manual.
4. **Proteksi MicroSD Anti-Korup (OverlayFS):** Kartu memori aman 100% dari korupsi data meski mesin/saklar aki unit dimatikan mendadak.

---

## 🛠️ Langkah Instalasi di Raspberry Pi Zero W

1. **Masuk ke Raspberry Pi melalui SSH dari laptop:**
   ```bash
   ssh pi@heracam.local
   ```

2. **Jalankan Skrip Instalasi Otomatis (Satu Baris Perintah):**
   ```bash
   # Unduh atau clone repository ke Pi, lalu jalankan:
   cd ~
   git clone https://github.com/your-repo/AI-CCTV.git || true
   cd AI-CCTV/scripts/rpi
   chmod +x setup_heracam.sh wifi-watchdog.sh enable_readonly_sd.sh
   ./setup_heracam.sh
   ```

3. **Cek Hasil Siaran:**
   Buka browser di laptop Anda pada URL:
   - **`http://heracam.local:8080/stream`**
   - Atau menggunakan IP: `http://<IP_RASPBERRY_PI>:8080/stream`

4. *(Opsional - Sangat Disarankan untuk Tambang)* **Aktifkan Mode Anti-Korup MicroSD:**
   ```bash
   ./enable_readonly_sd.sh
   ```

---

## 📡 Menghubungkan ke Web Admin HERA
1. Buka Web Admin HERA di laptop: `http://127.0.0.1:8002/master/kamera`
2. Klik **Tambah Kamera Baru**
   - **Nama:** `Dashcam Kabin EXC-07 (RPi Zero)`
   - **Tipe:** `RTSP IP Camera` (atau HTTP Stream)
   - **Path / URL:** `http://heracam.local:8080/stream`
   - **Resolusi:** `1280x720`
   - **Target FPS:** `20`
3. Kamera RPi Zero sekarang resmi terhubung dan aktivitasnya dianalisis real-time oleh model AI YOLO11.
