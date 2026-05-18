import os
import sys
import sqlite3
import requests
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrations import LinkedInIntegration

logging.basicConfig(level=logging.INFO)

def get_linkedin_token():
    try:
        conn = sqlite3.connect("oauth_tokens.db")
        c = conn.cursor()
        c.execute("SELECT access_token FROM oauth_tokens WHERE service = 'linkedin'")
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error fetching token: {e}")
        return None

def test_linkedin():
    token = get_linkedin_token()
    if not token:
        print("❌ LinkedIn token not found in database.")
        return

    print("✅ Found LinkedIn token. Testing profile fetch...")
    li = LinkedInIntegration(access_token=token)
    profile = li.get_profile()
    
    if "error" in profile:
        print(f"❌ Profile fetch failed: {profile['error']}")
        return
    
    print(f"✅ Profile fetch successful! Name: {profile.get('name', 'N/A')} (ID: {getattr(li, 'person_urn', 'N/A')})")
    
    print("\nAttempting sample post...")
    # Using a slightly unique message to avoid duplicates
    message = f"Testing AI Agent Builder LinkedIn Integration! 🚀 (Ref: {os.getpid()})"
    result = li.share_post(content=message)
    
    if "success" in result:
        print(f"✅ LinkedIn post successful! URL: {result['url']}")
    else:
        print(f"❌ LinkedIn post failed: {result.get('error')}")

if __name__ == "__main__":
    test_linkedin()
