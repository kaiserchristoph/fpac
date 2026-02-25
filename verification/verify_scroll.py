from playwright.sync_api import sync_playwright

def verify_scroll(page):
    # 1. Login
    page.goto("http://localhost:5000/login")
    page.fill('input[name="username"]', 'verifyuser')
    page.fill('input[name="password"]', 'verifypass')
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    # 2. Go to upload
    page.goto("http://localhost:5000/upload")

    # 3. Check for scroll options
    scroll_dir_visible = page.is_visible('#scroll_direction')
    scroll_speed_visible = page.is_visible('#scroll_speed')

    print(f"Scroll direction visible: {scroll_dir_visible}")
    print(f"Scroll speed visible: {scroll_speed_visible}")

    page.screenshot(path="verification/upload_page_scroll.png")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    try:
        verify_scroll(page)
    finally:
        browser.close()
