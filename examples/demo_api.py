"""
Demo script for Module 2: API Integration Engine

This script demonstrates:
1. Email sending (Outlook SMTP)
2. Object storage (Mock S3)
3. Electronic signatures (Mock DocuSign)
4. Search (Mock Google Search)

Before running:
- Install dependencies: pip install -r requirements.txt
- Set up .env file with Outlook credentials
- Update config/api_config.yaml if needed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_integration.email_service import create_email_service
from src.api_integration.storage_service import create_storage_service
from src.api_integration.signature_service import create_signature_service
from src.api_integration.search_service import create_search_service


def demo_email_service():
    """Demo email sending functionality"""
    print("\n" + "="*60)
    print("DEMO 1: Email Service (Outlook SMTP)")
    print("="*60)

    # Check if credentials are set
    if not os.getenv('OUTLOOK_USER') or not os.getenv('OUTLOOK_PASSWORD'):
        print("\n   [WARNING] Outlook credentials not found in environment!")
        print("   Please set OUTLOOK_USER and OUTLOOK_PASSWORD in .env file")
        print("   Skipping email service demo...")
        return

    try:
        email_service = create_email_service()

        print("\n1. Sending test email to yourself...")
        result = email_service.send_email(
            to=os.getenv('OUTLOOK_USER'),
            subject="Test Email from API Integration Module",
            content="Hello! This is a test email from the API integration module.\n\nIf you receive this, the email service is working correctly!",
            html=False
        )

        if result["status"] == "success":
            print(f"   [OK] Email sent successfully!")
            print(f"   [OK] Recipient: {result['to']}")
            print(f"   [OK] Subject: {result['subject']}")
        else:
            print(f"   [ERROR] Error: {result.get('error')}")

        print("\n2. Validating email addresses...")
        test_emails = [
            "valid@example.com",
            "invalid-email",
            "another.valid@test.org"
        ]
        for test_email in test_emails:
            is_valid = email_service.validate_email(test_email)
            status = "[OK] Valid" if is_valid else "[ERROR] Invalid"
            print(f"   {status}: {test_email}")

    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def demo_storage_service():
    """Demo object storage functionality"""
    print("\n" + "="*60)
    print("DEMO 2: Storage Service (Mock S3)")
    print("="*60)

    try:
        storage_service = create_storage_service()

        # Create a test file
        test_dir = Path("collected_data/test_files")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "test_document.txt"
        test_file.write_text("This is a test document for storage demo.\nCreated: " + str(Path(__file__).name))

        print(f"\n1. Uploading file to storage...")
        result = storage_service.upload_file(
            file_path=str(test_file),
            bucket="demo-bucket",
            key="documents/test_document.txt",
            metadata={"uploaded_by": "demo_script", "category": "test"}
        )

        if result["status"] == "success":
            print(f"   [OK] File uploaded successfully!")
            print(f"   [OK] Bucket: {result['bucket']}")
            print(f"   [OK] Key: {result['key']}")
            print(f"   [OK] URL: {result['url']}")
        else:
            print(f"   [ERROR] Error: {result.get('error')}")

        print(f"\n2. Listing files in bucket...")
        files = storage_service.list_files(bucket="demo-bucket")
        print(f"   [OK] Found {len(files)} file(s):")
        for file in files[:5]:  # Show first 5
            print(f"      - {file['key']} ({file['size_mb']} MB)")

        print(f"\n3. Generating presigned URL...")
        url = storage_service.get_file_url(
            bucket="demo-bucket",
            key="documents/test_document.txt",
            expires_in=3600
        )
        print(f"   [OK] URL: {url}")

        print(f"\n4. Downloading file...")
        download_path = test_dir / "downloaded_test.txt"
        result = storage_service.download_file(
            bucket="demo-bucket",
            key="documents/test_document.txt",
            local_path=str(download_path)
        )

        if result["status"] == "success":
            print(f"   [OK] File downloaded to: {result['local_path']}")
        else:
            print(f"   [ERROR] Error: {result.get('error')}")

    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def demo_signature_service():
    """Demo electronic signature functionality"""
    print("\n" + "="*60)
    print("DEMO 3: Signature Service (Mock DocuSign)")
    print("="*60)

    try:
        signature_service = create_signature_service()

        # Create a test document
        test_dir = Path("collected_data/test_files")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_doc = test_dir / "contract.txt"
        test_doc.write_text("""
SAMPLE CONTRACT

This is a sample contract document for electronic signature demonstration.

Party A: Company ABC
Party B: Individual XYZ

Both parties agree to the terms and conditions outlined herein.

Signature Required Below:
________________________
        """)

        print(f"\n1. Creating signature envelope...")
        result = signature_service.create_envelope(
            document_path=str(test_doc),
            signers=[
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Smith", "email": "jane@example.com"}
            ],
            subject="Please sign: Sample Contract",
            message="Please review and sign the attached contract.",
            metadata={"contract_type": "demo", "priority": "normal"}
        )

        if result["status"] == "success":
            envelope_id = result["envelope_id"]
            print(f"   [OK] Envelope created successfully!")
            print(f"   [OK] Envelope ID: {envelope_id}")
            print(f"   [OK] Status: {result['envelope_status']}")
            print(f"   [OK] Signers: {len(result['signers'])}")

            print(f"\n2. Checking envelope status...")
            status_result = signature_service.get_envelope_status(envelope_id)
            if status_result["status"] == "success":
                print(f"   [OK] Envelope Status: {status_result['envelope_status']}")
                print(f"   [OK] Created: {status_result['created_at']}")
                print(f"   Note: In real DocuSign, you'd wait for signers to complete")

            print(f"\n3. Simulating signed document download...")
            print(f"   Note: Mocking completion for demo purposes...")
            print(f"   [OK] In production, you'd check status and download when completed")

        else:
            print(f"   [ERROR] Error: {result.get('error')}")

    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def demo_search_service():
    """Demo search functionality"""
    print("\n" + "="*60)
    print("DEMO 4: Search Service (Mock Google Search)")
    print("="*60)

    try:
        search_service = create_search_service()

        print(f"\n1. Performing web search...")
        results = search_service.search(
            query="Python data collection",
            num_results=5
        )
        print(f"   [OK] Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"      {i}. {result['title']}")
            print(f"         URL: {result['url']}")
            print(f"         Snippet: {result['snippet'][:80]}...")
            print()

        print(f"\n2. Performing image search...")
        results = search_service.search_images(
            query="Python logo",
            num_results=3
        )
        print(f"   [OK] Found {len(results)} image results:")
        for i, result in enumerate(results, 1):
            print(f"      {i}. {result['title']}")
            print(f"         Image URL: {result['url']}")
            print(f"         Dimensions: {result['width']}x{result['height']}")

    except Exception as e:
        print(f"   [ERROR] Error: {e}")


def demo_pluggable_architecture():
    """Demonstrate how easy it is to swap providers"""
    print("\n" + "="*60)
    print("DEMO 5: Pluggable Architecture")
    print("="*60)

    print("""
    The architecture uses abstract base classes, making it easy to swap providers:

    1. Email Service:
       - Current: GmailSMTP (free)
       - Future: Switch to SendGrid by changing config:
         email_service:
           provider: "SendGrid"

    2. Storage Service:
       - Current: MockS3 (local filesystem)
       - Future: Switch to AWS S3 by changing config:
         storage_service:
           provider: "AWSS3"

    3. Signature Service:
       - Current: MockDocuSign (simulated)
       - Future: Switch to real DocuSign by changing config:
         signature_service:
           provider: "DocuSign"

    4. Search Service:
       - Current: MockGoogleSearch (simulated)
       - Future: Switch to real Google Search API:
         search_service:
           provider: "GoogleSearch"

    All services implement the same interface (BaseXXXService),
    so your code doesn't need to change - just update the config!
    """)


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("MODULE 2: API INTEGRATION ENGINE - DEMO")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Run demos
    demo_email_service()
    demo_storage_service()
    demo_signature_service()
    demo_search_service()
    demo_pluggable_architecture()

    print("\n" + "="*60)
    print("DEMO COMPLETED!")
    print("="*60)
    print("\nCheck the following for results:")
    print("  - collected_data/mock_s3/       (storage files)")
    print("  - collected_data/signatures/    (signature envelopes)")
    print("  - logs/api_call_log.jsonl       (API call logs)")
    print("\n")


if __name__ == "__main__":
    main()
