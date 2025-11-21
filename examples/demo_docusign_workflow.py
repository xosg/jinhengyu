"""
DocuSign E-Signature Workflow Demo
Complete workflow: Google Search → Web Scrape → Generate PDF → DocuSign Signature

This demo demonstrates:
1. Using Google Custom Search API to find relevant information
2. Scraping content from a search result
3. Generating a professional PDF document from the scraped content
4. Sending the PDF for signature via DocuSign

Requirements:
- Set up Google Custom Search API credentials (GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID)
- Set up DocuSign credentials (DOCUSIGN_INTEGRATION_KEY, DOCUSIGN_USER_ID, etc.)
- Update config/api_config.yaml to set signature_service provider to "DocuSign"
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
from src.api_integration.signature_service import create_signature_service


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_step(step_num, text):
    """Print formatted step"""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)


def main():
    """Main demo workflow"""
    print_header("DocuSign E-Signature Workflow Demo")
    print("This demo demonstrates the complete workflow:")
    print("  1. Google Search for relevant information")
    print("  2. Scrape content from a search result")
    print("  3. Generate professional PDF document")
    print("  4. Send document for signature via DocuSign")

    # Load environment variables
    load_dotenv()

    # Check if required credentials are set
    print("\nChecking credentials...")
    required_env_vars = [
        'GOOGLE_API_KEY',
        'GOOGLE_SEARCH_ENGINE_ID',
        'DOCUSIGN_INTEGRATION_KEY',
        'DOCUSIGN_USER_ID',
        'DOCUSIGN_ACCOUNT_ID',
        'DOCUSIGN_PRIVATE_KEY_PATH'
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file.")
        print("See .env.example for details on how to obtain these credentials.")
        return

    print("✓ All required credentials found")

    # Get user input for demo
    print("\n" + "=" * 80)
    print("Demo Configuration")
    print("=" * 80)

    # Search query
    search_query = input("\nEnter search query (or press Enter for default): ").strip()
    if not search_query:
        search_query = "python programming best practices"
        print(f"Using default: '{search_query}'")

    # Signer email
    signer_email = input("\nEnter signer email address (where DocuSign request will be sent): ").strip()
    if not signer_email:
        print("❌ ERROR: Signer email is required")
        return

    signer_name = input("Enter signer name: ").strip()
    if not signer_name:
        signer_name = "Document Reviewer"
        print(f"Using default: '{signer_name}'")

    # Output directory
    output_dir = Path("collected_data/docusign_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # =====================================================================
        # STEP 1: Google Search
        # =====================================================================
        print_step(1, "Performing Google Search")

        search_service = create_search_service()
        print(f"Search query: '{search_query}'")
        print("Searching...")

        search_result = search_service.search(
            query=search_query,
            num_results=5
        )

        if search_result.get("status") != "success":
            print(f"❌ Search failed: {search_result.get('error')}")
            return

        results = search_result.get("results", [])
        print(f"✓ Found {len(results)} results")

        # Display top 3 results
        print("\nTop search results:")
        for idx, result in enumerate(results[:3], 1):
            print(f"  {idx}. {result.get('title', 'No title')}")
            print(f"     {result.get('link', 'No URL')}")

        # =====================================================================
        # STEP 2: Scrape Content from First Result
        # =====================================================================
        print_step(2, "Scraping Content from Top Result")

        if not results:
            print("❌ No search results to scrape")
            return

        target_url = results[0].get('link', '')
        print(f"Scraping: {target_url}")

        scraper = WebScraper()
        scraped_result = scraper.scrape_static_site(target_url)

        if scraped_result.get("status") != "success":
            print(f"⚠ Scraping failed: {scraped_result.get('error')}")
            print("Continuing with search results only...")
            scraped_content = None
        else:
            scraped_content = scraped_result
            text_preview = scraped_result.get('text', '')[:200]
            print(f"✓ Scraped {len(scraped_result.get('text', ''))} characters")
            print(f"\nPreview: {text_preview}...")

        # =====================================================================
        # STEP 3: Generate PDF Document
        # =====================================================================
        print_step(3, "Generating PDF Document")

        pdf_generator = PDFGenerator()
        pdf_filename = f"research_report_{timestamp}.pdf"
        pdf_path = output_dir / pdf_filename

        print(f"Creating PDF: {pdf_path}")

        # Generate combined PDF with search results and scraped content
        pdf_result = pdf_generator.create_combined_document(
            search_query=search_query,
            search_results=results,
            scraped_content=scraped_content,
            output_path=str(pdf_path)
        )

        if pdf_result.get("status") != "success":
            print(f"❌ PDF generation failed: {pdf_result.get('error')}")
            return

        print(f"✓ PDF created successfully")
        print(f"  Path: {pdf_path}")
        print(f"  Size: {pdf_path.stat().st_size / 1024:.1f} KB")

        # =====================================================================
        # STEP 4: Send for Signature via DocuSign
        # =====================================================================
        print_step(4, "Sending Document for Signature via DocuSign")

        # Create signature service
        # NOTE: Make sure to set provider to "DocuSign" in config/api_config.yaml
        try:
            signature_service = create_signature_service()
        except Exception as e:
            print(f"❌ Failed to initialize DocuSign service: {e}")
            print("\nTips:")
            print("  1. Ensure 'provider: DocuSign' in config/api_config.yaml")
            print("  2. Verify all DocuSign credentials in .env file")
            print("  3. Check private key file path is correct")
            return

        # Prepare envelope details
        subject = f"Please Review: {search_query.title()}"
        message = (
            f"Hello {signer_name},\n\n"
            f"Please review and sign the attached research report on '{search_query}'.\n\n"
            f"This document contains:\n"
            f"- Search results overview\n"
            f"- Detailed content from top result\n\n"
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Please review and provide your signature."
        )

        signers = [
            {
                "name": signer_name,
                "email": signer_email,
                "routing_order": 1
            }
        ]

        print(f"\nSending to: {signer_email}")
        print(f"Subject: {subject}")
        print("\nCreating DocuSign envelope...")

        # Create envelope
        envelope_result = signature_service.create_envelope(
            document_path=str(pdf_path),
            signers=signers,
            subject=subject,
            message=message,
            metadata={
                "search_query": search_query,
                "generated_at": datetime.now().isoformat(),
                "source": "docusign_workflow_demo"
            }
        )

        if envelope_result.get("status") != "success":
            print(f"❌ Failed to create envelope: {envelope_result.get('error')}")
            return

        envelope_id = envelope_result.get("envelope_id")
        print(f"✓ DocuSign envelope created successfully!")
        print(f"\n  Envelope ID: {envelope_id}")
        print(f"  Status: {envelope_result.get('envelope_status')}")
        print(f"  Sent to: {signer_email}")

        # =====================================================================
        # Summary
        # =====================================================================
        print_header("Workflow Completed Successfully!")

        print("Summary:")
        print(f"  • Search Query: {search_query}")
        print(f"  • Results Found: {len(results)}")
        print(f"  • PDF Generated: {pdf_filename}")
        print(f"  • DocuSign Envelope: {envelope_id}")
        print(f"  • Sent to: {signer_email}")
        print(f"\n✓ {signer_name} will receive an email from DocuSign with signing instructions")

        print("\nNext Steps:")
        print(f"  1. Check {signer_email} inbox for DocuSign email")
        print("  2. Click the 'Review Document' button in the email")
        print("  3. Review and sign the document")
        print("  4. You'll receive a confirmation when signing is complete")

        print(f"\nYou can check envelope status anytime with:")
        print(f"  envelope_id = '{envelope_id}'")
        print("  status = signature_service.get_envelope_status(envelope_id)")

    except KeyboardInterrupt:
        print("\n\n⚠ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
