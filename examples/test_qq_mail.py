"""
Simple test to verify QQ Mail SMTP is working
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

print("="*80)
print("  QQ Mail SMTP Test")
print("="*80)
print()

# Check environment
email_provider = os.getenv('EMAIL_PROVIDER', 'outlook')
qqmail_user = os.getenv('QQMAIL_USER', '')
qqmail_password = os.getenv('QQMAIL_PASSWORD', '')

print(f"EMAIL_PROVIDER: {email_provider}")
print(f"QQMAIL_USER: {qqmail_user}")
print(f"QQMAIL_PASSWORD: {'*' * len(qqmail_password) if qqmail_password else 'NOT SET'}")
print()

if email_provider != 'qq':
    print("[WARNING] EMAIL_PROVIDER is not set to 'qq' in .env")
    print("         Email will use different provider")
    print()

if not qqmail_user or not qqmail_password:
    print("[ERROR] QQ Mail credentials not configured!")
    print("        Please set QQMAIL_USER and QQMAIL_PASSWORD in .env")
    sys.exit(1)

# Create email service
print("Creating email service...")
email_service = create_email_service()
print(f"[OK] Email service created: {email_service.provider_name}")
print()

# Send test email
print("Sending test email...")
result = email_service.send_email(
    to=qqmail_user,
    subject="QQ Mail SMTP Test - 测试邮件",
    content="""
    <h2>QQ Mail SMTP Test Successful! ✅</h2>

    <p>This is a test email to verify QQ Mail SMTP configuration.</p>

    <p><strong>Configuration Details:</strong></p>
    <ul>
        <li>SMTP Server: smtp.qq.com</li>
        <li>Port: 587</li>
        <li>TLS: Enabled</li>
        <li>Sender: {sender}</li>
    </ul>

    <p>If you received this email, your QQ Mail SMTP is working correctly!</p>

    <p style="color: #666; font-size: 12px;">
        Sent from Multi-API Integration System
    </p>
    """.format(sender=qqmail_user),
    html=True
)

print()
if result.get("status") == "success":
    print("="*80)
    print("[SUCCESS] Test email sent successfully!")
    print("="*80)
    print()
    print(f"Check your QQ Mail inbox: {qqmail_user}")
    print()
else:
    print("="*80)
    print("[FAILED] Email send failed!")
    print("="*80)
    print()
    print(f"Error: {result.get('error')}")
    print()
    print("Common issues:")
    print("  1. Authorization code is incorrect")
    print("  2. SMTP service not enabled in QQ Mail settings")
    print("  3. Firewall blocking port 587")
    print()
