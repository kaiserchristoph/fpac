# fpac - Flask Pixel Art Creator

A Flask-based web application designed for creating and managing pixel art, specifically optimized for driving WS2812 LED matrices via an ESP32 microcontroller.

## Features

- **Web-based Drawing Interface**: Create pixel art on a custom grid (default 64x16).
- **User Authentication**: Secure registration and login system.
- **Display Configuration**: Support for multiple display sizes via `displays.json`.
- **Image Management**:
  - Save drawings as BMP files.
  - Upload existing images (automatically converted to BMP).
  - Manage uploaded images.
- **ESP32 Integration**:
  - API endpoint optimized for microcontrollers (`/api/image/<id>/rgb`).
  - Returns pixel data in a simple JSON format.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fpac
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```
   The server will start on `http://0.0.0.0:5000` by default.

2. Open your web browser and navigate to `http://localhost:5000`.

3. Register a new account or log in if you already have one.

4. Use the "Draw" page to create pixel art or "Upload" to add existing images.

## Configuration

### Display Settings

Display configurations are stored in `displays.json`. You can modify this file to match your LED matrix setup.

Example `displays.json`:
```json
[
  {
    "name": "Standard 64x16",
    "width": 64,
    "height": 16,
    "max_width": 64,
    "max_height": 32
  }
]
```

## API Documentation

The application exposes several API endpoints for integration with external devices like ESP32.

### Get All Images
**Endpoint:** `GET /api/images`

Returns a list of all available images with metadata.

**Response Example:**
```json
{
  "images": [
    {
      "id": 1,
      "filename": "drawing_1_1623456789.bmp",
      "width": 64,
      "height": 16,
      "url": "http://localhost:5000/static/uploads/drawing_1_1623456789.bmp",
      "display_name": "Standard 64x16",
      "scroll_direction": "none",
      "scroll_speed": 0
    }
  ]
}
```

### Get Image RGB Data
**Endpoint:** `GET /api/image/<id>/rgb`

Returns the pixel data for a specific image in a format easy to process by microcontrollers.

**Response Example:**
```json
{
  "width": 64,
  "height": 16,
  "pixels": [
    [255, 0, 0], [0, 255, 0], [0, 0, 255], ...
  ]
}
```
Each pixel is represented as an array of `[Red, Green, Blue]` values (0-255).

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
