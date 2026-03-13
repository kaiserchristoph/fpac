# ESP32 MicroPython WS2812B Display Client

This directory contains the MicroPython code to connect your ESP32 to the Flask Pixel Art Creator backend and display the pixel art on a WS2812B LED matrix. The code supports a zigzag matrix layout natively.

## Prerequisites
1. **ESP32** flashed with the latest MicroPython firmware (tested on v1.20+).
2. **WS2812B** matrix wired to your ESP32.
   - Default GPIO data pin is `4`. Ensure your ESP32 and Matrix share a common ground.
   - Provide adequate 5V power for your LED matrix.

## Setup Instructions

### 1. Configure the Client
Before uploading the code, open `config.py` and modify the fields to match your network and backend settings:
- **`WIFI_SSID`** and **`WIFI_PASSWORD`**: Your local Wi-Fi credentials.
- **`BACKEND_URL`**: The IP address of the machine running your Flask backend (e.g., `http://192.168.1.50:5000`). Make sure your ESP32 and backend server are on the same network!
- **`MATRIX_WIDTH`** and **`MATRIX_HEIGHT`**: Dimensions of your WS2812B matrix (default is 16x16).
- **`MATRIX_PIN`**: The ESP32 GPIO pin connected to the matrix data line.
- **`POLL_INTERVAL_MS`**: How often the ESP32 checks for new images (default 5 minutes).
- **`CYCLE_INTERVAL_MS`**: How long each image is displayed before moving to the next (default 10 seconds).

### 2. Upload to the ESP32
Use a tool like `mpremote`, `ampy`, or Thonny to upload the files to the root directory of your ESP32.

If using `mpremote`:
```bash
mpremote fs cp config.py :config.py
mpremote fs cp main.py :main.py
```

### 3. Run the Code
Once uploaded, reboot your ESP32. The `main.py` script will automatically execute on boot (or you can rename `main.py` to `boot.py` if needed). It will:
1. Connect to Wi-Fi.
2. Reach out to the backend URL to get a list of active images.
3. Download the RGB pixel data for each image.
4. Draw the images to the WS2812B matrix, correctly mapping the standard row-major format to the zigzag matrix layout.
5. Cycle through all available images and periodically repoll for new additions.