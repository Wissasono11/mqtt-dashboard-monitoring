# mqtt_sensor

Panduan Setup & Penggunaan Virtual Environment untuk ESP (MicroPython)
Persyaratan Awal

## Pastikan sudah terinstal di komputer kamu:
- Python 3.8+
- pip (Python package manager)
- VS Code / Terminal / PowerShell
- Board ESP8266 atau ESP32
- Kabel USB data (bukan hanya kabel charger)

## 1. Membuat dan Mengaktifkan Virtual Environment
Buka folder proyek kamu di terminal, contoh:
```
cd D:\MQTT
```

Buat virtual environment:
```
python -m venv venv
```

Aktifkan environment:
```
.\venv\Scripts\Activate.ps1
```

Jika berhasil, prompt akan berubah menjadi:
```
(venv) PS D:\MQTT>
```

Jika muncul error “running scripts is disabled…”, jalankan PowerShell sebagai Administrator, lalu ketik:
```
Set-ExecutionPolicy Unrestricted
```
Setelah itu aktifkan ulang venv.

## 2. Instalasi Modul yang Dibutuhkan
Setelah environment aktif, install modul berikut:
```
pip install esptool adafruit-ampy
```
Install modul lain jika dibutuhkan dengan perintah yang serupa

## 3. Flash Firmware MicroPython ke Board
## Lewati bagian ini jika program esp yang akan di run sama
Hubungkan board ke komputer via kabel USB.

Periksa port COM dengan:
```
mode
```
atau di Device Manager → Ports (COM & LPT).
Misal: COM3.

Hapus flash lama:
```
python -m esptool --port COM3 erase_flash
```

Unduh firmware MicroPython sesuai board:
[ESP8266] (https://micropython.org/download/ESP8266/)
[ESP32] (https://micropython.org/download/ESP32/)

Misal file: esp32-20241101-v1.23.0.bin
Flash firmware:
```
python -m esptool --port COM3 --baud 460800 write_flash --flash_size=detect 0 esp8266-20241101-v1.23.0.bin
```
Setelah selesai, board siap digunakan dengan MicroPython.

## 4. Upload File Python ke Board
Misal kamu punya file:
- main.py
- wifi_config.py
- mqtt_publisher.py

Cek terlebih dahulu apakah file yang dibutuhkan sudah ada:
```
ampy --port COM3 ls
```

Upload satu per satu dengan ampy:
```
ampy --port COM3 --baud 115200 put main.py
ampy --port COM3 --baud 115200 put wifi_config.py
ampy --port COM3 --baud 115200 put mqtt_publisher.py
```

Hapus file jika perlu:
```
ampy --port COM3 rm main.py
```

Baca isi file dari board:
```
ampy --port COM3 get main.py
```

## 5. Jalankan Program
Begitu file main.py sudah ada di board, setiap kali ESP di-reset atau diberi daya, program akan otomatis berjalan.
Untuk melihat output log, gunakan serial monitor seperti:
- PuTTY
- TeraTerm
- Thonny
atau langsung:
```
ampy --port COM3 --baud 115200 run main.py
```
