import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def find_m3u8_url(page_url):
    """
    Navigates to a webpage, inspects network traffic, and finds the .m3u8 playlist URL.

    Args:
        page_url (str): The URL of the page containing the video.

    Returns:
        str: The .m3u8 URL if found, otherwise None.
    """
    m3u8_url = None
    
    # --- Setup Selenium WebDriver ---
    print("Setting up the browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in the background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('log-level=3') # Suppress console logs

    # Automatically download and manage chromedriver
    service = Service(ChromeDriverManager().install())
    
    # Use selenium-wire's webdriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # --- Navigate and Find the URL ---
        print(f"Navigating to {page_url}...")
        driver.get(page_url)

        # Wait for the browser to make network requests.
        # We can use a more advanced wait, but a simple sleep is often enough
        # for the video player to initialize.
        print("Waiting for network requests (10 seconds)...")
        time.sleep(10)

        print("Searching for .m3u8 file in network requests...")
        # Inspect requests made by the browser
        for request in driver.requests:
            if request.url.endswith('video.m3u8'):
                print("Found .m3u8 URL!")
                m3u8_url = request.url
                break # Exit the loop once we've found our URL

    finally:
        # --- Cleanup ---
        print("Closing the browser.")
        driver.quit()
        
    return m3u8_url

if __name__ == "__main__":
    # The URL provided in your request
    target_url = "https://www.tele-task.de/lecture/video/11420/"
    
    found_url = find_m3u8_url(target_url)
    
    if found_url:
        print("\n--- Success! ---")
        print(f"The captured .m3u8 playlist URL is:")
        print(found_url)
    else:
        print("\n--- Failed ---")
        print("Could not find an .m3u8 URL. The website might have changed,")
        print("or the wait time needs to be increased.")
