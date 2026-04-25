#!/usr/bin/env python3
"""
Diagnose Gmail authentication and token status
"""

import os
import pickle
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def diagnose_gmail():
    """Check Gmail authentication status"""
    
    load_dotenv()
    
    logger.info("=" * 60)
    logger.info("GMAIL AUTHENTICATION DIAGNOSTIC")
    logger.info("=" * 60)
    
    # Check 1: .env credentials
    logger.info("\n✓ Checking .env credentials...")
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    
    if client_id:
        logger.info(f"  ✅ GMAIL_CLIENT_ID: Found ({len(client_id)} chars)")
    else:
        logger.error(f"  ❌ GMAIL_CLIENT_ID: MISSING")
        
    if client_secret:
        logger.info(f"  ✅ GMAIL_CLIENT_SECRET: Found ({len(client_secret)} chars)")
    else:
        logger.error(f"  ❌ GMAIL_CLIENT_SECRET: MISSING")
    
    # Check 2: Token file
    logger.info("\n✓ Checking token file...")
    token_file = "gmail_token.pickle"
    
    if os.path.exists(token_file):
        size = os.path.getsize(token_file)
        mtime = datetime.fromtimestamp(os.path.getmtime(token_file))
        logger.info(f"  ✅ Token file exists: {token_file}")
        logger.info(f"     Size: {size} bytes")
        logger.info(f"     Last modified: {mtime}")
        
        # Check 3: Token validity
        logger.info("\n✓ Checking token validity...")
        try:
            with open(token_file, 'rb') as f:
                creds = pickle.load(f)
                
            if creds:
                logger.info(f"  ✅ Token loaded successfully")
                
                if hasattr(creds, 'valid'):
                    logger.info(f"  📊 Token valid: {creds.valid}")
                    
                if hasattr(creds, 'expired'):
                    logger.info(f"  📊 Token expired: {creds.expired}")
                    
                if hasattr(creds, 'expiry'):
                    logger.info(f"  📊 Token expiry time: {creds.expiry}")
                    
                if hasattr(creds, 'refresh_token'):
                    has_refresh = bool(creds.refresh_token)
                    logger.info(f"  📊 Has refresh token: {has_refresh}")
            else:
                logger.error(f"  ❌ Token is None/empty")
                
        except Exception as e:
            logger.error(f"  ❌ Failed to load token: {e}")
    else:
        logger.warning(f"  ⚠️  Token file not found: {token_file}")
        logger.info(f"     This file is created after Gmail authorization")
        logger.info(f"     Run: python gmail_auth.py")
    
    # Check 4: Gmail service initialization
    logger.info("\n✓ Checking Gmail service initialization...")
    try:
        from gmail_automation import get_gmail_automation
        
        gmail = get_gmail_automation()
        if gmail:
            logger.info(f"  ✅ GmailAutomation instance created")
            
            if hasattr(gmail, 'service') and gmail.service:
                logger.info(f"  ✅ Gmail service is READY")
            else:
                logger.error(f"  ❌ Gmail service is NOT initialized")
                logger.info(f"     → Token may be expired or invalid")
                logger.info(f"     → Run: python gmail_auth.py to re-authorize")
        else:
            logger.error(f"  ❌ Failed to create GmailAutomation instance")
            
    except Exception as e:
        logger.error(f"  ❌ Error during service initialization: {e}")
    
    # Summary & recommendations
    logger.info("\n" + "=" * 60)
    logger.info("RECOMMENDATIONS:")
    logger.info("=" * 60)
    
    logger.info("\nIf Gmail is not authenticated:")
    logger.info("  1. Run: python gmail_auth.py")
    logger.info("  2. This will open your browser for authorization")
    logger.info("  3. Grant permission to your agent")
    logger.info("  4. A new token will be saved automatically")
    logger.info("\nIf token is expired:")
    logger.info("  1. The system will try to refresh automatically")
    logger.info("  2. If refresh fails, run: python gmail_auth.py again")
    logger.info("=" * 60)

if __name__ == "__main__":
    diagnose_gmail()
