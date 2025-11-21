"""
Debug test for QQ Mail SMTP
"""
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

qqmail_user = os.getenv('QQMAIL_USER', '')
qqmail_password = os.getenv('QQMAIL_PASSWORD', '')

print("="*80)
print("  QQ Mail SMTP Debug Test")
print("="*80)
print()
print(f"User: {qqmail_user}")
print(f"Password length: {len(qqmail_password)}")
print()

# Test 1: SSL on port 465
print("[Test 1] Trying SMTP_SSL on port 465...")
try:
    server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=10)
    server.set_debuglevel(1)  # Enable debug output
    print("  [OK] Connected to smtp.qq.com:465")

    server.login(qqmail_user, qqmail_password)
    print("  [OK] Login successful!")

    server.quit()
    print("  [SUCCESS] SSL port 465 works!")

except Exception as e:
    print(f"  [FAILED] Error: {type(e).__name__}: {e}")

print()

# Test 2: STARTTLS on port 587
print("[Test 2] Trying SMTP with STARTTLS on port 587...")
try:
    server = smtplib.SMTP('smtp.qq.com', 587, timeout=10)
    server.set_debuglevel(1)  # Enable debug output
    print("  [OK] Connected to smtp.qq.com:587")

    server.starttls()
    print("  [OK] STARTTLS successful")

    server.login(qqmail_user, qqmail_password)
    print("  [OK] Login successful!")

    server.quit()
    print("  [SUCCESS] STARTTLS port 587 works!")

except Exception as e:
    print(f"  [FAILED] Error: {type(e).__name__}: {e}")

print()
print("="*80)
