# esp32/config.py

# Wi-Fi Credentials
WIFI_SSID = "your_wifi_ssid_here"
WIFI_PASSWORD = "your_wifi_password_here"

# Backend Server Configuration
# Provide the URL without a trailing slash, e.g., "http://192.168.1.100:5000"
BACKEND_URL = "http://your_backend_ip:5000"

# Matrix Display Configuration
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 16
MATRIX_PIN = 4 # GPIO pin connected to the WS2812B data line

# Polling and Display Behavior
# How often to check the backend for an updated list of images (in milliseconds)
POLL_INTERVAL_MS = 300000 # 5 minutes

# How long to display each image before moving to the next one (in milliseconds)
CYCLE_INTERVAL_MS = 10000 # 10 seconds
