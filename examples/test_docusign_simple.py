"""
Simple DocuSign Test Script
Tests basic DocuSign integration without dependencies on search/scrape

This script will:
1. Check your DocuSign credentials
2. Create a simple test PDF
3. Send it for signature to an email you specify

Run this BEFORE trying the full workflow demo.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.pdf_generator import PDFGenerator
from src.api_integration.signature_service import create_signature_service


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def main():
    """Main test function"""
    print_header("DocuSign Simple Integration Test")

    # Load environment variables
    load_dotenv()

    # Check credentials
    print("Step 1: Checking DocuSign Credentials")
    print("-" * 80)

    required_vars = {
        'DOCUSIGN_INTEGRATION_KEY': os.getenv('DOCUSIGN_INTEGRATION_KEY'),
        'DOCUSIGN_USER_ID': os.getenv('DOCUSIGN_USER_ID'),
        'DOCUSIGN_ACCOUNT_ID': os.getenv('DOCUSIGN_ACCOUNT_ID'),
        'DOCUSIGN_PRIVATE_KEY_PATH': os.getenv('DOCUSIGN_PRIVATE_KEY_PATH')
    }

    missing = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            print(f"  ❌ {var_name}: NOT SET")
            missing.append(var_name)
        else:
            # Mask sensitive values
            display_value = var_value
            if 'KEY' in var_name and len(var_value) > 10:
                display_value = var_value[:8] + "..." + var_value[-4:]
            print(f"  ✓ {var_name}: {display_value}")

    if missing:
        print(f"\n❌ ERROR: Missing required environment variables!")
        print("Please set these in your .env file.")
        print("\nSee DOCUSIGN_SETUP_GUIDE.md for detailed setup instructions.")
        return

    # Check private key file exists
    private_key_path = required_vars['DOCUSIGN_PRIVATE_KEY_PATH']
    if not os.path.exists(private_key_path):
        print(f"\n❌ ERROR: Private key file not found at: {private_key_path}")
        print("\nPlease:")
        print("  1. Go to DocuSign Developer portal")
        print("  2. Generate RSA keypair")
        print("  3. Download private key")
        print("  4. Update DOCUSIGN_PRIVATE_KEY_PATH in .env")
        return

    print(f"  ✓ Private key file found: {private_key_path}")
    print("\n✓ All credentials configured!")

    # Check config file
    print("\nStep 2: Checking Configuration")
    print("-" * 80)

    import yaml
    config_path = project_root / "config" / "api_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    provider = config.get('signature_service', {}).get('provider', '')
    print(f"  Signature service provider: {provider}")

    if provider != "DocuSign":
        print(f"\n⚠️  WARNING: Provider is set to '{provider}'")
        print("  For this test, we need to use real DocuSign.")
        print("\n  To fix: Edit config/api_config.yaml and change:")
        print("    signature_service:")
        print("      provider: \"DocuSign\"")
        print("\n  Would you like to continue anyway? (y/n): ", end='')

        response = input().strip().lower()
        if response != 'y':
            print("  Test cancelled.")
            return

    # Get signer information
    print("\nStep 3: Configure Test Envelope")
    print("-" * 80)

    signer_email = input("Enter email address to send test document to: ").strip()
    if not signer_email:
        print("❌ ERROR: Email address is required")
        return

    signer_name = input("Enter signer name (or press Enter for 'Test Signer'): ").strip()
    if not signer_name:
        signer_name = "Test Signer"

    print(f"\n  Signer: {signer_name} <{signer_email}>")

    # Create output directory
    output_dir = Path("collected_data/docusign_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create test PDF
        print("\nStep 4: Creating Test PDF")
        print("-" * 80)

        pdf_generator = PDFGenerator()
        pdf_filename = f"test_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = output_dir / pdf_filename

        # Create a simple test document
        test_data = {
            'title': 'DocuSign Integration Test Document',
            'url': 'https://example.com',
            'text': '''This is a test document to verify DocuSign integration.

Purpose:
This document is used to test the DocuSign e-signature integration in the Multi-Source Data Collection & API Integration System.

Test Details:
- Integration Key: c05831ad-c8a1-462c-a0f0-eb273e69d096
- Test Date: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''
- Environment: DocuSign Demo/Sandbox

Instructions:
If you receive this document via DocuSign email:
1. Click the "Review Document" button
2. Review the document content
3. Click to add your signature
4. Submit the signed document

Expected Outcome:
Upon successful signing, you should receive a completion confirmation, and the signed document will be available for download.

This test confirms that the DocuSign integration is working correctly.'''
        }

        result = pdf_generator.create_from_scraped_content(
            scraped_data=test_data,
            output_path=str(pdf_path),
            title="DocuSign Integration Test"
        )

        if result.get("status") != "success":
            print(f"❌ Failed to create PDF: {result.get('error')}")
            return

        print(f"  ✓ PDF created: {pdf_filename}")
        print(f"  ✓ Size: {pdf_path.stat().st_size / 1024:.1f} KB")

        # Initialize DocuSign service
        print("\nStep 5: Initializing DocuSign Service")
        print("-" * 80)
        print("  Connecting to DocuSign API...")
        print("  Authenticating with JWT...")

        try:
            signature_service = create_signature_service()
            print("  ✓ Successfully connected to DocuSign!")
        except Exception as e:
            print(f"\n❌ Failed to initialize DocuSign service:")
            print(f"  Error: {e}")
            print("\nCommon causes:")
            print("  1. Consent not granted - see DOCUSIGN_SETUP_GUIDE.md Step 3")
            print("  2. Invalid Account ID - check your DocuSign admin panel")
            print("  3. Private key file is incorrect or corrupted")
            print("\nCheck the logs/api_call_log.jsonl file for more details.")
            return

        # Create and send envelope
        print("\nStep 6: Creating DocuSign Envelope")
        print("-" * 80)

        subject = "DocuSign Integration Test - Please Sign"
        message = f"""Hello {signer_name},

This is a test document to verify DocuSign integration.

Please review and sign this document to complete the test.

This is sent from the Multi-Source Data Collection & API Integration System.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        signers = [
            {
                "name": signer_name,
                "email": signer_email,
                "routing_order": 1
            }
        ]

        print(f"  Creating envelope...")
        print(f"  Document: {pdf_filename}")
        print(f"  Recipient: {signer_email}")

        envelope_result = signature_service.create_envelope(
            document_path=str(pdf_path),
            signers=signers,
            subject=subject,
            message=message,
            metadata={
                "test_type": "simple_integration_test",
                "timestamp": datetime.now().isoformat()
            }
        )

        if envelope_result.get("status") != "success":
            print(f"\n❌ Failed to create envelope:")
            print(f"  Error: {envelope_result.get('error')}")

            # Additional troubleshooting info
            if 'response_body' in envelope_result:
                print(f"\n  API Response: {envelope_result.get('response_body')}")

            return

        # Success!
        envelope_id = envelope_result.get("envelope_id")

        print_header("✓ Test Successful!")

        print("DocuSign envelope created and sent successfully!")
        print(f"\n  Envelope ID: {envelope_id}")
        print(f"  Status: {envelope_result.get('envelope_status')}")
        print(f"  Recipient: {signer_email}")
        print(f"  Document: {pdf_filename}")

        print("\nNext Steps:")
        print(f"  1. Check the inbox of {signer_email}")
        print("  2. You should receive an email from DocuSign")
        print("  3. Click 'Review Document' in the email")
        print("  4. Sign the document")
        print("  5. You'll receive a confirmation email")

        print("\n✓ Your DocuSign integration is working correctly!")
        print("\nYou can now run the full workflow demo:")
        print("  python examples/demo_docusign_workflow.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("\nCheck logs/api_call_log.jsonl for detailed error information.")


if __name__ == "__main__":
    main()
