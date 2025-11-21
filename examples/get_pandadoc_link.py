"""
Quick script to get PandaDoc document signing link
"""
import os
import sys
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PANDADOC_API_KEY = os.getenv('PANDADOC_API_KEY')
DOCUMENT_ID = 'cU8iuH2jSSSZgkzuYNLSuD'

def get_document_details():
    """Get document details from PandaDoc"""
    response = requests.get(
        f'https://api.pandadoc.com/public/v1/documents/{DOCUMENT_ID}',
        headers={'Authorization': f'API-Key {PANDADOC_API_KEY}'}
    )

    if response.status_code == 200:
        doc_data = response.json()
        print("Document Details:")
        print(f"  ID: {doc_data.get('id')}")
        print(f"  Name: {doc_data.get('name')}")
        print(f"  Status: {doc_data.get('status')}")
        print(f"  Date Created: {doc_data.get('date_created')}")
        print(f"  Date Sent: {doc_data.get('date_sent')}")
        print()

        # Get recipients
        recipients = doc_data.get('recipients', [])
        print("Recipients:")
        for recipient in recipients:
            print(f"  - {recipient.get('first_name')} {recipient.get('last_name')} ({recipient.get('email')})")
            print(f"    Role: {recipient.get('role')}")
            print(f"    Status: {recipient.get('status', 'N/A')}")

            # Try to get recipient session link
            if recipient.get('id'):
                recipient_id = recipient.get('id')
                session_response = requests.post(
                    f'https://api.pandadoc.com/public/v1/documents/{DOCUMENT_ID}/session',
                    headers={
                        'Authorization': f'API-Key {PANDADOC_API_KEY}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'recipient': recipient.get('email'),
                        'lifetime': 3600  # 1 hour
                    }
                )

                if session_response.status_code == 201:
                    session_data = session_response.json()
                    print(f"    [OK] Signing Link: {session_data.get('id')}")
                    print()
                    return session_data.get('id')
                else:
                    print(f"    [!] Could not get session link: {session_response.status_code}")
                    print(f"        Response: {session_response.text}")

        return None
    else:
        print(f"Error getting document: {response.status_code}")
        print(response.text)
        return None

if __name__ == '__main__':
    print("="*80)
    print("  PandaDoc Document Signing Link")
    print("="*80)
    print()

    signing_link = get_document_details()

    if signing_link:
        print()
        print("="*80)
        print("  COPY THIS LINK TO SIGN THE DOCUMENT:")
        print("="*80)
        print()
        print(f"  {signing_link}")
        print()
        print("="*80)
