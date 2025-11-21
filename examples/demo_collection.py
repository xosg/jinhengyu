"""
Demo script for Module 1: Data Collection Engine

This script demonstrates:
1. Web scraping (static sites)
2. Email monitoring and attachment download
3. File organization by type

Before running:
- Install dependencies: pip install -r requirements.txt
- Set up .env file with Outlook credentials
- Update config/collection_config.yaml with your targets
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection.web_scraper import WebScraper
from src.collection.email_monitor import EmailMonitor
from src.collection.attachment_handler import AttachmentHandler


def demo_web_scraping():
    """Demo web scraping functionality"""
    print("\n" + "="*60)
    print("DEMO 1: Web Scraping")
    print("="*60)

    try:
        scraper = WebScraper()

        # Example 1: Scrape a simple static site
        print("\n1. Scraping static site (example.com)...")
        result = scraper.scrape_static_site(
            url="https://example.com",
            name="Example Site",
            extract_elements=[
                {"selector": "h1", "type": "text"},
                {"selector": "p", "type": "list"}
            ],
            output_dir="collected_data/web/static"
        )
        print(f"   [OK] Success! Output: {result['output_path']}")

        # Example 2: Scrape all configured static sites
        print("\n2. Scraping all configured static sites...")
        results = scraper.scrape_static_sites()
        print(f"   [OK] Scraped {results['successful']}/{results['total_sites']} sites")

        scraper.close()

    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def demo_email_monitoring():
    """Demo email monitoring functionality"""
    print("\n" + "="*60)
    print("DEMO 2: Email Monitoring")
    print("="*60)

    # Check if credentials are set
    if not os.getenv('OUTLOOK_USER') or not os.getenv('OUTLOOK_PASSWORD'):
        print("\n   [WARNING] Outlook credentials not found in environment!")
        print("   Please set OUTLOOK_USER and OUTLOOK_PASSWORD in .env file")
        print("   Skipping email monitoring demo...")
        return

    try:
        monitor = EmailMonitor()

        print("\n1. Connecting to email server...")
        monitor.connect()
        print("   [OK] Connected successfully!")

        print("\n2. Fetching emails by configured filters...")
        results = monitor.fetch_emails_by_filters()
        print(f"   [OK] Fetched {results['total_emails_fetched']} emails")
        print(f"   [OK] Downloaded {results['total_attachments_downloaded']} attachments")

        monitor.disconnect()

    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        print("   Make sure you're using the correct Outlook password!")
        print("   If you have 2FA enabled, you may need an App Password")


def demo_attachment_handling():
    """Demo attachment handling functionality"""
    print("\n" + "="*60)
    print("DEMO 3: Attachment Organization")
    print("="*60)

    try:
        handler = AttachmentHandler()

        # Check if we have any collected data
        collected_dir = Path("collected_data/email")
        if not collected_dir.exists() or not any(collected_dir.rglob('*')):
            print("\n   [WARNING] No collected email data found.")
            print("   Run email monitoring demo first, or create test files manually.")

            # Create sample test files for demo
            print("\n   Creating sample test files for demo...")
            test_dir = Path("collected_data/test_files")
            test_dir.mkdir(parents=True, exist_ok=True)

            # Create dummy files
            (test_dir / "document.pdf").write_text("PDF content")
            (test_dir / "spreadsheet.xlsx").write_text("Excel content")
            (test_dir / "image.jpg").write_text("Image content")
            (test_dir / "notes.txt").write_text("Text content")

            print(f"   [OK] Created sample files in {test_dir}")

            print("\n1. Creating file inventory...")
            inventory = handler.create_file_inventory(
                str(test_dir),
                output_file="collected_data/file_inventory.json"
            )
            print(f"   [OK] Found {inventory['total_files']} files")
            print(f"   [OK] Total size: {inventory['total_size_mb']} MB")
            print(f"   [OK] Categories: {list(inventory['by_category'].keys())}")

            print("\n2. Organizing files by type...")
            results = handler.organize_files(
                source_dir=str(test_dir),
                output_dir="collected_data/organized",
                organize_by_type=True
            )
            print(f"   [OK] Organized {results['organized']} files")
            print(f"   [OK] By category: {results['by_category']}")

        else:
            print("\n1. Creating file inventory...")
            inventory = handler.create_file_inventory(
                "collected_data/email",
                output_file="collected_data/file_inventory.json"
            )
            print(f"   [OK] Found {inventory['total_files']} files")
            print(f"   [OK] Total size: {inventory['total_size_mb']} MB")

            print("\n2. Organizing files by type...")
            results = handler.organize_files(
                source_dir="collected_data/email/attachments",
                output_dir="collected_data/organized",
                organize_by_type=True
            )
            print(f"   [OK] Organized {results['organized']} files")
            print(f"   [OK] By category: {results['by_category']}")

    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("MODULE 1: DATA COLLECTION ENGINE - DEMO")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Run demos
    demo_web_scraping()
    demo_email_monitoring()
    demo_attachment_handling()

    print("\n" + "="*60)
    print("DEMO COMPLETED!")
    print("="*60)
    print("\nCheck the following directories for results:")
    print("  - collected_data/web/        (web scraping results)")
    print("  - collected_data/email/      (email monitoring results)")
    print("  - collected_data/organized/  (organized files)")
    print("  - logs/collection_log.jsonl  (activity logs)")
    print("\n")


if __name__ == "__main__":
    main()
