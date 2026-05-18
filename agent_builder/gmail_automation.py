"""
Gmail Automation Module - Send emails using Gmail API with OAuth
"""

import os
import json
import pickle
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'gmail_token.pickle'


class GmailAutomation:
    """Automate Gmail sending using OAuth credentials."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.service = None
        self.creds = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Gmail service with OAuth."""
        try:
            # 1. Try loading from pickle first
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'rb') as token:
                    self.creds = pickle.load(token)
                    logger.info("✅ Loaded existing Gmail token from pickle")
            
            # 2. Fallback to GMAIL_ACCESS_TOKEN from .env
            if not self.creds or not self.creds.valid:
                env_token = os.getenv("GMAIL_ACCESS_TOKEN")
                if env_token:
                    self.creds = Credentials(env_token)
                    logger.info("✅ Using Gmail Access Token from .env")

            if not self.creds:
                logger.warning("⚠️ No Gmail token found. Please authorize or set GMAIL_ACCESS_TOKEN in .env")
                return False
            
            # If creds have a refresh token, try to refresh if expired
            if self.creds and not self.creds.valid and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    logger.info("✅ Gmail token refreshed")
                except Exception as e:
                    if "invalid_grant" in str(e):
                        logger.error("❌ Gmail token expired (invalid_grant). Deleting token file.")
                        if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)
                    raise e
            
            # Build Gmail service
            if self.creds and self.creds.valid:
                self.service = build('gmail', 'v1', credentials=self.creds)
                logger.info("✅ Gmail service initialized successfully")
                return True
            
        except Exception as e:
            logger.error(f"❌ Gmail initialization error: {e}")
            return False
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: str = "", bcc: str = "", html: bool = False) -> bool:
        """
        Send an email using Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body/content
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: If True, treat body as HTML
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not self.service:
                logger.error("Gmail service not initialized")
                return False
            
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Add body
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            message.attach(part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send email
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ Email sent successfully to {to} (Message ID: {result['id']})")
            return True
            
        except GoogleAPIError as e:
            logger.error(f"❌ Gmail API error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    def authorize(self) -> bool:
        """Perform OAuth authorization to get Gmail access token."""
        try:
            logger.info("🔐 Starting Gmail OAuth authorization...")
            
            # Create credentials JSON for OAuth flow
            creds_dict = {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8000/"]
                }
            }
            
            # Write temp credentials file
            with open('gmail_creds_temp.json', 'w') as f:
                json.dump(creds_dict, f)
            
            # Perform OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                'gmail_creds_temp.json', SCOPES)
            logger.info("📱 Opening browser for authorization...\nIf browser doesn't open, visit: https://accounts.google.com/o/oauth2/auth")
            self.creds = flow.run_local_server(port=8000, open_browser=True)
            
            # Save token for future use
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)
            logger.info("✅ Gmail authorization successful! Token saved.")
            
            # Clean up temp file
            if os.path.exists('gmail_creds_temp.json'):
                os.remove('gmail_creds_temp.json')
            
            # Rebuild service with new credentials
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
            
        except Exception as e:
            logger.error(f"❌ OAuth authorization failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if Gmail is authenticated."""
        return self.service is not None and self.creds is not None


def get_gmail_automation() -> GmailAutomation:
    """Get Gmail automation instance with credentials from .env"""
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("Gmail credentials not found in .env")
        return None
    
    return GmailAutomation(client_id, client_secret)
