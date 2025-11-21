"""
Test script for Search & Scrape feature (non-interactive)
This script tests the full workflow without requiring user input
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection.web_scraper import WebScraper
from src.api_integration.email_service import create_email_service
from src.api_integration.search_service import create_search_service


def test_search_and_scrape():
    """Test the search and scrape functionality"""

    print("\n" + "="*60)
    print("NON-INTERACTIVE TEST: Search & Scrape")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Check credentials
    if not os.getenv('OUTLOOK_USER') or not os.getenv('OUTLOOK_PASSWORD'):
        print("\n   [ERROR] Outlook credentials not found!")
        return

    if not os.getenv('GOOGLE_API_KEY') or not os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
        print("\n   [ERROR] Google API credentials not found!")
        return

    # Initialize services
    print("\nInitializing services...")
    scraper = WebScraper()
    email_service = create_email_service()
    search_service = create_search_service()
    print("   [OK] Services initialized")

    # Test parameters
    test_query = "Python tutorials"
    num_results = 3  # Use 3 for faster testing

    print(f"\nTest query: '{test_query}'")
    print(f"Number of results: {num_results}")

    try:
        # Import the search_and_scrape function logic
        from examples.demo_combined_menu import search_and_scrape, create_multi_site_report

        print("\n" + "="*60)
        print("STEP 1: Search with Google API")
        print("="*60)

        search_results = search_service.search(test_query, num_results=num_results)

        if not search_results:
            print("   [ERROR] No search results found")
            scraper.close()
            return

        print(f"   [OK] Found {len(search_results)} results:")
        for idx, result in enumerate(search_results, 1):
            print(f"      {idx}. {result['title']}")
            print(f"         {result['url']}")

        print("\n" + "="*60)
        print("STEP 2: Scrape discovered websites")
        print("="*60)

        results = []
        for idx, search_result in enumerate(search_results, 1):
            # Create site config for scraper
            site_config = {
                'name': f"Google Result {idx} - {search_result['display_url']}",
                'url': search_result['url'],
                'extract_elements': [
                    {'selector': 'h1', 'type': 'text'},
                    {'selector': 'h2', 'type': 'list'},
                    {'selector': 'p', 'type': 'list'}
                ],
                'output_dir': 'collected_data/web/google_discovery'
            }

            print(f"\n[{idx}/{len(search_results)}] Processing: {search_result['display_url']}")

            # Use Google thumbnail if available
            google_image = search_result.get('thumbnail_url') or search_result.get('image_url')
            if google_image:
                print(f"   [INFO] Using Google thumbnail: {google_image[:60]}...")

            from examples.demo_combined_menu import scrape_site
            result = scrape_site(site_config, scraper, google_image_url=google_image)
            results.append(result)

            # Small delay between requests
            if idx < len(search_results):
                import time
                time.sleep(1)

        scraper.close()

        # Count successes
        success_count = len([r for r in results if r['success']])
        print(f"\n   [OK] Successfully scraped {success_count}/{len(results)} sites")

        if success_count == 0:
            print("   [ERROR] No sites were scraped successfully")
            return

        print("\n" + "="*60)
        print("STEP 3: Create combined report")
        print("="*60)

        combined_html, attachments = create_multi_site_report(results, create_attachments=True)
        print(f"   [OK] Report created ({len(combined_html)} characters)")
        print(f"   [OK] Created {len(attachments)} attachments")

        for att in attachments:
            filename = Path(att).name
            size_kb = Path(att).stat().st_size / 1024
            print(f"       - {filename} ({size_kb:.1f} KB)")

        print("\n" + "="*60)
        print("STEP 4: Send email")
        print("="*60)

        recipient_email = os.getenv('OUTLOOK_USER')
        print(f"\nSending to: {recipient_email}")

        email_result = email_service.send_email(
            to=recipient_email,
            subject=f"Test: Google Search & Scrape - {success_count} Websites",
            content=combined_html,
            html=True,
            attachments=attachments
        )

        if email_result["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Subject: {email_result['subject']}")
        else:
            print(f"   [ERROR] Failed to send email: {email_result.get('error')}")

        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\nScraped {success_count} Google-discovered websites")
        print(f"Sent 1 combined email with {len(attachments)} attachments")
        print("\nCheck your email inbox!")

    except Exception as e:
        print(f"\n   [ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        scraper.close()


if __name__ == "__main__":
    test_search_and_scrape()
