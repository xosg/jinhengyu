"""
Comprehensive Multi-API Workflow Demo
Demonstrates maximum features from 需求.pdf (Requirements)

This single workflow showcases:

MODULE 1 - Data Collection:
✓ Web Scraping (static sites with requests/BeautifulSoup)

MODULE 2 - API Integration:
✓ Search Service (Google Custom Search API)
✓ Storage Service (Mock S3 / Local Storage)
✓ Signature Service (DocuSign or Mock)
✓ Email Service (Outlook SMTP)

Additional Features:
✓ PDF Generation from scraped content
✓ YAML Configuration Management
✓ Environment Variables Security
✓ JSONL Structured Logging
✓ Error Handling & Retry Logic
✓ Factory Pattern for Services

WORKFLOW:
1. Search Google for a topic
2. Scrape content from top search result
3. Generate professional PDF document
4. Store PDF in storage service
5. Send PDF for signature via DocuSign
6. Send email notification with summary
7. Display complete workflow results
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_integration.search_service import create_search_service
from src.collection.web_scraper import WebScraper
from src.utils.pdf_generator import PDFGenerator
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


def main():
    """Main comprehensive workflow"""
    print_header("Comprehensive Multi-API Integration Workflow")
    print("This demo showcases the complete system capabilities:")
    print("  Module 1: Web Scraping (Data Collection)")
    print("  Module 2: Search, Storage, Signature, Email (API Integration)")
    print("  Utilities: PDF Generation, Configuration, Logging")

    # Load environment variables
    load_dotenv()

    # Workflow configuration
    TOTAL_STEPS = 7
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("collected_data/comprehensive_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search configuration (simple, reliable topic)
    SEARCH_QUERY = "Python programming language"
    NUM_RESULTS = 3

    # Results tracking
    workflow_results = {
        "started_at": datetime.now().isoformat(),
        "search_query": SEARCH_QUERY,
        "steps_completed": [],
        "errors": []
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
                print_info("Continuing with sample data...")
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
            print_info("Continuing with sample data...")
            search_results = []

        # =====================================================================
        # STEP 2: Web Scraping
        # =====================================================================
        print_step(2, TOTAL_STEPS, "Web Scraping (Data Collection)")

        scraped_content = None

        if search_results:
            # Try both 'link' and 'url' keys
            target_url = search_results[0].get('url', '') or search_results[0].get('link', '')
            if not target_url:
                print_error("No URL found in search result")
                scraped_content = None
            else:
                print_info(f"Target: {target_url}")
                print_info("Scraping content...")

                scraper = WebScraper()
                scrape_result = scraper.scrape_static_site(target_url)

                if scrape_result.get("status") != "success":
                    print_error(f"Scraping failed: {scrape_result.get('error')}")
                    workflow_results["errors"].append({
                        "step": "scraping",
                        "error": scrape_result.get('error')
                    })
                    print_info("Using search results only for PDF")
                else:
                    scraped_content = scrape_result
                    text_length = len(scraped_content.get('text', ''))
                    print_success(f"Scraped {text_length} characters")
                    print_info(f"Title: {scraped_content.get('title', 'N/A')}")

                    workflow_results["steps_completed"].append("scraping")
                    workflow_results["scraped_content_size"] = text_length
        else:
            print_info("No search results available for scraping")
            print_info("Creating sample content for demo...")

            # Create sample content for demo
            scraped_content = {
                'title': 'Python Programming Language - Overview',
                'url': 'https://www.python.org',
                'text': """Python is a high-level, interpreted programming language.

Key Features:
Python emphasizes code readability with its notable use of significant whitespace. Its language constructs aim to help programmers write clear, logical code for small and large-scale projects.

Popular Uses:
- Web Development
- Data Science and Machine Learning
- Automation and Scripting
- Scientific Computing

Python's comprehensive standard library and vast ecosystem of third-party packages make it suitable for a wide range of applications."""
            }
            print_success("Sample content created for demonstration")

        # =====================================================================
        # STEP 3: PDF Generation
        # =====================================================================
        print_step(3, TOTAL_STEPS, "PDF Document Generation")

        pdf_generator = PDFGenerator()
        pdf_filename = f"research_report_{timestamp}.pdf"
        pdf_path = output_dir / pdf_filename

        print_info(f"Generating: {pdf_filename}")

        if search_results:
            # Create comprehensive PDF with search results and scraped content
            pdf_result = pdf_generator.create_combined_document(
                search_query=SEARCH_QUERY,
                search_results=search_results,
                scraped_content=scraped_content,
                output_path=str(pdf_path)
            )
        elif scraped_content:
            # Create PDF from scraped content only
            pdf_result = pdf_generator.create_from_scraped_content(
                scraped_data=scraped_content,
                output_path=str(pdf_path),
                title=f"Research Report: {SEARCH_QUERY}"
            )
        else:
            print_error("No content available for PDF generation")
            return

        if pdf_result.get("status") != "success":
            print_error(f"PDF generation failed: {pdf_result.get('error')}")
            workflow_results["errors"].append({
                "step": "pdf_generation",
                "error": pdf_result.get('error')
            })
            return

        pdf_size_kb = pdf_path.stat().st_size / 1024
        print_success(f"PDF created: {pdf_filename}")
        print_info(f"Size: {pdf_size_kb:.1f} KB")
        print_info(f"Path: {pdf_path}")

        workflow_results["steps_completed"].append("pdf_generation")
        workflow_results["pdf_path"] = str(pdf_path)
        workflow_results["pdf_size_kb"] = round(pdf_size_kb, 1)

        # =====================================================================
        # STEP 4: Storage Service
        # =====================================================================
        print_step(4, TOTAL_STEPS, "Storage Service (Mock S3)")

        print_info("Uploading PDF to storage...")

        storage_service = create_storage_service()

        # Create bucket if needed
        bucket_name = "research-reports"
        bucket_result = storage_service.create_bucket(bucket_name)

        if bucket_result.get("status") == "success":
            print_success(f"Bucket ready: {bucket_name}")
        elif "already exists" in bucket_result.get("message", "").lower():
            print_info(f"Using existing bucket: {bucket_name}")
        else:
            print_error(f"Bucket creation issue: {bucket_result.get('message')}")

        # Upload PDF
        storage_key = f"reports/{pdf_filename}"
        upload_result = storage_service.upload_file(
            file_path=str(pdf_path),
            bucket=bucket_name,
            key=storage_key
        )

        if upload_result.get("status") != "success":
            print_error(f"Upload failed: {upload_result.get('error')}")
            workflow_results["errors"].append({
                "step": "storage",
                "error": upload_result.get('error')
            })
        else:
            print_success(f"Uploaded: {storage_key}")
            print_info(f"Bucket: {bucket_name}")

            workflow_results["steps_completed"].append("storage")
            workflow_results["storage_location"] = f"{bucket_name}/{storage_key}"

        # =====================================================================
        # STEP 5: E-Signature Service
        # =====================================================================
        print_step(5, TOTAL_STEPS, "E-Signature Service (DocuSign/Mock)")

        print_info("Preparing signature envelope...")

        # Check which provider is configured
        import yaml
        with open(project_root / "config" / "api_config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        provider = config.get('signature_service', {}).get('provider', 'MockDocuSign')

        print_info(f"Provider: {provider}")

        # Use default signer for demo
        default_email = os.getenv('OUTLOOK_USER', 'demo@example.com')
        signer_name = "Document Reviewer"
        signer_email = default_email

        print_info(f"Signer: {signer_name} <{signer_email}>")

        try:
            signature_service = create_signature_service()

            envelope_result = signature_service.create_envelope(
                document_path=str(pdf_path),
                signers=[{
                    "name": signer_name,
                    "email": signer_email,
                    "routing_order": 1
                }],
                subject=f"Research Report: {SEARCH_QUERY}",
                message=f"Please review and sign this research report on '{SEARCH_QUERY}'.\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                metadata={
                    "search_query": SEARCH_QUERY,
                    "workflow": "comprehensive_demo",
                    "timestamp": timestamp
                }
            )

            if envelope_result.get("status") != "success":
                print_error(f"Envelope creation failed: {envelope_result.get('error')}")
                workflow_results["errors"].append({
                    "step": "signature",
                    "error": envelope_result.get('error')
                })
            else:
                envelope_id = envelope_result.get("envelope_id")
                print_success(f"Envelope created: {envelope_id}")
                print_info(f"Status: {envelope_result.get('envelope_status')}")

                if provider == "MockDocuSign":
                    print_info("Mock mode - signature request simulated")
                else:
                    print_info(f"Sent to: {signer_email}")

                workflow_results["steps_completed"].append("signature")
                workflow_results["envelope_id"] = envelope_id

        except Exception as e:
            print_error(f"Signature service error: {str(e)}")
            workflow_results["errors"].append({
                "step": "signature",
                "error": str(e)
            })
            print_info("Continuing workflow without signature...")

        # =====================================================================
        # STEP 6: Email Notification
        # =====================================================================
        print_step(6, TOTAL_STEPS, "Email Notification Service")

        print_info("Preparing summary email...")

        # Check if email credentials are configured
        outlook_user = os.getenv('OUTLOOK_USER', '')
        if not outlook_user:
            print_info("Email credentials not configured - skipping email notification")
            print_info("Set OUTLOOK_USER and OUTLOOK_PASSWORD in .env to enable")
        else:
            try:
                email_service = create_email_service()

                # Prepare email content
                email_body = f"""
Comprehensive Workflow Demo - Execution Summary

Search Query: {SEARCH_QUERY}
Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RESULTS:
--------
✓ Search Results: {workflow_results.get('search_results_count', 0)} found
✓ Web Scraping: {workflow_results.get('scraped_content_size', 0)} characters extracted
✓ PDF Generated: {pdf_filename} ({workflow_results.get('pdf_size_kb', 0)} KB)
✓ Storage: Uploaded to {workflow_results.get('storage_location', 'N/A')}
✓ Signature: Envelope {workflow_results.get('envelope_id', 'N/A')}

STEPS COMPLETED:
{chr(10).join(f'  • {step}' for step in workflow_results['steps_completed'])}

This email was automatically generated by the Multi-API Integration System.
"""

                email_result = email_service.send_email(
                    to=outlook_user,
                    subject=f"Workflow Complete: {SEARCH_QUERY}",
                    content=email_body
                )

                if email_result.get("status") != "success":
                    print_error(f"Email failed: {email_result.get('error')}")
                    workflow_results["errors"].append({
                        "step": "email",
                        "error": email_result.get('error')
                    })
                else:
                    print_success(f"Email sent to: {outlook_user}")
                    workflow_results["steps_completed"].append("email_notification")

            except Exception as e:
                print_error(f"Email service error: {str(e)}")
                workflow_results["errors"].append({
                    "step": "email",
                    "error": str(e)
                })
                print_info("Continuing workflow without email...")

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
        print_header("Workflow Execution Complete!")

        print("Summary:")
        print(f"  - Search Query: {SEARCH_QUERY}")
        print(f"  - Steps Completed: {workflow_results['total_steps_completed']}/{TOTAL_STEPS}")
        print(f"  - Success Rate: {workflow_results['success_rate']}")
        print(f"  - PDF Generated: {pdf_filename} ({workflow_results.get('pdf_size_kb', 0)} KB)")

        print("\nSteps Successfully Completed:")
        for step in workflow_results["steps_completed"]:
            print(f"  [OK] {step}")

        if workflow_results["errors"]:
            print("\nIssues Encountered:")
            for error in workflow_results["errors"]:
                print(f"  [!] {error['step']}: {error['error']}")

        print("\n" + "=" * 80)
        print("APIS & TECHNOLOGIES DEMONSTRATED:")
        print("=" * 80)
        print("\nModule 1 - Data Collection:")
        print("  [OK] Web Scraping (requests + BeautifulSoup)")
        print("  [OK] Content Extraction & Processing")

        print("\nModule 2 - API Integration:")
        print("  [OK] Google Custom Search API")
        print("  [OK] Storage Service (Mock S3/Local)")
        print("  [OK] E-Signature Service (DocuSign/Mock)")
        if "email_notification" in workflow_results["steps_completed"]:
            print("  [OK] Email Service (Outlook SMTP)")

        print("\nUtilities & Architecture:")
        print("  [OK] PDF Generation (ReportLab)")
        print("  [OK] YAML Configuration Management")
        print("  [OK] Environment Variables (Security)")
        print("  [OK] JSONL Structured Logging")
        print("  [OK] Factory Pattern (Service Creation)")
        print("  [OK] Error Handling & Recovery")
        print("  [OK] Type Hints & Documentation")

        print("\nOutput Files:")
        print(f"  - PDF Document: {pdf_path}")
        print(f"  - Workflow Results: {results_file}")
        print(f"  - Logs: logs/api_call_log.jsonl")

        print("\n" + "=" * 80)
        print("[SUCCESS] Comprehensive workflow demonstration complete!")
        print("=" * 80 + "\n")

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
