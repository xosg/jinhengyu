"""
Base classes for API integration services

This module defines abstract base classes for all third-party API services.
This allows easy swapping between different providers (e.g., Gmail SMTP <-> SendGrid)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path


class BaseEmailService(ABC):
    """Abstract base class for email sending services"""

    @abstractmethod
    def send_email(self, to: str, subject: str, content: str,
                   from_email: Optional[str] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None,
                   html: bool = False) -> Dict[str, Any]:
        """
        Send an email

        Args:
            to: Recipient email address
            subject: Email subject
            content: Email body (plain text or HTML)
            from_email: Sender email (optional, uses default if not specified)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of file paths to attach (optional)
            html: If True, content is treated as HTML

        Returns:
            Dictionary with send result {"status": "success|error", "message_id": "...", ...}
        """
        pass

    @abstractmethod
    def send_bulk_email(self, recipients: List[str], subject: str, content: str,
                       from_email: Optional[str] = None,
                       html: bool = False) -> Dict[str, Any]:
        """
        Send email to multiple recipients

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            content: Email body
            from_email: Sender email (optional)
            html: If True, content is treated as HTML

        Returns:
            Dictionary with send results {"total": N, "successful": N, "failed": N, ...}
        """
        pass

    @abstractmethod
    def validate_email(self, email: str) -> bool:
        """
        Validate email address format

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        pass


class BaseStorageService(ABC):
    """Abstract base class for object storage services"""

    @abstractmethod
    def upload_file(self, file_path: str, bucket: str, key: str,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to storage

        Args:
            file_path: Local file path
            bucket: Bucket/container name
            key: Object key (path in storage)
            metadata: Optional metadata dictionary

        Returns:
            Dictionary with upload result {"status": "success|error", "url": "...", ...}
        """
        pass

    @abstractmethod
    def download_file(self, bucket: str, key: str, local_path: str) -> Dict[str, Any]:
        """
        Download a file from storage

        Args:
            bucket: Bucket/container name
            key: Object key (path in storage)
            local_path: Local file path to save to

        Returns:
            Dictionary with download result
        """
        pass

    @abstractmethod
    def delete_file(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Delete a file from storage

        Args:
            bucket: Bucket/container name
            key: Object key (path in storage)

        Returns:
            Dictionary with delete result
        """
        pass

    @abstractmethod
    def list_files(self, bucket: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in storage

        Args:
            bucket: Bucket/container name
            prefix: Optional prefix to filter by

        Returns:
            List of file information dictionaries
        """
        pass

    @abstractmethod
    def get_file_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """
        Get a presigned URL for file access

        Args:
            bucket: Bucket/container name
            key: Object key (path in storage)
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL string
        """
        pass


class BaseSignatureService(ABC):
    """Abstract base class for electronic signature services"""

    @abstractmethod
    def create_envelope(self, document_path: str, signers: List[Dict[str, str]],
                       subject: str, message: str,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a signature envelope (document + signers)

        Args:
            document_path: Path to document to sign
            signers: List of signer dictionaries [{"name": "...", "email": "..."}, ...]
            subject: Email subject for signature request
            message: Email message for signature request
            metadata: Optional metadata

        Returns:
            Dictionary with envelope info {"envelope_id": "...", "status": "...", ...}
        """
        pass

    @abstractmethod
    def get_envelope_status(self, envelope_id: str) -> Dict[str, Any]:
        """
        Get status of a signature envelope

        Args:
            envelope_id: Envelope ID

        Returns:
            Dictionary with status info
        """
        pass

    @abstractmethod
    def download_signed_document(self, envelope_id: str, output_path: str) -> Dict[str, Any]:
        """
        Download signed document

        Args:
            envelope_id: Envelope ID
            output_path: Local path to save document

        Returns:
            Dictionary with download result
        """
        pass

    @abstractmethod
    def void_envelope(self, envelope_id: str, reason: str) -> Dict[str, Any]:
        """
        Void/cancel a signature envelope

        Args:
            envelope_id: Envelope ID
            reason: Reason for voiding

        Returns:
            Dictionary with void result
        """
        pass


class BaseSearchService(ABC):
    """Abstract base class for search services"""

    @abstractmethod
    def search(self, query: str, num_results: int = 10,
              language: str = "en", region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform a search query

        Args:
            query: Search query string
            num_results: Number of results to return
            language: Language code (e.g., "en", "zh")
            region: Region code for localized results (optional)

        Returns:
            List of search result dictionaries [{"title": "...", "url": "...", "snippet": "..."}, ...]
        """
        pass

    @abstractmethod
    def search_images(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for images

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of image result dictionaries
        """
        pass


class BaseMailService(ABC):
    """Abstract base class for physical mail services"""

    @abstractmethod
    def send_letter(self, to_address: Dict[str, str], from_address: Dict[str, str],
                   content: str, color: bool = False) -> Dict[str, Any]:
        """
        Send a physical letter

        Args:
            to_address: Recipient address {"name": "...", "street": "...", "city": "...", "state": "...", "zip": "..."}
            from_address: Sender address (same format)
            content: Letter content (plain text or HTML)
            color: If True, print in color

        Returns:
            Dictionary with send result
        """
        pass

    @abstractmethod
    def send_postcard(self, to_address: Dict[str, str], from_address: Dict[str, str],
                     front_image: str, back_message: str) -> Dict[str, Any]:
        """
        Send a postcard

        Args:
            to_address: Recipient address
            from_address: Sender address
            front_image: Path to front image
            back_message: Message on back

        Returns:
            Dictionary with send result
        """
        pass

    @abstractmethod
    def track_mail(self, mail_id: str) -> Dict[str, Any]:
        """
        Track mail delivery status

        Args:
            mail_id: Mail tracking ID

        Returns:
            Dictionary with tracking info
        """
        pass
