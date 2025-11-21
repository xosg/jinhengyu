"""
Demo script: Combining Module 1 & Module 2 with RAW HTML injection
Scrape web content and email it with preserved HTML formatting

⚠️ SECURITY NOTE:
This version injects raw HTML from scraped content into the email.
This is SAFE for trusted domains (example.com) but could be a security risk
with untrusted sources. For production, use HTML sanitization libraries.

Before running:
- Install dependencies: pip install -r requirements.txt
- Set up .env file with Outlook credentials
"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection.web_scraper import WebScraper
from src.api_integration.email_service import create_email_service


def sanitize_html_basic(html_content: str) -> str:
    """
    Basic HTML sanitization - removes dangerous tags/attributes

    ⚠️ NOTE: This is a simple implementation for demo purposes.
    For production, use libraries like bleach or html-sanitizer.

    Args:
        html_content: Raw HTML string

    Returns:
        Sanitized HTML string
    """
    # Remove script tags and their content
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    # Remove event handlers (onclick, onerror, etc.)
    html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'\s*on\w+\s*=\s*[^\s>]+', '', html_content, flags=re.IGNORECASE)

    # Remove iframe tags
    html_content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    # Remove object/embed tags
    html_content = re.sub(r'<(object|embed)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

    # Remove javascript: URLs
    html_content = re.sub(r'javascript:[^"\']*', '', html_content, flags=re.IGNORECASE)

    return html_content


def create_html_report(scraped_data: dict, extracted_data: dict, use_raw_html: bool = True) -> str:
    """
    Create HTML email from scraped data

    Args:
        scraped_data: Data returned from web scraper
        extracted_data: Extracted content from the scraped site
        use_raw_html: If True, inject raw HTML; if False, use plain text

    Returns:
        HTML string for email
    """
    # Load HTML template from external file
    template_path = Path(__file__).parent.parent / "templates" / "email_report.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Load the raw HTML from scraped page
    output_dir = Path(scraped_data['output_path'])
    page_html_file = output_dir / "page.html"

    with open(page_html_file, 'r', encoding='utf-8') as f:
        raw_page_html = f.read()

    # Extract content with or without HTML
    content_html = ""

    if use_raw_html:
        content_html += "<div style='background: #fffbf0; padding: 15px; border: 1px solid #ffd700; border-radius: 5px; margin-bottom: 10px;'>"
        content_html += "<p><strong>⚠️ Mode: RAW HTML Injection</strong> - Preserving original HTML structure and formatting</p>"
        content_html += "</div>"

        # Parse the raw HTML to extract specific sections
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_page_html, 'html.parser')

        for selector, content in extracted_data.items():
            elements = soup.select(selector)

            if elements:
                content_html += f"<div style='margin-bottom: 20px;'>"
                content_html += f"<p><strong>Selector:</strong> <code>&lt;{selector}&gt;</code> (found {len(elements)} element(s))</p>"

                # Inject raw HTML (sanitized for safety)
                for idx, element in enumerate(elements[:5], 1):  # Limit to first 5
                    raw_html = str(element)
                    sanitized_html = sanitize_html_basic(raw_html)

                    content_html += f"<div style='border-left: 3px solid #4CAF50; padding-left: 10px; margin: 10px 0;'>"
                    content_html += f"<small style='color: #666;'>Element {idx}:</small><br>"
                    content_html += sanitized_html
                    content_html += "</div>"

                if len(elements) > 5:
                    content_html += f"<p><em>... and {len(elements) - 5} more elements</em></p>"

                content_html += "</div>"
    else:
        # Plain text mode (original approach)
        content_html += "<div style='background: #f0f8ff; padding: 15px; border: 1px solid #4CAF50; border-radius: 5px; margin-bottom: 10px;'>"
        content_html += "<p><strong>✓ Mode: PLAIN TEXT</strong> - HTML stripped for security</p>"
        content_html += "</div>"

        for selector, content in extracted_data.items():
            if isinstance(content, list):
                content_html += f"<p><strong>&lt;{selector}&gt;</strong> (found {len(content)} items):</p><ul>"
                for item in content[:10]:
                    item_text = str(item)[:300]
                    content_html += f"<li>{item_text}</li>"
                if len(content) > 10:
                    content_html += f"<li><em>... and {len(content) - 10} more items</em></li>"
                content_html += "</ul>"
            else:
                content_html += f"<p><strong>&lt;{selector}&gt;:</strong> {content}</p>"

    # Get timestamp from output path
    timestamp_match = re.search(r'_(\d{8}_\d{6})', scraped_data.get('output_path', ''))
    timestamp = timestamp_match.group(1).replace('_', ' ') if timestamp_match else 'Unknown'

    # Render template with data
    html = html_template
    html = html.replace('{{name}}', scraped_data.get('name', 'Unknown'))
    html = html.replace('{{url}}', scraped_data.get('url', 'Unknown'))
    html = html.replace('{{timestamp}}', timestamp)
    html = html.replace('{{content}}', content_html or "<p><em>No content extracted</em></p>")
    html = html.replace('{{output_path}}', scraped_data.get('output_path', 'Unknown'))
    html = html.replace('{{elements_count}}', str(len(extracted_data)))

    return html


def main():
    """Run combined demo with HTML injection comparison"""
    print("\n" + "="*60)
    print("COMBINED DEMO: Web Scraping + HTML Email")
    print("Demonstrating RAW HTML injection vs Plain Text")
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
        # STEP 1: Scrape Website
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 1: Scraping Website (Module 1)")
        print("-"*60)

        scraper = WebScraper()

        print("\nScraping example.com...")
        scraped_data = scraper.scrape_static_site(
            url="https://example.com",
            name="Example Domain - HTML Injection Demo",
            extract_elements=[
                {"selector": "h1", "type": "text"},
                {"selector": "p", "type": "list"},
                {"selector": "a", "type": "list"}  # Also extract links
            ],
            output_dir="collected_data/web/static"
        )

        print(f"   [OK] Successfully scraped!")
        print(f"   [OK] URL: {scraped_data['url']}")
        print(f"   [OK] Elements extracted: {scraped_data['extracted_elements']}")

        scraper.close()

        # Load extracted data
        output_dir = Path(scraped_data['output_path'])
        extracted_data_file = output_dir / "extracted_data.json"

        with open(extracted_data_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)

        print(f"   [OK] Loaded data: {list(extracted_data.keys())}")

        # ==========================================
        # STEP 2: Send TWO emails for comparison
        # ==========================================
        email_service = create_email_service()

        # Email 1: RAW HTML injection
        print("\n" + "-"*60)
        print("STEP 2a: Sending Email with RAW HTML")
        print("-"*60)

        print("\nGenerating HTML report with raw HTML injection...")
        html_report_raw = create_html_report(scraped_data, extracted_data, use_raw_html=True)
        print(f"   [OK] HTML report created ({len(html_report_raw)} characters)")

        print(f"\nSending email to {recipient_email}...")
        result1 = email_service.send_email(
            to=recipient_email,
            subject="[RAW HTML] Web Scraping Report - example.com",
            content=html_report_raw,
            html=True
        )

        if result1["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Subject: [RAW HTML] Web Scraping Report")

        # Email 2: Plain text (safe mode)
        print("\n" + "-"*60)
        print("STEP 2b: Sending Email with Plain Text (Safe Mode)")
        print("-"*60)

        print("\nGenerating HTML report with plain text...")
        html_report_safe = create_html_report(scraped_data, extracted_data, use_raw_html=False)
        print(f"   [OK] HTML report created ({len(html_report_safe)} characters)")

        print(f"\nSending email to {recipient_email}...")
        result2 = email_service.send_email(
            to=recipient_email,
            subject="[PLAIN TEXT] Web Scraping Report - example.com",
            content=html_report_safe,
            html=True
        )

        if result2["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Subject: [PLAIN TEXT] Web Scraping Report")

        # ==========================================
        # Summary
        # ==========================================
        print("\n" + "="*60)
        print("DEMO COMPLETED!")
        print("="*60)
        print("\nYou should receive TWO emails:")
        print("  1. [RAW HTML] - Shows original HTML with links, formatting")
        print("  2. [PLAIN TEXT] - Shows stripped text for security")
        print("\nCompare them to see the difference!")
        print("\nSecurity Note:")
        print("  - RAW HTML is OK for trusted sites (example.com)")
        print("  - For untrusted sites, ALWAYS sanitize or use plain text")
        print("  - Production systems should use libraries like 'bleach'")
        print("\n")

    except Exception as e:
        print(f"\n   [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
