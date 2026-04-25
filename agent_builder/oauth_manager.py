"""
OAuth Manager for handling third-party authentication
Manages authentication flows for LinkedIn, Gmail, GitHub, WhatsApp, Google Meet
"""

import os
import json
import secrets
from typing import Optional, Dict, Tuple
import sqlite3
from datetime import datetime, timedelta


class OAuthManager:
    """Manage OAuth tokens and authentication flows."""
    
    def __init__(self, db_path: str = "oauth_tokens.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize OAuth tokens database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    id INTEGER PRIMARY KEY,
                    service TEXT UNIQUE,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_type TEXT,
                    expires_at TIMESTAMP,
                    user_id TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS oauth_state (
                    id INTEGER PRIMARY KEY,
                    state TEXT UNIQUE,
                    service TEXT,
                    created_at TIMESTAMP,
                    used INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing OAuth DB: {e}")
    
    def generate_state(self, service: str) -> str:
        """Generate OAuth state for CSRF protection."""
        try:
            state = secrets.token_urlsafe(32)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO oauth_state (state, service, created_at)
                VALUES (?, ?, ?)
            ''', (state, service, datetime.utcnow().isoformat()))
            
            conn.commit()
            conn.close()
            
            return state
        except Exception as e:
            print(f"Error generating state: {e}")
            return ""
    
    def verify_state(self, state: str) -> Tuple[bool, str]:
        """Verify OAuth state and return service name."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT service FROM oauth_state 
                WHERE state = ? AND used = 0 AND datetime(created_at) > datetime('now', '-10 minutes')
            ''', (state,))
            
            result = c.fetchone()
            
            if result:
                # Mark state as used
                c.execute('UPDATE oauth_state SET used = 1 WHERE state = ?', (state,))
                conn.commit()
                conn.close()
                return True, result[0]
            
            conn.close()
            return False, ""
        
        except Exception as e:
            print(f"Error verifying state: {e}")
            return False, ""
    
    def save_token(self, service: str, access_token: str, refresh_token: Optional[str] = None,
                   expires_in: Optional[int] = None, user_id: Optional[str] = None) -> bool:
        """Save OAuth token to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            expires_at = None
            if expires_in:
                expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            
            now = datetime.utcnow().isoformat()
            
            # Try to update first, then insert
            c.execute('''
                INSERT OR REPLACE INTO oauth_tokens 
                (service, access_token, refresh_token, expires_at, user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (service, access_token, refresh_token, expires_at, user_id, now, now))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"Error saving token: {e}")
            return False
    
    def get_token(self, service: str) -> Optional[Dict]:
        """Retrieve OAuth token for a service."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT access_token, refresh_token, expires_at, user_id
                FROM oauth_tokens
                WHERE service = ?
            ''', (service,))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                access_token, refresh_token, expires_at, user_id = result
                
                # Check if token expired
                if expires_at:
                    if datetime.fromisoformat(expires_at) < datetime.utcnow():
                        return None  # Token expired
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "user_id": user_id
                }
            
            return None
        
        except Exception as e:
            print(f"Error retrieving token: {e}")
            return None
    
    def delete_token(self, service: str) -> bool:
        """Delete OAuth token for a service."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('DELETE FROM oauth_tokens WHERE service = ?', (service,))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"Error deleting token: {e}")
            return False
    
    def is_authenticated(self, service: str) -> bool:
        """Check if user is authenticated with a service."""
        token = self.get_token(service)
        return token is not None
    
    def get_all_services(self) -> Dict[str, Dict]:
        """Get authentication status for all services."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('SELECT service, user_id, updated_at FROM oauth_tokens')
            
            results = c.fetchall()
            conn.close()
            
            services = {}
            for service, user_id, updated_at in results:
                services[service] = {
                    "authenticated": True,
                    "user_id": user_id,
                    "updated_at": updated_at
                }
            
            return services
        
        except Exception as e:
            print(f"Error getting services: {e}")
            return {}
    
    @staticmethod
    def create_auth_url(service: str, client_id: str, redirect_uri: str, 
                       scopes: list, state: str) -> str:
        """Create OAuth authorization URL."""
        
        if service.lower() == "linkedin":
            scope_str = " ".join(scopes)
            return (
                f"https://www.linkedin.com/oauth/v2/authorization?"
                f"response_type=code&"
                f"client_id={client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"state={state}&"
                f"scope={scope_str}"
            )
        
        elif service.lower() == "gmail":
            scope_str = " ".join(scopes)
            return (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"response_type=code&"
                f"scope={scope_str}&"
                f"state={state}&"
                f"access_type=offline"
            )
        
        elif service.lower() == "github":
            scope_str = ",".join(scopes)
            return (
                f"https://github.com/login/oauth/authorize?"
                f"client_id={client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope_str}&"
                f"state={state}"
            )
        
        return ""


# OAuth callback handler for Flask/FastAPI integration
class OAuthCallbackHandler:
    """Handle OAuth callbacks from third-party services."""
    
    def __init__(self, oauth_manager: OAuthManager):
        self.oauth_manager = oauth_manager
    
    def handle_linkedin_callback(self, code: str, state: str) -> Tuple[bool, str]:
        """Handle LinkedIn OAuth callback."""
        # Verify state
        is_valid, _ = self.oauth_manager.verify_state(state)
        if not is_valid:
            return False, "Invalid state parameter"
        
        # Exchange code for token
        try:
            import requests
            
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/oauth/linkedin/callback"),
                "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
                "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET")
            }
            
            response = requests.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Save token
                self.oauth_manager.save_token(
                    "linkedin",
                    token_response.get("access_token"),
                    refresh_token=token_response.get("refresh_token"),
                    expires_in=token_response.get("expires_in"),
                    user_id=None  # Will need to fetch from API
                )
                
                return True, "Successfully authenticated with LinkedIn"
            else:
                return False, f"Failed to get access token: {response.text}"
        
        except Exception as e:
            return False, f"Error during LinkedIn callback: {str(e)}"
    
    def handle_gmail_callback(self, code: str, state: str) -> Tuple[bool, str]:
        """Handle Gmail OAuth callback."""
        # Verify state
        is_valid, _ = self.oauth_manager.verify_state(state)
        if not is_valid:
            return False, "Invalid state parameter"
        
        # Exchange code for token
        try:
            import requests
            
            token_data = {
                "code": code,
                "client_id": os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                "redirect_uri": os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/oauth/gmail/callback"),
                "grant_type": "authorization_code"
            }
            
            response = requests.post(
                "https://oauth2.googleapis.com/token",
                data=token_data
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Save token
                self.oauth_manager.save_token(
                    "gmail",
                    token_response.get("access_token"),
                    refresh_token=token_response.get("refresh_token"),
                    expires_in=token_response.get("expires_in")
                )
                
                return True, "Successfully authenticated with Gmail"
            else:
                return False, f"Failed to get access token: {response.text}"
        
        except Exception as e:
            return False, f"Error during Gmail callback: {str(e)}"
    
    def handle_github_callback(self, code: str, state: str) -> Tuple[bool, str]:
        """Handle GitHub OAuth callback."""
        # Verify state
        is_valid, _ = self.oauth_manager.verify_state(state)
        if not is_valid:
            return False, "Invalid state parameter"
        
        # Exchange code for token
        try:
            import requests
            
            token_data = {
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "code": code,
                "state": state
            }
            
            response = requests.post(
                "https://github.com/login/oauth/access_token",
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                if "error" not in token_response:
                    # Save token
                    self.oauth_manager.save_token(
                        "github",
                        token_response.get("access_token"),
                        refresh_token=None,
                        expires_in=None
                    )
                    
                    return True, "Successfully authenticated with GitHub"
                else:
                    return False, f"GitHub error: {token_response.get('error_description')}"
            else:
                return False, f"Failed to get access token: {response.text}"
        
        except Exception as e:
            return False, f"Error during GitHub callback: {str(e)}"
