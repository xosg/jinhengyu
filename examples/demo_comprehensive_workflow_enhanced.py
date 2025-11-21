"""
Enhanced Comprehensive Multi-API Workflow Demo
Demonstrates maximum features with HTML email, screenshots, and logs

Enhancements:
✓ Custom keyword input
✓ Webpage screenshots using Selenium
✓ Beautiful HTML email with embedded images
✓ Log files attached to email
✓ Reduced to 2 search results for efficiency
"""

import sys
import os
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_integration.search_service import create_search_service
from src.collection.web_scraper import WebScraper
from src.utils.pdf_generator import PDFGenerator
from src.utils.screenshot_service import ScreenshotService
from src.api_integration.storage_service import create_storage_service
from src.api_integration.signature_service import create_signature_service
from src.api_integration.email_service import create_email_service


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_step(step_num, total_steps, text):
    """Print formatted step"""
    print(f"\n[Step {step_num}/{total_steps}] {text}")
    print("-" * 80)


def print_success(text):
    """Print success message"""
    print(f"  [OK] {text}")


def print_info(text):
    """Print info message"""
    print(f"  - {text}")


def print_error(text):
    """Print error message"""
    print(f"  [ERROR] {text}")


def create_html_email(workflow_results, screenshots_data, search_query):
    """Create beautiful HTML email with embedded screenshots"""

    # Prepare screenshot sections
    screenshot_sections = ""
    for idx, screenshot in enumerate(screenshots_data, 1):
        if screenshot.get("status") == "success":
            screenshot_path = screenshot.get("screenshot_path")
            page_title = screenshot.get("page_title", "Webpage")
            url = screenshot.get("url", "")

            # Encode image as base64
            with open(screenshot_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode()

            screenshot_sections += f"""
            <div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3 style="color: #2c3e50; margin-top: 0;">
                    {idx}. {page_title}
                </h3>
                <p style="color: #7f8c8d; font-size: 14px; margin: 10px 0;">
                    <strong>URL:</strong> <a href="{url}" style="color: #3498db;">{url}</a>
                </p>
                <div style="margin: 15px 0; border: 1px solid #ddd; border-radius: 4px; overflow: hidden;">
                    <img src="data:image/png;base64,{img_data}"
                         style="width: 100%; height: auto; display: block;"
                         alt="Screenshot {idx}">
                </div>
            </div>
            """

    # Build HTML email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; margin: 0; font-size: 28px;">
                🚀 Workflow Execution Complete
            </h1>
            <p style="color: #e0e0e0; margin: 10px 0 0 0; font-size: 16px;">
                Multi-API Integration System Report
            </p>
        </div>

        <!-- Main Content Container -->
        <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">

            <!-- Summary Section -->
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px;">
                    📊 Execution Summary
                </h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px; background: #f8f9fa; border: 1px solid #dee2e6; font-weight: bold; width: 40%;">
                            Search Query
                        </td>
                        <td style="padding: 12px; background: white; border: 1px solid #dee2e6;">
                            {search_query}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; background: #f8f9fa; border: 1px solid #dee2e6; font-weight: bold;">
                            Execution Time
                        </td>
                        <td style="padding: 12px; background: white; border: 1px solid #dee2e6;">
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; background: #f8f9fa; border: 1px solid #dee2e6; font-weight: bold;">
                            Success Rate
                        </td>
                        <td style="padding: 12px; background: white; border: 1px solid #dee2e6;">
                            <span style="color: #27ae60; font-weight: bold; font-size: 18px;">
                                {workflow_results.get('success_rate', 'N/A')}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; background: #f8f9fa; border: 1px solid #dee2e6; font-weight: bold;">
                            Steps Completed
                        </td>
                        <td style="padding: 12px; background: white; border: 1px solid #dee2e6;">
                            {workflow_results.get('total_steps_completed', 0)} / 7
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Results Section -->
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px;">
                    ✅ Workflow Results
                </h2>
                <ul style="list-style: none; padding: 0;">
                    <li style="padding: 10px; margin: 8px 0; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px;">
                        <strong>Search Results:</strong> {workflow_results.get('search_results_count', 0)} found
                    </li>
                    <li style="padding: 10px; margin: 8px 0; background: #e3f2fd; border-left: 4px solid #2196f3; border-radius: 4px;">
                        <strong>Web Scraping:</strong> {workflow_results.get('scraped_content_size', 0)} characters extracted
                    </li>
                    <li style="padding: 10px; margin: 8px 0; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px;">
                        <strong>PDF Generated:</strong> {workflow_results.get('pdf_filename', 'N/A')} ({workflow_results.get('pdf_size_kb', 0)} KB)
                    </li>
                    <li style="padding: 10px; margin: 8px 0; background: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 4px;">
                        <strong>Storage:</strong> Uploaded to {workflow_results.get('storage_location', 'N/A')}
                    </li>
                    <li style="padding: 10px; margin: 8px 0; background: #fce4ec; border-left: 4px solid #e91e63; border-radius: 4px;">
                        <strong>E-Signature:</strong> Envelope {workflow_results.get('envelope_id', 'N/A')}
                    </li>
                </ul>
            </div>

            <!-- Screenshots Section -->
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px;">
                    📸 Webpage Screenshots
                </h2>
                {screenshot_sections}
            </div>

            <!-- Steps Completed Section -->
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px;">
                    📋 Steps Completed
                </h2>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    {''.join([f'<div style="padding: 15px; background: #e8f5e9; border-radius: 6px; text-align: center;"><strong>[OK]</strong> {step}</div>' for step in workflow_results.get('steps_completed', [])])}
                </div>
            </div>

        </div>

        <!-- Footer -->
        <div style="text-align: center; margin-top: 30px; padding: 20px; color: #7f8c8d; font-size: 14px;">
            <p style="margin: 5px 0;">
                🤖 This email was automatically generated by the Multi-API Integration System
            </p>
            <p style="margin: 5px 0;">
                Powered by Google Search, PandaDoc, Selenium, and Python
            </p>
            <p style="margin: 15px 0 5px 0; font-size: 12px; color: #95a5a6;">
                📎 Log files are attached to this email for detailed information
            </p>
        </div>

    </body>
    </html>
    """

    return html_content


def main():
    """Main enhanced workflow"""
    print_header("Enhanced Comprehensive Multi-API Integration Workflow")
    print("New Features:")
    print("  [+] Custom keyword input")
    print("  [+] Webpage screenshots (Selenium)")
    print("  [+] Beautiful HTML email")
    print("  [+] Log files attached")

    # Load environment variables
    load_dotenv()

    # Get custom search query from user
    print("\n" + "-" * 80)
    default_query = "Artificial Intelligence applications"
    user_input = input(f"Enter search keywords (or press Enter for default '{default_query}'): ").strip()
    SEARCH_QUERY = user_input if user_input else default_query
    print("-" * 80)

    # Workflow configuration
    TOTAL_STEPS = 7
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("collected_data/comprehensive_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search configuration - reduced to 2 results
    NUM_RESULTS = 2

    # Results tracking
    workflow_results = {
        "started_at": datetime.now().isoformat(),
        "search_query": SEARCH_QUERY,
        "steps_completed": [],
        "errors": [],
        "screenshots": []
    }

    try:
        # =====================================================================
        # STEP 1: Google Search
        # =====================================================================
        print_step(1, TOTAL_STEPS, "Google Custom Search API")

        print_info(f"Search query: '{SEARCH_QUERY}'")
        print_info(f"Requesting {NUM_RESULTS} results")

        search_service = create_search_service()

        try:
            search_results = search_service.search(
                query=SEARCH_QUERY,
                num_results=NUM_RESULTS
            )

            if not search_results or len(search_results) == 0:
                print_error("Search returned no results")
                workflow_results["errors"].append({
                    "step": "search",
                    "error": "No results returned"
                })
                search_results = []
            else:
                print_success(f"Found {len(search_results)} results")
                for idx, result in enumerate(search_results, 1):
                    print_info(f"{idx}. {result.get('title', 'No title')[:60]}...")

                workflow_results["steps_completed"].append("search")
                workflow_results["search_results_count"] = len(search_results)

        except Exception as e:
            print_error(f"Search failed: {str(e)}")
            workflow_results["errors"].append({
                "step": "search",
                "error": str(e)
            })
            search_results = []

        # =====================================================================
        # STEP 2: Web Scraping + Screenshots
        # =====================================================================
        print_step(2, TOTAL_STEPS, "Web Scraping & Screenshots")

        scraped_content = None
        screenshots_data = []

        if search_results:
            target_url = search_results[0].get('url', '') or search_results[0].get('link', '')
            if not target_url:
                print_error("No URL found in search result")
            else:
                print_info(f"Target: {target_url}")
                print_info("Scraping content...")

                scraper = WebScraper()

                try:
                    scrape_result = scraper.scrape_static_site(target_url)

                    if scrape_result.get("status") != "success":
                        print_error(f"Scraping failed: {scrape_result.get('error')}")
                        raise Exception(scrape_result.get('error'))

                    scraped_content = scrape_result
                    text_length = len(scraped_content.get('text', ''))

                    # If no content extracted, try Selenium scraping
                    if text_length < 100:
                        print_info("Low content from static scraper, trying Selenium...")
                        selenium_result = scraper.scrape_with_selenium(target_url)

                        if selenium_result.get("status") == "success":
                            scraped_content = selenium_result
                            text_length = len(scraped_content.get('text', ''))
                            print_success(f"Scraped {text_length} characters (Selenium)")
                        else:
                            print_success(f"Scraped {text_length} characters (static)")
                    else:
                        print_success(f"Scraped {text_length} characters")

                    print_info(f"Title: {scraped_content.get('title', 'N/A')}")

                    workflow_results["steps_completed"].append("scraping")
                    workflow_results["scraped_content_size"] = text_length

                except Exception as scrape_error:
                    # If static scraping fails completely, try Selenium as fallback
                    print_error(f"Static scraping failed: {str(scrape_error)}")
                    print_info("Trying Selenium fallback...")

                    try:
                        selenium_result = scraper.scrape_with_selenium(target_url)

                        if selenium_result.get("status") == "success":
                            scraped_content = selenium_result
                            text_length = len(scraped_content.get('text', ''))
                            print_success(f"Scraped {text_length} characters (Selenium fallback)")
                            print_info(f"Title: {scraped_content.get('title', 'N/A')}")

                            workflow_results["steps_completed"].append("scraping")
                            workflow_results["scraped_content_size"] = text_length
                        else:
                            print_error(f"Selenium also failed: {selenium_result.get('error')}")
                            workflow_results["errors"].append({
                                "step": "scraping",
                                "error": f"Both static and Selenium failed: {str(scrape_error)}"
                            })
                            scraped_content = None
                    except Exception as selenium_error:
                        print_error(f"Selenium fallback failed: {str(selenium_error)}")
                        workflow_results["errors"].append({
                            "step": "scraping",
                            "error": f"All scraping methods failed: {str(scrape_error)}"
                        })
                        scraped_content = None

                # Capture screenshots
                print_info("Capturing webpage screenshots...")
                screenshot_service = ScreenshotService(headless=True)

                for idx, result in enumerate(search_results, 1):
                    url = result.get('url', '') or result.get('link', '')
                    if url:
                        screenshot_path = output_dir / f"screenshot_{idx}_{timestamp}.png"
                        print_info(f"  Capturing: {result.get('title', 'Page')[:50]}...")

                        screenshot_result = screenshot_service.capture_screenshot(
                            url=url,
                            output_path=str(screenshot_path),
                            wait_for_load=5.0  # Increased wait time for better image loading
                        )

                        if screenshot_result.get("status") == "success":
                            print_success(f"  Screenshot saved: {screenshot_path.name}")
                            screenshots_data.append(screenshot_result)
                        else:
                            print_error(f"  Screenshot failed: {screenshot_result.get('error')}")

                if screenshots_data:
                    workflow_results["steps_completed"].append("screenshots")
                    workflow_results["screenshots"] = screenshots_data

        # =====================================================================
        # STEP 3: PDF Generation
        # =====================================================================
        print_step(3, TOTAL_STEPS, "PDF Document Generation")

        pdf_generator = PDFGenerator()
        pdf_filename = f"research_report_{timestamp}.pdf"
        pdf_path = output_dir / pdf_filename

        print_info(f"Generating: {pdf_filename}")

        if search_results:
            pdf_result = pdf_generator.create_combined_document(
                search_query=SEARCH_QUERY,
                search_results=search_results,
                scraped_content=scraped_content,
                output_path=str(pdf_path)
            )
        else:
            print_error("No content available for PDF generation")
            return

        if pdf_result.get("status") != "success":
            print_error(f"PDF generation failed: {pdf_result.get('error')}")
            return

        pdf_size_kb = pdf_path.stat().st_size / 1024
        print_success(f"PDF created: {pdf_filename}")
        print_info(f"Size: {pdf_size_kb:.1f} KB")

        workflow_results["steps_completed"].append("pdf_generation")
        workflow_results["pdf_path"] = str(pdf_path)
        workflow_results["pdf_size_kb"] = round(pdf_size_kb, 1)
        workflow_results["pdf_filename"] = pdf_filename

        # =====================================================================
        # STEP 4: Storage Service
        # =====================================================================
        print_step(4, TOTAL_STEPS, "Storage Service (MinIO)")

        print_info("Uploading PDF to MinIO storage...")

        storage_service = create_storage_service()

        bucket_name = "research-reports"
        bucket_result = storage_service.create_bucket(bucket_name)

        if bucket_result.get("status") == "success":
            print_success(f"Bucket ready: {bucket_name}")

        storage_key = f"reports/{pdf_filename}"
        upload_result = storage_service.upload_file(
            file_path=str(pdf_path),
            bucket=bucket_name,
            key=storage_key
        )

        if upload_result.get("status") == "success":
            print_success(f"Uploaded: {storage_key}")
            workflow_results["steps_completed"].append("storage")
            workflow_results["storage_location"] = f"{bucket_name}/{storage_key}"

        # =====================================================================
        # STEP 5: E-Signature Service
        # =====================================================================
        print_step(5, TOTAL_STEPS, "E-Signature Service (PandaDoc)")

        print_info("Preparing signature envelope...")

        # IMPORTANT: PandaDoc signatures always go to Outlook email
        # (PandaDoc account restriction: can't send to external emails)
        default_email = os.getenv('OUTLOOK_USER', 'demo@example.com')
        print_info(f"Note: PandaDoc signatures sent to organization email only")

        try:
            signature_service = create_signature_service()

            envelope_result = signature_service.create_envelope(
                document_path=str(pdf_path),
                signers=[{
                    "name": "Document Reviewer",
                    "email": default_email,
                    "routing_order": 1
                }],
                subject=f"Research Report: {SEARCH_QUERY}",
                message=f"Please review and sign this research report on '{SEARCH_QUERY}'.",
                metadata={
                    "search_query": SEARCH_QUERY,
                    "workflow": "comprehensive_demo_enhanced",
                    "timestamp": timestamp
                }
            )

            if envelope_result.get("status") == "success":
                envelope_id = envelope_result.get("envelope_id")
                print_success(f"Envelope created: {envelope_id}")
                workflow_results["steps_completed"].append("signature")
                workflow_results["envelope_id"] = envelope_id
            else:
                print_error(f"Envelope creation failed: {envelope_result.get('error')}")

        except Exception as e:
            print_error(f"Signature service error: {str(e)}")

        # =====================================================================
        # STEP 6: Enhanced Email Notification with HTML & Attachments
        # =====================================================================
        print_step(6, TOTAL_STEPS, "Enhanced Email Notification")

        # Get the active email address based on EMAIL_PROVIDER
        email_provider = os.getenv('EMAIL_PROVIDER', 'outlook').lower()
        if email_provider == 'qq':
            active_email = os.getenv('QQMAIL_USER', '')
        else:  # Default to outlook
            active_email = os.getenv('OUTLOOK_USER', '')

        if not active_email:
            print_info("Email credentials not configured - skipping email")
        else:
            try:
                email_service = create_email_service()

                # Create beautiful HTML email
                print_info("Creating HTML email with screenshots...")
                html_content = create_html_email(workflow_results, screenshots_data, SEARCH_QUERY)

                # Prepare attachments: log file and PDF report
                attachments = []

                # Attach log file
                log_file = project_root / "logs" / "api_call_log.jsonl"
                if log_file.exists():
                    attachments.append(str(log_file))
                    print_info(f"Attaching log file: {log_file.name}")

                # Attach PDF research report
                if pdf_path.exists():
                    attachments.append(str(pdf_path))
                    print_info(f"Attaching PDF report: {pdf_path.name}")

                # Send HTML email with attachments
                email_result = email_service.send_email(
                    to=active_email,
                    subject=f"✅ Workflow Complete: {SEARCH_QUERY}",
                    content=html_content,
                    html=True,
                    attachments=attachments
                )

                if email_result.get("status") == "success":
                    print_success(f"HTML email sent to: {active_email}")
                    print_info(f"Provider: {email_provider.upper()} Mail")
                    print_info("  [+] Screenshots embedded in email")
                    print_info(f"  [+] {len(attachments)} attachment(s): {', '.join([Path(a).name for a in attachments])}")
                    workflow_results["steps_completed"].append("email_notification")
                else:
                    print_error(f"Email failed: {email_result.get('error')}")

            except Exception as e:
                print_error(f"Email service error: {str(e)}")

        # =====================================================================
        # STEP 7: Workflow Summary
        # =====================================================================
        print_step(7, TOTAL_STEPS, "Workflow Summary & Results")

        workflow_results["completed_at"] = datetime.now().isoformat()
        workflow_results["total_steps_completed"] = len(workflow_results["steps_completed"])
        workflow_results["success_rate"] = f"{(len(workflow_results['steps_completed']) / TOTAL_STEPS) * 100:.0f}%"

        # Save workflow results
        results_file = output_dir / f"workflow_results_{timestamp}.json"
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_results, f, indent=2, ensure_ascii=False)

        print_success(f"Results saved: {results_file}")

        # Display summary
        print_header("Enhanced Workflow Execution Complete!")

        print("Summary:")
        print(f"  - Search Query: {SEARCH_QUERY}")
        print(f"  - Steps Completed: {workflow_results['total_steps_completed']}/{TOTAL_STEPS}")
        print(f"  - Success Rate: {workflow_results['success_rate']}")
        print(f"  - Screenshots: {len(screenshots_data)} captured")

        print("\nCheck your email for the beautiful HTML report with screenshots!")

        return 0

    except KeyboardInterrupt:
        print("\n\n[!] Workflow interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
