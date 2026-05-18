import time
from playwright.sync_api import sync_playwright

def live_demo():
    print("Launching visible browser for Live Demo...")
    with sync_playwright() as p:
        # Launch browser in non-headless mode so user can see it
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Navigating to AI Agent Builder (http://127.0.0.1:7860)...")
        page.goto("http://127.0.0.1:7860")
        
        print("Finding chat input box...")
        # Wait for the Gradio text area to appear
        page.wait_for_selector("textarea[data-testid='textbox']")
        
        message = "Send an email to ashwinkbd3@gmail.com with subject Test Email and body This is a test email. Also post a LinkedIn post: Excited to test the AI Agent Builder live! by ashwin"
        
        print(f"Typing message: '{message}'")
        # Type slowly to simulate a human
        page.fill("textarea[data-testid='textbox']", "")
        page.type("textarea[data-testid='textbox']", message, delay=50)
        
        time.sleep(1)
        
        print("Clicking Send button...")
        # Click the Send button (it has text 'Send' and is a button)
        page.click("button:has-text('Send')")
        
        print("✅ Message sent! Watch the browser to see the AI generate the response.")
        
        # Keep the browser open for 60 seconds to let the user see the result
        time.sleep(60)
        browser.close()

if __name__ == "__main__":
    live_demo()
