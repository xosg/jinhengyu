"""
Simple QQ Mail test without HTML
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_integration.email_service import create_email_service

# Load environment variables
load_dotenv()

print("Testing QQ Mail with plain text email...")

# Create email service
email_service = create_email_service()

# Send plain text email (not HTML)
result = email_service.send_email(
    to=os.getenv('QQMAIL_USER'),
    subject="QQ Mail Test - Plain Text",
    content="This is a plain text test email from QQ Mail SMTP service.",
    html=False  # Plain text, not HTML
)

print()
if result.get("status") == "success":
    print("[SUCCESS] Plain text email sent!")
else:
    print(f"[FAILED] Error: {result.get('error')}")
