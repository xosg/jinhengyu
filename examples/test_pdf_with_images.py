"""
Test PDF generation with images from search results
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.api_integration.search_service import GoogleSearchService
from src.utils.pdf_generator import PDFGenerator

# Load environment variables
load_dotenv()

def test_pdf_with_images():
    # Step 1: Perform a search
    print("\n[Step 1] Performing Google Search...")
    search_service = GoogleSearchService()
    results = search_service.search("technology news", num_results=2)

    if not results:
        print(f"  [ERROR] Search failed: No results returned")
        return

    print(f"  [OK] Found {len(results)} results")

    # Check for images in search results
    print("\n[Step 2] Checking for images in search results...")
    for idx, result in enumerate(results, 1):
        print(f"\n  Result {idx}: {result.get('title', 'N/A')[:50]}...")

        # Check for pre-extracted image fields
        thumbnail_url = result.get('thumbnail_url')
        image_url = result.get('image_url')
        og_image = result.get('og_image')

        if thumbnail_url:
            print(f"    Thumbnail URL: {thumbnail_url[:80]}...")
        if image_url:
            print(f"    Image URL: {image_url[:80]}...")
        if og_image:
            print(f"    OG Image URL: {og_image[:80]}...")

        if not (thumbnail_url or image_url or og_image):
            print(f"    [WARNING] No images found for this result")

    # Step 3: Generate PDF with images
    print("\n[Step 3] Generating PDF with images...")
    pdf_gen = PDFGenerator()

    output_path = project_root / "collected_data" / "test_pdf_with_images.pdf"

    result = pdf_gen.create_combined_document(
        search_query="technology news",
        search_results=results,
        scraped_content=None,
        output_path=str(output_path)
    )

    if result['status'] == 'success':
        print(f"  [OK] PDF created: {result['output_path']}")

        # Check file size
        file_size = output_path.stat().st_size / 1024
        print(f"  [OK] File size: {file_size:.1f} KB")

        if file_size > 10:
            print("  [OK] File size suggests images were included!")
        else:
            print("  [WARNING] File size is small - images may not have been included")
    else:
        print(f"  [ERROR] PDF generation failed: {result.get('error')}")

if __name__ == "__main__":
    test_pdf_with_images()
