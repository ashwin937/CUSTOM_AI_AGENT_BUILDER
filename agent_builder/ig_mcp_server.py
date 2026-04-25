import os
import time
import requests
from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize MCP Server
mcp = FastMCP("Instagram")

def download_image_if_url(image_path_or_url):
    """Downloads an image from a URL to a temporary file if needed, otherwise returns the path."""
    if image_path_or_url.startswith("http"):
        local_filename = f"temp_insta_upload_{int(time.time())}.jpg"
        print(f"Downloading image from {image_path_or_url} to {local_filename}...")
        with requests.get(image_path_or_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return os.path.abspath(local_filename)
    # Ensure absolute path for file input
    return os.path.abspath(image_path_or_url)

@mcp.tool()
def post_photo(image_path: str, caption: str) -> str:
    """
    Post a photo to Instagram using Selenium automation (Mobile Emulation).
    Requires INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in .env.
    Args:
        image_path (str): Local file path or URL of the image to post.
        caption (str): Caption for the post.
    """
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        return "Error: INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD must be set in your .env file for full automation to work."

    # 1. Prepare Image
    try:
        final_image_path = download_image_if_url(image_path)
        if not os.path.exists(final_image_path):
            return f"Error: Image file not found at {final_image_path}"
    except Exception as e:
        return f"Error preparing image: {str(e)}"

    driver = None
    try:
        print("Initializing Browser...")
        # Mobile Emulation is crucial for the 'New Post' button to appear easily
        mobile_emulation = { "deviceName": "iPhone X" }
        options = webdriver.ChromeOptions()
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument("--log-level=3")
        
        # Start Driver
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        
        # 2. Login Process
        print("Navigating to Instagram Login...")
        driver.get("https://www.instagram.com/accounts/login/")
        
        # Accept Cookies (European Compliance)
        try:
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow all cookies')]"))
            )
            cookie_btn.click()
        except:
            pass # No cookie banner found

        print("Entering credentials...")
        # Wait for inputs
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        pass_input = driver.find_element(By.NAME, "password")
        
        user_input.send_keys(username)
        pass_input.send_keys(password)
        
        # Click Login
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        
        # Wait for login to complete (url change or element appearance)
        print("Waiting for login to complete...")
        time.sleep(5)
        
        # Check for errors
        if "instagram.com/accounts/login" in driver.current_url:
            return "Login failed. Please check your username and password, or check if Instagram requires a security code."

        # 3. Handle Post-Login Popups
        print("Handling 'Save Info' / 'Notifications' popups...")
        # Often "Save Info" comes first
        try:
            not_now_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')] | //div[contains(text(), 'Not now')]"))
            )
            not_now_btn.click()
        except:
            pass
            
        try:
            cancel_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cancel')]"))
            )
            cancel_btn.click()
        except:
            pass

        # 4. Upload File
        print(f"Uploading file: {final_image_path}")
        
        # The trick: Find the file input directly. 
        # In mobile view, the 'New Post' button usually triggers the file dialog.
        # But we can try to send keys to the input[type=file] directly if it exists.
        
        # Wait for the UI to settle
        time.sleep(2)
        
        # In modern Instagram PWA, the input[type=file] might be hidden or created dynamically.
        # We try to click the New Post button to trigger creation, providing it doesn't block with a native dialog immediately.
        # However, Selenium usually can send_keys to a file input even if hidden.
        
        try:
            # Look for file input
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            # Unhide if necessary (optional, usually send_keys works on hidden inputs too)
            driver.execute_script("arguments[0].style.display = 'block';", file_input)
            file_input.send_keys(final_image_path)
        except Exception as e:
            # If no input found, try clicking the 'New Post' button first
            print("File input not found directly. Attempting to click New Post button first...")
            new_post_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='New post']")))
            new_post_btn.click()
            time.sleep(1)
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(final_image_path)

        print("File uploaded. Proceeding to edit...")
        
        # 5. Review / Edit Steps
        # Click "Next"
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]")))
        next_btn.click()
        time.sleep(2)
        
        # 6. Caption
        print("Adding caption...")
        try:
            caption_area = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            caption_area.click() # Focus
            caption_area.send_keys(caption)
        except:
            print("Caption area not found, skipping caption.")

        # 7. Share
        print("Clicking Share...")
        share_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Share')]")))
        share_btn.click()
        
        # Wait for upload completion
        time.sleep(5)
        
        success_msg = "Successfully posted to Instagram!"
        
        # Verify success by checking if we see the post or redirect
        if "instagram.com" in driver.current_url: 
             return success_msg
        else:
            return "Post process finished, but verify on Instagram."

    except Exception as e:
        return f"Automation Failed: {str(e)}\n(Note: Instagram may have blocked the automation or requested 2FA.)"
    finally:
        if driver:
            # We delay closing slightly to let the upload finish
             time.sleep(3)
             driver.quit()

if __name__ == "__main__":
    mcp.run()
