"""
Demo script: Combining Module 1 & Module 2 with Website Selection
Scrape web content and email it with screenshots - Choose from multiple sites!

This script demonstrates:
1. Configuration-driven web scraping (multiple sites in YAML)
2. Interactive site selection menu
3. Screenshot capture with Selenium
4. HTML email generation with embedded images
5. Integration of Module 1 (Data Collection) + Module 2 (Email API)

Before running:
- Install dependencies: pip install -r requirements.txt
- Set up .env file with Outlook credentials
- Configure websites in config/collection_config.yaml
"""

import os
import sys
import json
import base64
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection.web_scraper import WebScraper
from src.api_integration.email_service import create_email_service


def load_available_sites(config_path: str = "config/collection_config.yaml"):
    """Load list of available sites from config"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    sites = config.get('web_scraping', {}).get('static_sites', [])
    # Filter only enabled sites
    enabled_sites = [site for site in sites if site.get('enabled', True)]
    return enabled_sites


def show_site_menu():
    """Display simplified menu"""
    print("\n" + "="*60)
    print("AVAILABLE OPTIONS")
    print("="*60)
    print("  1. Search & Scrape (Google API) - Auto-discover websites")
    print("  2. 8values Political Quiz - Auto-complete & screenshot results")
    print("  0. Exit")
    print("="*60)


def create_html_report(scraped_data: dict, extracted_data: dict, screenshot_path: str = None) -> str:
    """
    Create HTML email from scraped data

    Args:
        scraped_data: Data returned from web scraper
        extracted_data: Extracted content from the scraped site
        screenshot_path: Path to screenshot file (optional)

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


def scrape_site(site_config: dict, scraper: WebScraper, google_image_url: str = None):
    """
    Scrape a single site and return results (no email)

    Args:
        site_config: Site configuration dictionary
        scraper: WebScraper instance
        google_image_url: Optional Google thumbnail/image URL to download instead of screenshot
    """

    print("\n" + "="*60)
    print(f"PROCESSING: {site_config['name']}")
    print("="*60)

    try:
        # ==========================================
        # STEP 1: Scrape Website
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 1: Scraping Website (Module 1)")
        print("-"*60)

        print(f"\nScraping {site_config['url']}...")
        scraped_data = scraper.scrape_static_site(
            url=site_config['url'],
            name=site_config['name'],
            extract_elements=site_config.get('extract_elements', []),
            output_dir=site_config.get('output_dir', 'collected_data/web/static')
        )

        print(f"   [OK] Successfully scraped!")
        print(f"   [OK] URL: {scraped_data['url']}")
        print(f"   [OK] Elements extracted: {scraped_data['extracted_elements']}")

        # Load extracted data from file
        output_dir = Path(scraped_data['output_path'])
        extracted_data_file = output_dir / "extracted_data.json"

        with open(extracted_data_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)

        print(f"   [OK] Loaded data: {list(extracted_data.keys())}")

        # ==========================================
        # STEP 2: Get Website Image
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 2: Downloading Google Search Thumbnail")
        print("-"*60)

        screenshot_path = None
        if google_image_url:
            try:
                screenshot_path = output_dir / "screenshot.png"

                # Download Google's thumbnail image
                print(f"\nDownloading thumbnail from Google Search...")
                import requests
                response = requests.get(google_image_url, timeout=10)
                response.raise_for_status()

                with open(screenshot_path, 'wb') as f:
                    f.write(response.content)

                print(f"   [OK] Thumbnail downloaded: {screenshot_path.name}")

                # Get image file size
                image_size_kb = screenshot_path.stat().st_size / 1024
                print(f"   [OK] Image size: {image_size_kb:.1f} KB")
            except Exception as e:
                print(f"   [WARNING] Could not download thumbnail: {str(e)[:80]}")
                screenshot_path = None
        else:
            print(f"\n   [INFO] No Google thumbnail available")
            print(f"   [INFO] Leaving image blank")

        # ==========================================
        # STEP 3: Create HTML Report
        # ==========================================
        print("\n" + "-"*60)
        print("STEP 3: Creating HTML Email Report")
        print("-"*60)

        print("\nGenerating HTML report...")
        html_report = create_html_report(scraped_data, extracted_data, str(screenshot_path) if screenshot_path else None)
        print(f"   [OK] HTML report created ({len(html_report)} characters)")

        # Return results for later processing
        return {
            'success': True,
            'site_config': site_config,
            'scraped_data': scraped_data,
            'extracted_data': extracted_data,
            'screenshot_path': str(screenshot_path) if screenshot_path else None,
            'html_report': html_report
        }

    except Exception as e:
        print(f"\n   [ERROR] Error processing {site_config['name']}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'site_config': site_config,
            'error': str(e)
        }


def create_multi_site_report(results_list, create_attachments=True):
    """
    Create combined HTML report for multiple sites

    Args:
        results_list: List of scraping results
        create_attachments: If True, create metadata JSON files as attachments

    Returns:
        tuple: (html_content, list_of_attachment_paths)
    """
    from datetime import datetime

    # Load multi-site template
    template_path = Path(__file__).parent.parent / "templates" / "email_report_multi.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Prepare attachments directory
    attachments = []
    if create_attachments:
        attachments_dir = Path("collected_data/attachments")
        attachments_dir.mkdir(parents=True, exist_ok=True)

        # Clear old attachments
        for old_file in attachments_dir.glob("*.json"):
            old_file.unlink()

    # Calculate summary stats
    total_sites = len([r for r in results_list if r['success']])
    total_elements = sum(len(r.get('extracted_data', {})) for r in results_list if r['success'])
    total_screenshots = len([r for r in results_list if r['success'] and r.get('screenshot_path')])

    # Build site sections
    site_sections_html = ""

    for idx, result in enumerate(results_list, 1):
        if not result['success']:
            continue

        site_config = result['site_config']
        scraped_data = result['scraped_data']
        extracted_data = result['extracted_data']
        screenshot_path = result.get('screenshot_path')

        # Get timestamp
        import re
        timestamp_match = re.search(r'_(\d{8}_\d{6})', scraped_data.get('output_path', ''))
        timestamp = timestamp_match.group(1).replace('_', ' ') if timestamp_match else 'Unknown'

        # Create metadata attachment for this site
        if create_attachments:
            site_metadata = {
                "site_name": site_config['name'],
                "url": site_config['url'],
                "scraped_at": timestamp,
                "selectors_used": list(extracted_data.keys()),
                "total_elements": len(extracted_data),
                "output_directory": scraped_data.get('output_path', 'N/A'),
                "screenshot_size_kb": round(Path(screenshot_path).stat().st_size / 1024, 2) if screenshot_path and Path(screenshot_path).exists() else 0,
                "extracted_data": extracted_data
            }

            # Save metadata to JSON file
            safe_name = site_config['name'].replace(' ', '_').replace('-', '_')
            metadata_file = attachments_dir / f"{idx}_{safe_name}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(site_metadata, f, indent=2, ensure_ascii=False)

            attachments.append(str(metadata_file))

        # Build content HTML for this site (simplified - show preview only)
        content_html = ""
        preview_count = 0
        for selector, content in extracted_data.items():
            if isinstance(content, list) and len(content) > 0:
                content_html += f"<div><strong>&lt;{selector}&gt;</strong> ({len(content)} items): "
                content_html += f"{str(content[0])[:100]}...</div>"
                preview_count += len(content)
            elif content:
                content_html += f"<div><strong>&lt;{selector}&gt;:</strong> {str(content)[:100]}...</div>"
                preview_count += 1

        if create_attachments:
            content_html += f"<p style='margin-top: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; font-size: 13px;'>"
            content_html += f"📎 <strong>Full data available in attachment:</strong> <code>{idx}_{safe_name}_metadata.json</code>"
            content_html += f"</p>"

        # Build screenshot section
        screenshot_html = ""
        if screenshot_path and Path(screenshot_path).exists():
            with open(screenshot_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                screenshot_data = f"data:image/png;base64,{img_data}"
                screenshot_html = f"""
        <div class="screenshot-box">
            <img src="{screenshot_data}" alt="Screenshot of {site_config['name']}" style="max-width: 100%;">
            <div class="screenshot-caption">Full-page screenshot captured with Selenium WebDriver</div>
        </div>
"""

        # Build this site's section
        site_section = f"""
    <div class="site-section">
        <div class="site-header">
            <h2>{idx}. {site_config['name']}</h2>
            <div class="site-url">🔗 <a href="{site_config['url']}">{site_config['url']}</a></div>
        </div>

        {screenshot_html}

        <div class="content-box">
            <h3>📋 Extracted Content</h3>
            {content_html}
        </div>

        <div class="metadata">
            <strong>Scraped:</strong> {timestamp} |
            <strong>Elements:</strong> {len(extracted_data)}
        </div>
    </div>
"""

        site_sections_html += site_section

        # Add divider between sites (except after last one)
        if idx < total_sites:
            site_sections_html += '<div class="divider"></div>'

    # Create summary attachment
    if create_attachments:
        summary = {
            "report_generated": datetime.now().isoformat(),
            "total_sites_scraped": total_sites,
            "total_elements_extracted": total_elements,
            "total_screenshots_captured": total_screenshots,
            "sites": [
                {
                    "name": r['site_config']['name'],
                    "url": r['site_config']['url'],
                    "success": r['success'],
                    "elements_count": len(r.get('extracted_data', {})) if r['success'] else 0
                }
                for r in results_list
            ]
        }

        summary_file = attachments_dir / "00_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        attachments.insert(0, str(summary_file))  # Put summary first

    # Render final HTML
    html = html_template
    html = html.replace('{{timestamp}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html = html.replace('{{total_sites}}', str(total_sites))
    html = html.replace('{{total_elements}}', str(total_elements))
    html = html.replace('{{total_screenshots}}', str(total_screenshots))
    html = html.replace('{{site_sections}}', site_sections_html)

    return html, attachments


def search_and_scrape(scraper: WebScraper, email_service, search_query: str, num_results: int = 5):
    """
    Use Google Search API to discover websites, then scrape them

    Args:
        scraper: WebScraper instance
        email_service: Email service instance
        search_query: Query to search for
        num_results: Number of search results to process (max 5)

    Returns:
        List of scraping results
    """
    from src.api_integration.search_service import create_search_service

    print("\n" + "="*60)
    print("SMART WEBSITE DISCOVERY (Google Custom Search API)")
    print("="*60)

    try:
        # Initialize Google Search API
        print(f"\nInitializing Google Custom Search API...")
        search_service = create_search_service()
        print(f"   [OK] Connected to Google Search API")

        # Perform search
        print(f"\nSearching Google for: '{search_query}'")
        print(f"   Looking for {num_results} results...")

        search_results = search_service.search(search_query, num_results=num_results)

        if not search_results:
            print(f"   [ERROR] No search results found for '{search_query}'")
            return []

        print(f"   [OK] Found {len(search_results)} websites!")
        print("\n   Discovered websites:")
        for idx, result in enumerate(search_results, 1):
            print(f"      {idx}. {result['title']}")
            print(f"         {result['url']}")

        # Ask user to confirm
        print(f"\n   Ready to scrape {len(search_results)} websites.")
        confirm = input(f"   Continue? (y/n): ").strip().lower()

        if confirm != 'y':
            print("   [CANCELLED] Scraping cancelled by user")
            return []

        # Scrape each discovered website
        print("\n" + "="*60)
        print("SCRAPING DISCOVERED WEBSITES...")
        print("="*60)

        results = []
        for idx, search_result in enumerate(search_results, 1):
            # Create site config for scraper with enriched Google data
            site_config = {
                'name': f"Google Result {idx} - {search_result['display_url']}",
                'url': search_result['url'],
                'extract_elements': [
                    {'selector': 'h1', 'type': 'text'},
                    {'selector': 'h2', 'type': 'list'},
                    {'selector': 'p', 'type': 'list'}
                ],
                'output_dir': 'collected_data/web/google_discovery',
                # Enriched Google Search metadata
                'google_snippet': search_result.get('snippet', ''),
                'google_meta_description': search_result.get('meta_description', ''),
                'google_og_description': search_result.get('og_description', ''),
                'google_formatted_url': search_result.get('formatted_url', ''),
                'google_position': search_result.get('position', idx)
            }

            print(f"\n[{idx}/{len(search_results)}] Processing: {search_result['display_url']}")

            # Use Google thumbnail, then image_url, then og_image, otherwise None
            google_image = (search_result.get('thumbnail_url') or
                          search_result.get('image_url') or
                          search_result.get('og_image'))

            result = scrape_site(site_config, scraper, google_image_url=google_image)
            results.append(result)

            # Small delay between requests
            if idx < len(search_results):
                import time
                time.sleep(1)

        return results

    except Exception as e:
        print(f"\n   [ERROR] Google Search API error: {e}")
        print(f"   Make sure:")
        print(f"     1. GOOGLE_API_KEY is set in .env")
        print(f"     2. GOOGLE_SEARCH_ENGINE_ID is set in .env")
        print(f"     3. Custom Search API is enabled in Google Cloud Console")
        print(f"     4. pip install google-api-python-client")
        return []


def run_8values_quiz(scraper: WebScraper, email_service):
    """
    Automate the 8values political quiz with random answers

    Args:
        scraper: WebScraper instance
        email_service: Email service instance
    """
    import random
    from datetime import datetime

    print("\n" + "="*60)
    print("8VALUES POLITICAL QUIZ AUTOMATION")
    print("="*60)

    quiz_url = "https://8values.github.io/quiz.html"

    try:
        # Initialize browser
        if not scraper.driver:
            scraper._init_driver()

        print(f"\nNavigating to: {quiz_url}")
        scraper.driver.get(quiz_url)

        # Wait for page to load
        import time
        time.sleep(3)

        print(f"   [OK] Quiz page loaded")
        print(f"\nAnswering 70 questions randomly...")

        # Answer all 70 questions
        # The buttons are clickable elements that call next_question(mult)
        # mult values: 1.0 (strongly agree), 0.5 (agree), 0 (neutral), -0.5 (disagree), -1.0 (strongly disagree)
        questions_answered = 0
        max_questions = 70

        for question_num in range(1, max_questions + 1):
            try:
                # Wait for buttons to be available
                time.sleep(0.5)

                # Find all buttons on the page
                # The 8values quiz uses buttons with class="button" and onclick events
                buttons = scraper.driver.find_elements("tag name", "button")

                # Filter for answer buttons (should be 5 buttons per question)
                answer_buttons = [btn for btn in buttons if btn.is_displayed() and btn.get_attribute("onclick")]

                if len(answer_buttons) >= 5:
                    # Pick a random button (0-4 for the 5 answer options)
                    chosen_button = random.choice(answer_buttons)

                    # Scroll to the button to ensure it's visible
                    scraper.driver.execute_script("arguments[0].scrollIntoView(true);", chosen_button)
                    time.sleep(0.2)

                    # Use JavaScript click to avoid interception
                    scraper.driver.execute_script("arguments[0].click();", chosen_button)

                    questions_answered += 1

                    # Progress indicator every 10 questions
                    if question_num % 10 == 0:
                        print(f"   Progress: {question_num}/70 questions answered")

                    # Small delay between questions
                    time.sleep(0.3)
                else:
                    # No more answer buttons found, quiz is complete
                    break

            except Exception as e:
                # Quiz might be finished or page structure changed
                print(f"   [INFO] Stopped at question {question_num} (quiz complete or error: {str(e)[:50]})")
                break

        print(f"   [OK] Answered {questions_answered} questions")

        # Wait for results page to load
        print(f"\nWaiting for results...")
        time.sleep(5)

        # Take screenshot of results
        print(f"\nCapturing results screenshot...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("collected_data/8values")
        output_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = output_dir / f"8values_results_{timestamp}.png"
        scraper.driver.save_screenshot(str(screenshot_path))

        screenshot_size_kb = screenshot_path.stat().st_size / 1024
        print(f"   [OK] Screenshot saved: {screenshot_path.name}")
        print(f"   [OK] Size: {screenshot_size_kb:.1f} KB")

        # Create simple HTML email with results
        print(f"\nCreating email report...")

        # Convert screenshot to base64
        with open(screenshot_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
            screenshot_data = f"data:image/png;base64,{img_data}"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                .info {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .screenshot {{ text-align: center; margin: 20px 0; }}
                .screenshot img {{ max-width: 100%; border: 2px solid #ddd; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>8values Political Quiz Results</h1>

                <div class="info">
                    <p><strong>Quiz URL:</strong> <a href="{quiz_url}">{quiz_url}</a></p>
                    <p><strong>Questions Answered:</strong> {questions_answered}/70 (random selections)</p>
                    <p><strong>Completed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="screenshot">
                    <h2>Your Political Compass</h2>
                    <img src="{screenshot_data}" alt="8values Quiz Results">
                </div>

                <div class="footer">
                    <p>🤖 Generated automatically with Claude Code</p>
                    <p>This quiz was completed with randomly selected answers for demonstration purposes.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email
        print(f"\nSending email report...")
        recipient_email = os.getenv('OUTLOOK_USER')

        email_result = email_service.send_email(
            to=recipient_email,
            subject=f"8values Political Quiz Results - {timestamp}",
            content=html_content,
            html=True
        )

        if email_result["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Subject: {email_result['subject']}")
        else:
            print(f"   [ERROR] Failed to send email: {email_result.get('error')}")

        print("\n" + "="*60)
        print("8VALUES QUIZ COMPLETED!")
        print("="*60)
        print(f"\nAnswered {questions_answered} questions with random selections")
        print(f"Screenshot saved to: {screenshot_path}")
        print(f"Check your email inbox for the results!")

    except Exception as e:
        print(f"\n   [ERROR] Quiz automation failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run interactive demo with simplified menu"""
    print("\n" + "="*60)
    print("COMBINED DEMO: Web Scraping + API Integration")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Check credentials
    if not os.getenv('OUTLOOK_USER') or not os.getenv('OUTLOOK_PASSWORD'):
        print("\n   [ERROR] Outlook credentials not found!")
        print("   Please set OUTLOOK_USER and OUTLOOK_PASSWORD in .env file")
        return

    # Show menu and get selection
    while True:
        show_site_menu()

        try:
            choice = input("\nSelect an option (number): ").strip()

            if choice == '0':
                print("\nExiting...")
                return

            choice_num = int(choice)

            if choice_num == 1:
                # Search & Scrape mode
                print(f"\n[OK] Launching Search & Scrape...")
                break
            elif choice_num == 2:
                # 8values Quiz
                print(f"\n[OK] Launching 8values Quiz...")
                break
            else:
                print(f"\n[ERROR] Invalid choice. Please enter 0, 1, or 2")
        except ValueError:
            print("\n[ERROR] Please enter a number")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return

    # Initialize services
    scraper = WebScraper()
    email_service = create_email_service()

    # Handle choice
    if choice_num == 1:
        # Ask for search query
        print("\n" + "="*60)
        print("Enter search query (e.g., 'Python tutorials')")
        search_query = input("Query: ").strip()

        if not search_query:
            print("[ERROR] Empty query. Exiting...")
            scraper.close()
            return

        # Ask for number of results
        try:
            num_str = input("Number of results to scrape (1-5, default 5): ").strip()
            num_results = int(num_str) if num_str else 5
            num_results = max(1, min(num_results, 5))  # Clamp between 1-5
        except ValueError:
            num_results = 5
            print(f"[INFO] Using default: {num_results} results")

        # Execute search and scrape
        results = search_and_scrape(scraper, email_service, search_query, num_results)

        scraper.close()

        # Count successful scrapes
        success_count = len([r for r in results if r['success']])

        if success_count == 0:
            print("\n   [ERROR] No sites were scraped successfully. Cannot send email.")
            return

        # ==========================================
        # Send Email
        # ==========================================
        print("\n" + "="*60)
        print("SENDING EMAIL REPORT...")
        print("="*60)

        recipient_email = os.getenv('OUTLOOK_USER')

        # Send combined report with attachments
        print(f"\nCreating combined report for {success_count} sites...")
        combined_html, attachments = create_multi_site_report(results, create_attachments=True)
        print(f"   [OK] Combined report created ({len(combined_html)} characters)")
        print(f"   [OK] Created {len(attachments)} metadata attachment(s)")

        # List attachments
        for att in attachments:
            filename = Path(att).name
            size_kb = Path(att).stat().st_size / 1024
            print(f"       - {filename} ({size_kb:.1f} KB)")

        print(f"\nSending combined report to {recipient_email}...")
        email_result = email_service.send_email(
            to=recipient_email,
            subject=f"Google Search & Scrape Report - {success_count} Websites",
            content=combined_html,
            html=True,
            attachments=attachments
        )

        if email_result["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Subject: {email_result['subject']}")
            print(f"   [OK] All {success_count} sites included in ONE email")
            print(f"   [OK] {len(attachments)} attachments included")
        else:
            print(f"   [ERROR] Failed to send email: {email_result.get('error')}")

        print("\n" + "="*60)
        print("SEARCH & SCRAPE COMPLETED!")
        print("="*60)
        print(f"\nProcessed {len(results)} Google-discovered site(s)")
        print(f"Successfully scraped {success_count} site(s)")
        print(f"Sent 1 combined report with {success_count} websites")
        print("\nCheck your email inbox for the HTML report!")

    elif choice_num == 2:
        # Run 8values quiz
        run_8values_quiz(scraper, email_service)
        scraper.close()


if __name__ == "__main__":
    main()
