"""
Test image download functionality
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.pdf_generator import PDFGenerator
from reportlab.lib.units import inch

def test_image_download():
    pdf_gen = PDFGenerator()

    # Test with different image URLs
    test_urls = [
        ("Google Thumbnail", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRROWXcpPdqfWuO63rxbG82M4CYlE32g-o_Kw&s"),
        ("Reuters OG Image", "https://www.reuters.com/pf/resources/images/reuters/reuters-default.webp?d=331"),
        ("Simple test image", "https://picsum.photos/200/150")
    ]

    for name, test_url in test_urls:
        print(f"\nTesting {name}:")
        print(f"  URL: {test_url}")
        img = pdf_gen._download_image(test_url, max_width=1.5 * inch)

        if img:
            print(f"  [OK] Image downloaded successfully!")
            print(f"  - Width: {img.drawWidth}")
            print(f"  - Height: {img.drawHeight}")
        else:
            print(f"  [ERROR] Image download failed")

if __name__ == "__main__":
    test_image_download()
