"""
Email Auto-Reply Demo
Monitors QQ Mail inbox and automatically replies to new emails with the same content
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.collection.email_auto_reply import create_auto_reply_service


def main():
    """Run email auto-reply demo"""

    print("=" * 80)
    print("EMAIL AUTO-REPLY DEMO")
    print("=" * 80)
    print()
    print("This demo monitors your QQ Mail inbox and automatically replies to new emails")
    print("with the same content (echo/mirror reply).")
    print()
    print("SETUP REQUIRED:")
    print("  - QQMAIL_USER=your_email@qq.com")
    print("  - QQMAIL_PASSWORD=your_authorization_code")
    print("  - EMAIL_PROVIDER=qq")
    print()
    print("API USED:")
    print("  - IMAP (imap.qq.com:993) - To monitor incoming emails")
    print("  - SMTP (smtp.qq.com:465) - To send auto-replies")
    print()
    print("=" * 80)
    print()

    try:
        # Create auto-reply service
        print("Initializing auto-reply service...")
        service = create_auto_reply_service()

        # Start monitoring (blocks until Ctrl+C)
        service.monitor_forever()

    except KeyboardInterrupt:
        print("\nStopped by user")

    except Exception as e:
        import traceback
        print(f"\nError: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
