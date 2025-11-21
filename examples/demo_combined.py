"""
Demo script: Combining Module 1 & Module 2
Scrape web content and email it as HTML report

This demonstrates a practical integration:
1. Module 1: Scrape website content
2. Module 2: Send scraped content via email

Before running:
- Install dependencies: pip install -r requirements.txt
- Set up .env file with Outlook credentials
"""

import os
import sys
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection.web_scraper import WebScraper
from src.api_integration.email_service import create_email_service


def create_html_report(scraped_data: dict, extracted_data: dict, screenshot_path: str = None) -> str:
    """
    Create a nice HTML email from scraped data

    Args:
        scraped_data: Data returned from web scraper
        extracted_data: Extracted content from the scraped site

    Returns:
        HTML string for email
    """
    # Load HTML template from external file
    template_path = Path(__file__).parent.parent / "templates" / "email_report.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Extract content from scraped data
    content_html = ""
    for selector, content in extracted_data.items():
        if isinstance(content, list):
            # It's a list of items
            content_html += f"<p><strong>&lt;{selector}&gt;</strong> (found {len(content)} items):</p><ul>"
            for item in content[:10]:  # Show first 10 items
                item_text = str(item)[:300]  # Truncate long items
                content_html += f"<li>{item_text}</li>"
            if len(content) > 10:
                content_html += f"<li><em>... and {len(content) - 10} more items</em></li>"
            content_html += "</ul>"
        else:
            # It's a single text value
            content_html += f"<p><strong>&lt;{selector}&gt;:</strong> {content}</p>"

    # Get timestamp from output path (extract from directory name)
    import re
    timestamp_match = re.search(r'_(\d{8}_\d{6})', scraped_data.get('output_path', ''))
    timestamp = timestamp_match.group(1).replace('_', ' ') if timestamp_match else 'Unknown'

    # Convert screenshot to base64 for embedding in email
    screenshot_html = ""
    if screenshot_path and Path(screenshot_path).exists():
        with open(screenshot_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
            screenshot_data = f"data:image/png;base64,{img_data}"
            screenshot_html = f"""
    <div class="section">
        <h2>Website Screenshot</h2>
        <div class="content-box" style="text-align: center;">
            <img src="{screenshot_data}" alt="Website Screenshot" style="max-width: 100%; border: 1px solid #ddd; border-radius: 3px;">
            <p style="font-size: 12px; color: #666; margin-top: 10px;">Full-page screenshot captured with Selenium WebDriver</p>
        </div>
    </div>
"""
    else:
        screenshot_html = f"""
    <div class="section">
        <h2>Website Screenshot</h2>
        <div class="content-box" style="text-align: center; padding: 30px; background-color: #fff8dc;">
            <p style="color: #856404;"><strong>⚠️ Screenshot not available</strong></p>
            <p style="font-size: 14px; color: #666;">Selenium requires Chrome or Firefox to capture screenshots.<br>
            Install a browser to enable this feature.</p>
        </div>
    </div>
"""

    # Render template with data (simple string replacement)
    html = html_template
    html = html.replace('{{name}}', scraped_data.get('name', 'Unknown'))
    html = html.replace('{{url}}', scraped_data.get('url', 'Unknown'))
    html = html.replace('{{timestamp}}', timestamp)
    html = html.replace('{{screenshot_section}}', screenshot_html)
    html = html.replace('{{content}}', content_html or "<p><em>No content extracted</em></p>")
    html = html.replace('{{output_path}}', scraped_data.get('output_path', 'Unknown'))
    html = html.replace('{{elements_count}}', str(len(extracted_data)))

    return html


def main():
    """Run combined demo: scrape content and email it"""
    print("\n" + "="*60)
    print("COMBINED DEMO: Web Scraping + Email Integration")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Check credentials
    if not os.getenv('OUTLOOK_USER') or not os.getenv('OUTLOOK_PASSWORD'):
        print("\n   [ERROR] Outlook credentials not found!")
        print("   Please set OUTLOOK_USER and OUTLOOK_PASSWORD in .env file")
        return

    recipient_email = os.getenv('OUTLOOK_USER')

    try:
        # ==========================================
        # STEP 1: Scrape Website (Module 1)
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 1: Scraping Website (Module 1: Data Collection)")
        print("-"*60)

        scraper = WebScraper()

        print("\nScraping example.com...")
        scraped_data = scraper.scrape_static_site(
            url="https://example.com",
            name="Example Domain",
            extract_elements=[
                {"selector": "h1", "type": "text"},
                {"selector": "p", "type": "list"}
            ],
            output_dir="collected_data/web/static"
        )

        print(f"   [OK] Successfully scraped!")
        print(f"   [OK] URL: {scraped_data['url']}")
        print(f"   [OK] Elements extracted: {scraped_data['extracted_elements']}")
        print(f"   [OK] Saved to: {scraped_data['output_path']}")

        # Load extracted data from file
        output_dir = Path(scraped_data['output_path'])
        extracted_data_file = output_dir / "extracted_data.json"

        with open(extracted_data_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)

        print(f"   [OK] Loaded extracted data: {list(extracted_data.keys())}")

        # ==========================================
        # STEP 2: Capture Screenshot
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 2: Capturing Website Screenshot (Selenium)")
        print("-"*60)

        screenshot_path = None
        try:
            print(f"\nCapturing full-page screenshot of {scraped_data['url']}...")
            screenshot_path = output_dir / "screenshot.png"
            scraper.capture_screenshot(
                url=scraped_data['url'],
                output_path=str(screenshot_path),
                width=1280,
                height=720,
                full_page=True
            )
            print(f"   [OK] Screenshot saved to: {screenshot_path}")

            # Get screenshot file size
            screenshot_size_kb = screenshot_path.stat().st_size / 1024
            print(f"   [OK] Screenshot size: {screenshot_size_kb:.1f} KB")
        except Exception as e:
            print(f"   [WARNING] Could not capture screenshot: {str(e)[:100]}")
            print(f"   [WARNING] Selenium requires Chrome/Firefox installed")
            print(f"   [WARNING] Continuing without screenshot...")
            screenshot_path = None

        scraper.close()

        # ==========================================
        # STEP 3: Create HTML Report
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 3: Creating HTML Email Report")
        print("-"*60)

        print("\nGenerating HTML report with embedded screenshot...")
        html_report = create_html_report(scraped_data, extracted_data, str(screenshot_path))
        print(f"   [OK] HTML report created ({len(html_report)} characters)")
        print(f"   [OK] Screenshot embedded as base64 data")

        # ==========================================
        # STEP 4: Send Email (Module 2)
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 4: Sending Email (Module 2: API Integration)")
        print("-"*60)

        email_service = create_email_service()

        print(f"\nSending HTML email to {recipient_email}...")
        result = email_service.send_email(
            to=recipient_email,
            subject="Web Scraping Report - example.com",
            content=html_report,
            html=True  # <-- ENABLE HTML!
        )

        if result["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Recipient: {result['to']}")
            print(f"   [OK] Subject: {result['subject']}")
            print(f"   [OK] Format: HTML")
        else:
            print(f"   [ERROR] Failed to send email: {result.get('error')}")

        # ==========================================
        # Summary
        # ==========================================
        print("\n" + "="*60)
        print("DEMO COMPLETED!")
        print("="*60)
        print("\nWhat happened:")
        print("  1. Module 1 scraped content from example.com (requests + BeautifulSoup)")
        print("  2. Captured full-page screenshot using Selenium WebDriver")
        print("  3. Created formatted HTML report with embedded screenshot")
        print("  4. Module 2 sent the report via Outlook SMTP API")
        print("\nCheck your email inbox for the HTML report with screenshot!")
        print("This demonstrates:")
        print("  - Web scraping (static content extraction)")
        print("  - Browser automation (Selenium screenshot capture)")
        print("  - Email API integration (Outlook SMTP)")
        print("  - HTML email with base64-encoded images")
        print("\n")

    except Exception as e:
        print(f"\n   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
