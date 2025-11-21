"""
File Watcher Demo
Demonstrates how to monitor directories and send email notifications on file changes
"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.collection.file_watcher import create_file_watcher


def main():
    """Run file watcher demo"""

    print("=" * 80)
    print("FILE WATCHER DEMO")
    print("=" * 80)
    print()
    print("This demo monitors the ./test directory and sends email notifications")
    print("when files are added or modified.")
    print()
    print("SETUP REQUIRED:")
    print("1. Ensure your .env file has the following variables:")
    print("   - NOTIFY_EMAIL=your_qqmail@qq.com  (recipient)")
    print("   - EMAIL_PROVIDER=qq  (or outlook)")
    print("   - QQMAIL_USER=your_email@qq.com")
    print("   - QQMAIL_PASSWORD=your_auth_code")
    print()
    print("2. The configuration is in config/collection_config.yaml")
    print("   under the 'file_watching' section")
    print()
    print("=" * 80)
    print()

    try:
        # Create file watcher service
        print("Initializing file watcher...")
        watcher = create_file_watcher()

        # Show configuration
        print("\nConfigured to watch:")
        for dir_config in watcher.watched_dirs:
            if dir_config.get('enabled', True):
                path = dir_config.get('path', '')
                recursive = dir_config.get('recursive', False)
                notify_email = watcher._resolve_env_var(dir_config.get('notify_email', ''))

                print(f"  - {path}")
                print(f"    Recursive: {recursive}")
                print(f"    Notify email: {notify_email or '(not configured)'}")
                print()

        # Check if email is configured
        if not watcher.email_service:
            print("⚠️  WARNING: Email service not initialized!")
            print("   File changes will be logged but no emails will be sent.")
            print()

        # Start watching
        print("Starting file watcher...")
        print()
        print("TIP: Try these actions to test:")
        print("  1. Create a new file in ./test/")
        print("  2. Edit an existing file in ./test/")
        print("  3. Add multiple files at once")
        print()
        print("The watcher will:")
        print(f"  - Wait {watcher.debounce_delay} seconds to batch changes")
        print("  - Send email with all changed files as attachments")
        print()

        # Run the watcher (blocks until Ctrl+C)
        watcher.watch_forever()

    except FileNotFoundError as e:
        print(f"❌ Error: Configuration file not found")
        print(f"   {e}")
        print()
        print("Please ensure config/collection_config.yaml exists.")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n✓ File watcher stopped by user")

    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        print()
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
