import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def live_demo():
    print("Launching Chrome for Live Demo...")
    try:
        options = uc.ChromeOptions()
        # Keep browser open after script finishes
        options.add_experimental_option("detach", True)
        driver = uc.Chrome(options=options)
        
        print("Navigating to AI Agent Builder (http://127.0.0.1:7860)")
        driver.get("http://127.0.0.1:7860")
        
        # Wait for Gradio interface to load
        time.sleep(5)
        
        print("Finding chat input box...")
        # Gradio textboxes are usually textareas
        wait = WebDriverWait(driver, 15)
        textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[data-testid='textbox']")))
        
        if not textarea:
             textarea = driver.find_element(By.TAG_NAME, "textarea")
             
        message = "Send an email to ashwinkbd3@gmail.com with subject Test Email and body This is a test email. Also post a LinkedIn post: Excited to test the AI Agent Builder live!"
        
        print(f"Typing message: '{message}'")
        # Simulate typing like a human
        for char in message:
            textarea.send_keys(char)
            time.sleep(0.02)
            
        time.sleep(1)
        
        print("Clicking Send button...")
        # Find the send button
        try:
             # Gradio usually has a button with text 'Send' or a specific class
             send_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
             send_btn.click()
        except:
             # Fallback to pressing Enter
             from selenium.webdriver.common.keys import Keys
             textarea.send_keys(Keys.ENTER)
             
        print("✅ Message sent! Watch the browser to see the AI generate the response and trigger the automations in the background.")
        
    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    live_demo()
