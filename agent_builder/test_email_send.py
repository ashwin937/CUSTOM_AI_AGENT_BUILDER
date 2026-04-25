#!/usr/bin/env python3
"""
Test Gmail email sending with detailed error reporting
"""

import logging
from gmail_automation import get_gmail_automation

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_email_send():
    """Send a test email with full error details"""
    
    logger.info("=" * 70)
    logger.info("GMAIL EMAIL SENDING TEST")
    logger.info("=" * 70)
    
    # Initialize Gmail
    logger.info("\n1️⃣  Initializing Gmail automation...")
    gmail = get_gmail_automation()
    
    if not gmail:
        logger.error("❌ Failed to create GmailAutomation instance")
        return
    
    logger.info("✅ GmailAutomation instance created")
    
    # Check service
    logger.info("\n2️⃣  Checking Gmail service...")
    if not gmail.service:
        logger.error("❌ Gmail service not initialized")
        logger.info("   Solution: Run 'python gmail_auth.py' to authorize")
        return
    
    if not gmail.creds:
        logger.error("❌ Gmail credentials not loaded")
        return
    
    logger.info("✅ Gmail service is ready")
    logger.info(f"   Credentials valid: {gmail.creds.valid}")
    logger.info(f"   Credentials expired: {gmail.creds.expired}")
    
    # Send test email
    logger.info("\n3️⃣  Sending test email...")
    test_recipient = "ashwinkbd3@gmail.com"
    test_subject = "Test Email from AI Agent Builder"
    test_body = """Hello,

This is a test email from the AI Agent Builder system.

If you received this, email integration is working correctly! ✅

Timestamp: """ + str(__import__('datetime').datetime.now())
    
    logger.info(f"   To: {test_recipient}")
    logger.info(f"   Subject: {test_subject}")
    logger.info(f"   Body length: {len(test_body)} chars")
    
    try:
        result = gmail.send_email(
            to=test_recipient,
            subject=test_subject,
            body=test_body,
            html=False
        )
        
        if result:
            logger.info("✅ EMAIL SENT SUCCESSFULLY!")
            logger.info(f"   Result: {result}")
        else:
            logger.error("❌ EMAIL SENDING FAILED")
            logger.error("   send_email() returned False or empty")
            logger.info("\n   Troubleshooting:")
            logger.info("   1. Check that the email address is correct")
            logger.info("   2. Verify Gmail is still authorized (token not revoked)")
            logger.info("   3. Check Gmail account quotas/limits")
            logger.info("   4. Try re-authorizing: python gmail_auth.py")
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION DURING EMAIL SEND: {type(e).__name__}")
        logger.error(f"   Error message: {str(e)}")
        logger.info("\n   Troubleshooting:")
        logger.info("   1. Copy the error above and search for solutions")
        logger.info("   2. If 'invalid_grant': token may be revoked, re-authorize")
        logger.info("   3. If 'quota exceeded': wait before sending more emails")
        logger.info("   4. Run 'python gmail_auth.py' to get a fresh token")
        import traceback
        logger.debug(f"\nFull traceback:\n{traceback.format_exc()}")
    
    logger.info("\n" + "=" * 70)

if __name__ == "__main__":
    test_email_send()
