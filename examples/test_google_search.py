"""
Quick test of Google Custom Search API integration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_integration.search_service import create_search_service

def main():
    print("\n" + "="*60)
    print("TESTING GOOGLE CUSTOM SEARCH API")
    print("="*60)

    # Load environment variables
    load_dotenv()

    # Check credentials
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

    print(f"\nChecking credentials...")
    print(f"   API Key: {'[OK] Found' if api_key else '[ERROR] Missing'}")
    print(f"   Search Engine ID: {'[OK] Found' if search_engine_id else '[ERROR] Missing'}")

    if not api_key or not search_engine_id:
        print("\n[ERROR] Missing Google API credentials!")
        print("Please update your .env file with:")
        print("  GOOGLE_API_KEY=your_api_key")
        print("  GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id")
        return

    try:
        # Initialize search service
        print(f"\nInitializing Google Custom Search API...")
        search_service = create_search_service()
        print(f"   [OK] Connected successfully!")

        # Perform test search
        test_query = "Python web scraping"
        print(f"\nSearching for: '{test_query}'")
        print(f"   Requesting 5 results...")

        results = search_service.search(test_query, num_results=5)

        if not results:
            print(f"\n   [ERROR] No results found!")
            return

        print(f"   [OK] Found {len(results)} results!")

        # Display results
        print("\n" + "="*60)
        print("SEARCH RESULTS")
        print("="*60)

        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Snippet: {result['snippet'][:100]}...")

        print("\n" + "="*60)
        print("TEST PASSED!")
        print("="*60)
        print("\nYour Google Custom Search API is working correctly!")
        print("You can now use option 7 in demo_combined_menu.py")
        print("\n")

    except Exception as e:
        print(f"\n   [ERROR] Test failed: {e}")
        print(f"\n   Troubleshooting:")
        print(f"     1. Check your API key is correct")
        print(f"     2. Check your Search Engine ID is correct")
        print(f"     3. Make sure Custom Search API is enabled:")
        print(f"        https://console.cloud.google.com/apis/library/customsearch.googleapis.com")
        print(f"     4. Check you haven't exceeded the 100 queries/day limit")


if __name__ == "__main__":
    main()
