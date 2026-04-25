"""
Third-party service integrations (LinkedIn, Gmail, GitHub, WhatsApp, Google Meet, Instagram)
"""

import os
import json
import webbrowser
import subprocess
import time
from typing import Optional, Dict
import requests
from urllib.parse import urlencode

# Selenium imports for Instagram Automation
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import undetected_chromedriver as uc
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False


class OAuthConfig:
    """OAuth configuration for third-party services."""
    
    SERVICES = {
        "linkedin": {
            "client_id": os.getenv("LINKEDIN_CLIENT_ID", ""),
            "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET", ""),
            "redirect_uri": "http://localhost:8000/oauth/linkedin/callback",
            "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
            "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
            "scopes": ["r_liteprofile", "w_member_social"]
        },
        "gmail": {
            "client_id": os.getenv("GMAIL_CLIENT_ID", ""),
            "client_secret": os.getenv("GMAIL_CLIENT_SECRET", ""),
            "redirect_uri": "http://localhost:8000/oauth/gmail/callback",
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": ["https://www.googleapis.com/auth/gmail.send"]
        },
        "github": {
            "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
            "redirect_uri": "http://localhost:8000/oauth/github/callback",
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "scopes": ["repo", "user:email"]
        },
    }


class LinkedInIntegration:
    """LinkedIn API integration for sharing posts."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        } if access_token else {}

    def get_profile(self) -> Dict:
        """Get authenticated user's profile to extract the URN."""
        if not self.access_token:
            return {"error": "Not authenticated"}
            
        try:
            # 1. Try modern OIDC endpoint first (preferred for new apps)
            endpoint_oidc = "https://api.linkedin.com/v2/userinfo"
            response_oidc = requests.get(endpoint_oidc, headers=self.headers)
            
            if response_oidc.status_code == 200:
                profile_data = response_oidc.json()
                self.person_urn = f"urn:li:person:{profile_data.get('sub')}"
                return profile_data

            # 2. Fallback to legacy /me endpoint
            endpoint = f"{self.base_url}/me"
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                profile_data = response.json()
                self.person_urn = f"urn:li:person:{profile_data.get('id')}"
                return profile_data

            return {"error": f"Failed to fetch profile. Response: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    def share_post(self, content: str, media_url: Optional[str] = None) -> Dict:
        """Share a post on LinkedIn."""
        if not self.access_token:
            return {"error": "Not authenticated with LinkedIn"}

        try:
            if not getattr(self, 'person_urn', None):
                profile_res = self.get_profile()
                if isinstance(profile_res, dict) and "error" in profile_res:
                    return {"error": f"Could not fetch LinkedIn profile ID: {profile_res['error']}"}

            endpoint = f"{self.base_url}/ugcPosts"
            
            share_content = {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE"
            }
            
            if media_url:
                share_content["shareMediaCategory"] = "ARTICLE"
                share_content["media"] = [{"status": "READY", "originalUrl": media_url}]
            
            payload = {
                "author": self.person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            
            response = requests.post(endpoint, json=payload, headers=self.headers)
            
            if response.status_code in [200, 201]:
                post_id = response.json().get("id", "")
                post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else "Check your profile"
                return {"success": True, "message": "Post shared successfully", "url": post_url}
            else:
                return {"error": f"Failed to share post: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}


class GmailIntegration:
    """Gmail API integration for sending emails."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = "https://gmail.googleapis.com/gmail/v1/users/me"
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> Dict:
        """Send an email via Gmail."""
        if not self.access_token:
            return {"error": "Not authenticated with Gmail"}
        
        try:
            import base64
            from email.mime.text import MIMEText
            
            message = MIMEText(body, "html" if html else "plain")
            message["to"] = to
            message["subject"] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
            payload = {"raw": raw_message}
            
            response = requests.post(f"{self.base_url}/messages/send", json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                return {"success": True, "message": "Email sent successfully"}
            else:
                return {"error": f"Failed to send email: {response.text}"}
        
        except Exception as e:
            return {"error": str(e)}
    
    def open_and_paste(self, to: str, subject: str, body: str) -> Dict:
        try:
            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={urlencode({'su': subject})}&body={urlencode({'body': body})}"
            webbrowser.open(gmail_url)
            return {"success": True, "message": "Gmail opened.", "instruction": "Review and send."}
        except Exception as e:
            return {"error": str(e)}


class GitHubIntegration:
    """GitHub API integration."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.username = self._get_username() if access_token else None

    def _get_username(self) -> Optional[str]:
        try:
            headers = {"Authorization": f"token {self.access_token}"}
            resp = requests.get(f"{self.base_url}/user", headers=headers)
            if resp.status_code == 200:
                return resp.json().get("login")
            return None
        except:
            return None

    def create_repo(self, name: str, description: str = "", private: bool = True) -> Dict:
        if not self.access_token:
            return {"error": "Not authenticated with GitHub"}
        try:
            headers = {"Authorization": f"token {self.access_token}", "Content-Type": "application/json"}
            payload = {"name": name, "description": description, "private": private, "auto_init": True}
            response = requests.post(f"{self.base_url}/user/repos", json=payload, headers=headers)
            if response.status_code in [200, 201]:
                return {"success": True, "repo": response.json()}
            else:
                return {"error": f"Failed to create repo: {response.text}"}
        except Exception as e:
            return {"error": str(e)}

    def upload_file(self, repo_name: str, file_path: str, content: str, message: str) -> Dict:
        if not self.access_token or not self.username:
            return {"error": "Authentication or username missing"}
        try:
            import base64
            url = f"{self.base_url}/repos/{self.username}/{repo_name}/contents/{file_path}"
            headers = {"Authorization": f"token {self.access_token}", "Content-Type": "application/json"}
            
            sha = None
            existing = requests.get(url, headers=headers)
            if existing.status_code == 200:
                sha = existing.json().get("sha")

            content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            payload = {"message": message, "content": content_b64}
            if sha: payload["sha"] = sha

            response = requests.put(url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                return {"success": True, "file": response.json()}
            else:
                return {"error": f"Failed to upload {file_path}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}

    def create_issue(self, owner: str, repo: str, title: str, body: str, labels: list = None) -> Dict:
        if not self.access_token: return {"error": "Not authenticated"}
        try:
            headers = {"Authorization": f"token {self.access_token}", "Content-Type": "application/json"}
            payload = {"title": title, "body": body, "labels": labels or []}
            response = requests.post(f"{self.base_url}/repos/{owner}/{repo}/issues", json=payload, headers=headers)
            if response.status_code in [200, 201]: return {"success": True, "issue": response.json()}
            else: return {"error": f"Failed to create issue: {response.text}"}
        except Exception as e: return {"error": str(e)}


class WhatsAppIntegration:
    """WhatsApp Business API integration."""
    def __init__(self, access_token: Optional[str] = None, phone_number_id: Optional[str] = None):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.instagram.com/v18.0/{phone_number_id}"
    
    def send_message(self, recipient_phone: str, message_text: str) -> Dict:
        if not self.access_token: return {"error": "Not authenticated"}
        try:
            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
            payload = {"messaging_product": "whatsapp", "to": recipient_phone, "type": "text", "text": {"body": message_text}}
            response = requests.post(f"{self.base_url}/messages", json=payload, headers=headers)
            if response.status_code in [200, 201]: return {"success": True, "message_id": response.json().get("messages", [{}])[0].get("id")}
            else: return {"error": f"Failed to send: {response.text}"}
        except Exception as e: return {"error": str(e)}


class GoogleMeetIntegration:
    """Google Meet integration."""
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
    
    def create_meeting(self, title: str, start_time: str, duration_minutes: int = 60) -> Dict:
        if not self.access_token: return {"error": "Not authenticated"}
        try:
            from datetime import datetime, timedelta
            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
            start = datetime.fromisoformat(start_time)
            end = start + timedelta(minutes=duration_minutes)
            payload = {
                "summary": title,
                "description": "Meeting created by AI Agent",
                "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
                "conferenceData": {"createRequest": {"requestId": f"meet-{int(time.time())}"}}
            }
            response = requests.post("https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1", json=payload, headers=headers)
            if response.status_code in [200, 201]:
                event = response.json()
                return {"success": True, "meet_link": event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri", ""), "event_id": event.get("id")}
            else: return {"error": f"Failed to create meeting: {response.text}"}
        except Exception as e: return {"error": str(e)}


class ServiceLauncher:
    """Launch external services and paste content."""
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except ImportError:
            try:
                import subprocess
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return True
            except: return False

    @staticmethod
    def open_and_launch(service: str, content: str, **kwargs) -> Dict:
        if service.lower() == "gmail":
            gmail = GmailIntegration(kwargs.get("access_token"))
            result = gmail.open_and_paste(to=kwargs.get("to", ""), subject=kwargs.get("subject", ""), body=content)
            ServiceLauncher.copy_to_clipboard(content)
            return result
        elif service.lower() == "linkedin":
            webbrowser.open("https://www.linkedin.com/feed/")
            ServiceLauncher.copy_to_clipboard(content)
            return {"success": True, "message": "LinkedIn opened."}
        elif service.lower() == "whatsapp":
            webbrowser.open("https://web.whatsapp.com/")
            ServiceLauncher.copy_to_clipboard(content)
            return {"success": True, "message": "WhatsApp Web opened."}
        elif service.lower() == "github":
            webbrowser.open("https://github.com/")
            ServiceLauncher.copy_to_clipboard(content)
            return {"success": True, "message": "GitHub opened."}
        elif service.lower() == "google meet":
            webbrowser.open("https://meet.google.com/")
            return {"success": True, "message": "Google Meet opened."}
        return {"error": f"Unknown service: {service}"}


class InstagramIntegration:
    """Instagram integration supporting both Graph API and Selenium Automation."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.base_url = "https://graph.facebook.com/v19.0"
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")

    def _download_image_if_url(self, image_path_or_url: str):
        if image_path_or_url.startswith("http"):
            try:
                local_filename = f"temp_insta_upload_{int(time.time())}.jpg"
                with requests.get(image_path_or_url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                return os.path.abspath(local_filename)
            except Exception as e:
                print(f"Failed to download image: {e}")
                return image_path_or_url
        return os.path.abspath(image_path_or_url)

    def post_photo_selenium(self, image_path: str, caption: str) -> Dict:
        """Automated posting using Selenium (Mobile Emulation)."""
        print("DEBUG: Starting Selenium...")
        if not HAS_SELENIUM:
            return {"error": "Selenium not installed."}
        if not self.username or not self.password:
             return {"error": "Missing INSTAGRAM_USERNAME or INSTAGRAM_PASSWORD in .env"}

        driver = None
        try:
            final_image_path = self._download_image_if_url(image_path)
            if not os.path.exists(final_image_path):
                 return {"error": f"Image not found: {final_image_path}"}

            print("DEBUG: Image checked. Initializing undetected-chromedriver...")
            
            # undetected-chromedriver has built-in anti-detection. Use subprocess=True (default)
            # which properly manages the Chrome binary on Windows
            try:
                print("DEBUG: Attempting standard uc.Chrome initialization...")
                driver = uc.Chrome()
            except Exception as e:
                print(f"DEBUG: Standard init failed: {e}. Trying with no_sandbox...")
                try:
                    import undetected_chromedriver
                    driver = undetected_chromedriver.Chrome(use_subprocess=True)
                except Exception as e2:
                    print(f"DEBUG: Subprocess attempt failed: {e2}. Trying version detection...")
                    driver = uc.Chrome(version_main=None)
            
            # undetected-chromedriver already masks automation
            wait = WebDriverWait(driver, 20)
            
            # Login
            print("DEBUG: Navigating to login...")
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3) # Explicit wait for load
            
            print(f"DEBUG: Page loaded: {driver.title}")

            # Handle Cookies
            try:
                print("DEBUG: Checking for cookies...")
                cookie_xpath = "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]"
                cookie_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, cookie_xpath)))
                cookie_btn.click()
                print("DEBUG: Cookies accepted.")
            except: 
                print("DEBUG: No cookies popup found.")
            
            print("DEBUG: Entering credentials...")
            user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            pass_input = driver.find_element(By.NAME, "password")
            user_input.send_keys(self.username)
            pass_input.send_keys(self.password)
            time.sleep(1) # Wait for UI to update

            # Try submitting via Enter key first (most reliable)
            from selenium.webdriver.common.keys import Keys
            print("DEBUG: Attempting Enter key on password field...")
            pass_input.send_keys(Keys.ENTER)
            time.sleep(3)

            # Check if we are still on login page
            if "login" not in driver.current_url:
                print("DEBUG: Enter key worked, navigated away from login.")
                clicked = True
            else:
                print("DEBUG: Clicking login button as fallback...")
                # Stronger login button finding
                login_strategies = [
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.XPATH, "//button[contains(text(), 'Log in')]"),
                    (By.XPATH, "//div[contains(text(), 'Log in')]"),
                    (By.XPATH, "//form//button")
                ]
                
                clicked = False
                for strategy in login_strategies:
                    try:
                        btn = driver.find_element(*strategy)
                        btn.click()
                        clicked = True
                        print(f"DEBUG: Clicked login using {strategy}")
                        break
                    except:
                        continue
            
            if not clicked and "login" in driver.current_url:
                 # SAVE COMPREHENSIVE DEBUG INFO
                 with open("debug_insta_source.html", "w", encoding="utf-8") as f:
                     f.write(driver.page_source)
                 screenshot_path = os.path.abspath("debug_insta_screenshot.png")
                 driver.save_screenshot(screenshot_path)
                 print(f"DEBUG: Saved source to debug_insta_source.html and screenshot to {screenshot_path}")
                 return {"error": "Could not find login button. Debug files saved."}

            time.sleep(8)
            
            if "login" in driver.current_url:
                 return {"error": "Login failed (check credentials or 2FA)"}

            # Handle Popups
            try:
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')] | //div[text()='Not now']"))).click()
            except: pass
            try:
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cancel')]"))).click()
            except: pass
            
            # Upload
            try:
                file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                driver.execute_script("arguments[0].style.display = 'block';", file_input)
                file_input.send_keys(final_image_path)
            except:
                # Click button fallback
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='New post']"))).click()
                time.sleep(1)
                driver.find_element(By.XPATH, "//input[@type='file']").send_keys(final_image_path)
            
            # Next -> Caption -> Share
            print("DEBUG: Uploading...")
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))).click()
            time.sleep(2)
            
            try:
                caption_area = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                caption_area.click()
                caption_area.send_keys(caption)
            except: pass
            
            print("DEBUG: Sharing...")
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Share')]"))).click()
            time.sleep(5)
            
            return {"success": True, "message": "Posted via Selenium automation."}
            
        except Exception as e:
            return {"error": f"Selenium Error: {str(e)}"}
        finally:
            if driver:
                time.sleep(2)
                driver.quit()

    def post_photo(self, image_url: str, caption: str) -> Dict:
        """Publish a photo to Instagram Feed using Graph API (Selenium disabled due to binary incompatibility)."""
        # Debugging
        print(f"DEBUG: Instagram Post Check - Token: {bool(self.access_token)}, Account ID: {bool(self.account_id)}")
        
        # DISABLED: Selenium causes binary crash on Windows. Using Graph API only.
        # if self.username and self.password and HAS_SELENIUM:
        #      print("Using Selenium for Instagram Post...")
        #      return self.post_photo_selenium(image_url, caption)

        # Graph API method (no browser automation)
        if not self.access_token or not self.account_id:
            return {"error": "INSTAGRAM_ACCOUNT_ID or INSTAGRAM_ACCESS_TOKEN missing in .env"}

            
        try:
            # Step 1: Create Container
            container_endpoint = f"{self.base_url}/{self.account_id}/media"
            payload = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            
            resp = requests.post(container_endpoint, params=payload)
            
            if resp.status_code != 200:
                return {"error": f"Failed to create media container: {resp.text}"}
                
            creation_id = resp.json().get("id")
            if not creation_id:
                return {"error": f"No creation ID returned: {resp.text}"}
            
            # Step 2: Publish Container
            publish_endpoint = f"{self.base_url}/{self.account_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": self.access_token
            }
            
            resp2 = requests.post(publish_endpoint, params=publish_payload)
            
            if resp2.status_code == 200:
                post_id = resp2.json().get("id")
                return {"success": True, "message": "Photo posted to Instagram!", "post_id": post_id}
            else:
                return {"error": f"Failed to publish container: {resp2.text}"}
                
        except Exception as e:
            return {"error": f"Instagram API Error: {str(e)}"}
