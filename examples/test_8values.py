"""
Test script for 8values quiz automation (non-interactive)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection.web_scraper import WebScraper
from src.api_integration.email_service import create_email_service


def test_8values():
    """Test the 8values quiz automation"""

    print("\n" + "="*60)
    print("TESTING 8VALUES QUIZ AUTOMATION")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Check credentials
    if not os.getenv('OUTLOOK_USER') or not os.getenv('OUTLOOK_PASSWORD'):
        print("\n   [ERROR] Outlook credentials not found!")
        return

    # Initialize services
    print("\nInitializing services...")
    scraper = WebScraper()
    email_service = create_email_service()
    print("   [OK] Services initialized")

    # Run the quiz
    from examples.demo_combined_menu import run_8values_quiz
    run_8values_quiz(scraper, email_service)

    scraper.close()

    print("\n" + "="*60)
    print("TEST COMPLETED!")
    print("="*60)


if __name__ == "__main__":
    test_8values()
