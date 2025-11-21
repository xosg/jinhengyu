"""
Check full PandaDoc document details
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PANDADOC_API_KEY = os.getenv('PANDADOC_API_KEY')
DOCUMENT_ID = 'NSyquVBRTAHwkqUvBBYnKg'

# Get full document details
response = requests.get(
    f'https://api.pandadoc.com/public/v1/documents/{DOCUMENT_ID}/details',
    headers={'Authorization': f'API-Key {PANDADOC_API_KEY}'}
)

print("Full Document Details:")
print("="*80)
print(json.dumps(response.json(), indent=2))
print("="*80)
