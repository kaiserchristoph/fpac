import network
import time
import urequests as requests
import machine
import neopixel
import config

# Initialize Neopixel
np = neopixel.NeoPixel(machine.Pin(config.MATRIX_PIN), config.MATRIX_WIDTH * config.MATRIX_HEIGHT)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
            print('.', end='')
        print()
    print('Network config:', wlan.ifconfig())

def get_zigzag_index(x, y):
    """
    Calculate the index for a zigzag wired WS2812B matrix.
    Even rows go left to right (0 to width-1).
    Odd rows go right to left (width-1 to 0).
    """
    if y % 2 == 0:
        return (y * config.MATRIX_WIDTH) + x
    else:
        return (y * config.MATRIX_WIDTH) + (config.MATRIX_WIDTH - 1 - x)

def display_image(image_data):
    """
    Display RGB pixels on the neopixel matrix.
    The image_data is expected to have 'pixels', a flat list of [r, g, b] lists.
    """
    pixels = image_data.get('pixels', [])
    img_width = image_data.get('width', config.MATRIX_WIDTH)
    img_height = image_data.get('height', config.MATRIX_HEIGHT)

    # We only render pixels that fit in our matrix
    for y in range(min(img_height, config.MATRIX_HEIGHT)):
        for x in range(min(img_width, config.MATRIX_WIDTH)):
            # The backend pixels list is row-major (top-left to bottom-right)
            pixel_index = (y * img_width) + x
            if pixel_index < len(pixels):
                r, g, b = pixels[pixel_index]

                # WS2812B is usually GRB, but the Neopixel library takes (r, g, b)
                # Ensure the color fits into the zigzag mapped index
                matrix_index = get_zigzag_index(x, y)
                if matrix_index < len(np):
                    np[matrix_index] = (r, g, b)

    np.write()

def fetch_image_list():
    """
    Fetch the list of available images from the backend.
    """
    url = f"{config.BACKEND_URL}/api/images"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            images = data.get('images', [])
            response.close()
            return images
        else:
            print(f"Failed to fetch image list: HTTP {response.status_code}")
            response.close()
            return []
    except Exception as e:
        print(f"Error fetching image list: {e}")
        return []

def fetch_image_rgb(image_id):
    """
    Fetch the RGB pixel data for a specific image.
    """
    url = f"{config.BACKEND_URL}/api/image/{image_id}/rgb"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            response.close()
            return data
        else:
            print(f"Failed to fetch image data for id {image_id}: HTTP {response.status_code}")
            response.close()
            return None
    except Exception as e:
        print(f"Error fetching image data: {e}")
        return None

def clear_matrix():
    for i in range(len(np)):
        np[i] = (0, 0, 0)
    np.write()

def main():
    connect_wifi()

    last_poll_time = 0
    available_images = []
    current_image_index = 0

    while True:
        current_time = time.ticks_ms()

        # Check if it's time to poll the backend for a new image list
        if time.ticks_diff(current_time, last_poll_time) >= config.POLL_INTERVAL_MS or last_poll_time == 0:
            print("Polling backend for updated image list...")
            available_images = fetch_image_list()
            last_poll_time = current_time
            current_image_index = 0 # Reset index when new list arrives

        if not available_images:
            print("No images found or backend unreachable. Waiting...")
            clear_matrix()
            time.sleep(10)
            continue

        # Cycle through available images
        if current_image_index >= len(available_images):
            current_image_index = 0

        image_info = available_images[current_image_index]
        image_id = image_info.get('id')

        print(f"Displaying image ID {image_id}")
        image_data = fetch_image_rgb(image_id)

        if image_data:
            display_image(image_data)
        else:
            print(f"Could not load data for image ID {image_id}")

        current_image_index += 1

        # Wait for the cycle interval before moving to the next image
        time.sleep_ms(config.CYCLE_INTERVAL_MS)

if __name__ == '__main__':
    main()
