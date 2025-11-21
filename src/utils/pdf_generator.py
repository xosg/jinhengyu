"""
PDF Generator Utility
Converts scraped web content into formatted PDF documents
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


class PDFGenerator:
    """Generate PDF documents from scraped content"""

    def __init__(self, page_size=letter):
        """
        Initialize PDF Generator

        Args:
            page_size: Page size (letter or A4)
        """
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            bold=True
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a4a4a'),
            spaceAfter=20,
            spaceBefore=20
        ))

        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#2a2a2a'),
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=16
        ))

        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#888888'),
            spaceAfter=6
        ))

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text for PDF generation (remove problematic characters)

        Args:
            text: Raw text

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove or replace problematic characters
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('&', '&amp;')

        # Normalize whitespace
        text = ' '.join(text.split())

        return text

    def _download_image(self, url: str, max_width: float = 2.0 * inch) -> Optional[Image]:
        """
        Download image from URL and create ReportLab Image object

        Args:
            url: Image URL
            max_width: Maximum width for the image in PDF

        Returns:
            ReportLab Image object or None if download fails
        """
        try:
            # Download image with timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Create image from bytes
            img_data = io.BytesIO(response.content)
            img = Image(img_data)

            # Resize to fit max_width while maintaining aspect ratio
            aspect_ratio = img.imageHeight / img.imageWidth
            img.drawWidth = max_width
            img.drawHeight = max_width * aspect_ratio

            return img
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None

    def create_from_search_results(self,
                                   search_results: List[Dict[str, Any]],
                                   output_path: str,
                                   title: str = "Search Results Document",
                                   include_metadata: bool = True) -> Dict[str, Any]:
        """
        Create PDF from Google search results

        Args:
            search_results: List of search result dictionaries
            output_path: Path to save PDF
            title: Document title
            include_metadata: Include metadata (date, source, etc.)

        Returns:
            Dictionary with generation result
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for document elements
            story = []

            # Add title
            story.append(Paragraph(self._sanitize_text(title), self.styles['CustomTitle']))
            story.append(Spacer(1, 0.3 * inch))

            # Add metadata
            if include_metadata:
                metadata_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                story.append(Paragraph(metadata_text, self.styles['Metadata']))
                story.append(Paragraph(f"Total Results: {len(search_results)}", self.styles['Metadata']))
                story.append(Spacer(1, 0.3 * inch))

            # Add each search result
            for idx, result in enumerate(search_results, 1):
                # Result number and title
                result_title = result.get('title', 'No Title')
                story.append(Paragraph(
                    f"<b>{idx}. {self._sanitize_text(result_title)}</b>",
                    self.styles['CustomSubtitle']
                ))

                # URL
                url = result.get('link', '')
                if url:
                    story.append(Paragraph(
                        f"<i>URL: {self._sanitize_text(url)}</i>",
                        self.styles['Metadata']
                    ))

                # Snippet/Description
                snippet = result.get('snippet', '')
                if snippet:
                    story.append(Paragraph(
                        self._sanitize_text(snippet),
                        self.styles['CustomBody']
                    ))

                story.append(Spacer(1, 0.2 * inch))

                # Add page break after every 3 results
                if idx % 3 == 0 and idx < len(search_results):
                    story.append(PageBreak())

            # Build PDF
            doc.build(story)

            return {
                "status": "success",
                "output_path": str(output_path),
                "results_count": len(search_results)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def create_from_scraped_content(self,
                                   scraped_data: Dict[str, Any],
                                   output_path: str,
                                   title: Optional[str] = None) -> Dict[str, Any]:
        """
        Create PDF from scraped website content

        Args:
            scraped_data: Dictionary with scraped content (url, title, text, etc.)
            output_path: Path to save PDF
            title: Document title (uses scraped title if not provided)

        Returns:
            Dictionary with generation result
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for document elements
            story = []

            # Add title
            doc_title = title or scraped_data.get('title', 'Scraped Content')
            story.append(Paragraph(self._sanitize_text(doc_title), self.styles['CustomTitle']))
            story.append(Spacer(1, 0.3 * inch))

            # Add metadata
            url = scraped_data.get('url', '')
            if url:
                story.append(Paragraph(
                    f"<i>Source: {self._sanitize_text(url)}</i>",
                    self.styles['Metadata']
                ))

            story.append(Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles['Metadata']
            ))
            story.append(Spacer(1, 0.3 * inch))

            # Add main content
            text_content = scraped_data.get('text', '')
            if text_content:
                # Split into paragraphs
                paragraphs = text_content.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        story.append(Paragraph(
                            self._sanitize_text(para),
                            self.styles['CustomBody']
                        ))
                        story.append(Spacer(1, 0.1 * inch))

            # Build PDF
            doc.build(story)

            return {
                "status": "success",
                "output_path": str(output_path),
                "source_url": url
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def create_combined_document(self,
                                search_query: str,
                                search_results: List[Dict[str, Any]],
                                scraped_content: Optional[Dict[str, Any]],
                                output_path: str) -> Dict[str, Any]:
        """
        Create a comprehensive PDF combining search results and scraped content

        Args:
            search_query: The search query used
            search_results: List of search result dictionaries
            scraped_content: Dictionary with scraped content (optional)
            output_path: Path to save PDF

        Returns:
            Dictionary with generation result
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for document elements
            story = []

            # Add main title
            story.append(Paragraph(
                "Web Research Report",
                self.styles['CustomTitle']
            ))
            story.append(Spacer(1, 0.3 * inch))

            # Add search query
            story.append(Paragraph(
                f"<b>Search Query:</b> {self._sanitize_text(search_query)}",
                self.styles['CustomBody']
            ))
            story.append(Paragraph(
                f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles['Metadata']
            ))
            story.append(Spacer(1, 0.4 * inch))

            # Section 1: Search Results Summary
            story.append(Paragraph(
                "Section 1: Search Results Overview",
                self.styles['CustomSubtitle']
            ))
            story.append(Spacer(1, 0.1 * inch))

            for idx, result in enumerate(search_results[:5], 1):  # Top 5 results
                result_title = result.get('title', 'No Title')
                story.append(Paragraph(
                    f"<b>{idx}. {self._sanitize_text(result_title)}</b>",
                    self.styles['CustomBody']
                ))

                # Try to add thumbnail image from search result
                # Try multiple image sources in order until one succeeds
                img = None
                for img_url in [result.get('og_image'), result.get('image_url'), result.get('thumbnail_url')]:
                    if img_url:
                        img = self._download_image(img_url, max_width=1.5 * inch)
                        if img:
                            break  # Successfully downloaded, stop trying

                if img:
                    story.append(Spacer(1, 0.1 * inch))
                    story.append(img)
                    story.append(Spacer(1, 0.1 * inch))

                url = result.get('link', '')
                if url:
                    story.append(Paragraph(
                        f"<i>{self._sanitize_text(url)}</i>",
                        self.styles['Metadata']
                    ))

                snippet = result.get('snippet', '')
                if snippet:
                    story.append(Paragraph(
                        self._sanitize_text(snippet),
                        self.styles['CustomBody']
                    ))

                story.append(Spacer(1, 0.15 * inch))

            # Section 2: Detailed Content (if available)
            if scraped_content:
                story.append(PageBreak())
                story.append(Paragraph(
                    "Section 2: Detailed Content",
                    self.styles['CustomSubtitle']
                ))
                story.append(Spacer(1, 0.1 * inch))

                # Add scraped content title
                content_title = scraped_content.get('title', '')
                if content_title:
                    story.append(Paragraph(
                        f"<b>{self._sanitize_text(content_title)}</b>",
                        self.styles['CustomBody']
                    ))
                    story.append(Spacer(1, 0.1 * inch))

                # Add source URL
                url = scraped_content.get('url', '')
                if url:
                    story.append(Paragraph(
                        f"<i>Source: {self._sanitize_text(url)}</i>",
                        self.styles['Metadata']
                    ))
                    story.append(Spacer(1, 0.2 * inch))

                # Add content
                text_content = scraped_content.get('text', '')
                if text_content:
                    paragraphs = text_content.split('\n\n')[:10]  # First 10 paragraphs
                    for para in paragraphs:
                        para = para.strip()
                        if para:
                            story.append(Paragraph(
                                self._sanitize_text(para),
                                self.styles['CustomBody']
                            ))
                            story.append(Spacer(1, 0.1 * inch))

            # Add signature section at the end
            story.append(Spacer(1, 0.5 * inch))
            story.append(PageBreak())
            story.append(Paragraph(
                "Signature and Approval",
                self.styles['CustomSubtitle']
            ))
            story.append(Spacer(1, 0.2 * inch))

            story.append(Paragraph(
                "This document has been reviewed and approved by the undersigned.",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 0.4 * inch))

            # Add signature field tag for PandaDoc
            story.append(Paragraph(
                "Signature: {{signature:Signer}}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 0.2 * inch))

            story.append(Paragraph(
                f"Date: ___________________________",
                self.styles['CustomBody']
            ))

            # Build PDF
            doc.build(story)

            return {
                "status": "success",
                "output_path": str(output_path),
                "search_query": search_query,
                "results_count": len(search_results),
                "has_detailed_content": scraped_content is not None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
