"""
Email Service Implementation
Supports Gmail SMTP (free) - easily swappable to SendGrid or other providers
"""

import os
import json
import smtplib
import re
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, List, Optional, Any

import yaml

from .base import BaseEmailService


class GmailSMTPService(BaseEmailService):
    """Gmail SMTP email service (free)"""

    def __init__(self, config_path: str = "config/api_config.yaml", config_key: str = 'gmail_smtp'):
        """
        Initialize Gmail SMTP service

        Args:
            config_path: Path to YAML configuration file
            config_key: Config key to read from (gmail_smtp or qqmail_smtp)
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get SMTP configuration (works for both Gmail and QQ Mail)
        email_config = self.config.get('email_service', {})
        smtp_config = email_config.get(config_key, {})

        self.smtp_server = smtp_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = smtp_config.get('smtp_port', 587)
        self.use_tls = smtp_config.get('use_tls', True)
        self.use_ssl = smtp_config.get('use_ssl', False)  # For QQ Mail (port 465)
        self.username = self._resolve_env_var(smtp_config.get('username', ''))
        self.password = self._resolve_env_var(smtp_config.get('password', ''))
        self.default_sender = self._resolve_env_var(smtp_config.get('default_sender', self.username))
        self.provider_name = config_key.replace('_smtp', '').upper()

        # Settings
        settings = email_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 30)
        self.max_recipients = settings.get('max_recipients', 50)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "email_service",
            "provider": self.provider_name,
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def send_email(self, to: str, subject: str, content: str,
                   from_email: Optional[str] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None,
                   html: bool = False) -> Dict[str, Any]:
        """
        Send an email via Gmail SMTP

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
            Dictionary with send result
        """
        # Validate recipient
        if not self.validate_email(to):
            return {"status": "error", "error": "Invalid recipient email address"}

        # Use default sender if not specified
        if from_email is None:
            from_email = self.default_sender

        self._log("send_email", "started", {
            "to": to,
            "subject": subject,
            "from": from_email,
            "has_attachments": bool(attachments)
        })

        # Retry logic
        for attempt in range(self.retry_attempts):
            try:
                # Create message
                if attachments:
                    msg = MIMEMultipart()
                else:
                    msg = MIMEMultipart('alternative') if html else MIMEText(content)

                if isinstance(msg, MIMEMultipart):
                    msg['From'] = from_email
                    msg['To'] = to
                    msg['Subject'] = subject

                    if cc:
                        msg['Cc'] = ', '.join(cc)
                    if bcc:
                        msg['Bcc'] = ', '.join(bcc)

                    # Attach body
                    if html:
                        msg.attach(MIMEText(content, 'html'))
                    else:
                        msg.attach(MIMEText(content, 'plain'))

                    # Attach files
                    if attachments:
                        for file_path in attachments:
                            self._attach_file(msg, file_path)
                else:
                    msg['From'] = from_email
                    msg['To'] = to
                    msg['Subject'] = subject

                # Build recipient list
                recipients = [to]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                # Connect and send
                if self.use_ssl:
                    # Use SMTP_SSL for SSL connections (QQ Mail port 465)
                    try:
                        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                            server.login(self.username, self.password)
                            server.sendmail(from_email, recipients, msg.as_string())
                    except smtplib.SMTPResponseException as e:
                        # QQ Mail sometimes sends garbage during disconnect, but email is sent
                        if e.smtp_code == -1:
                            pass  # Ignore disconnect errors, email was already sent
                        else:
                            raise
                else:
                    # Use SMTP with STARTTLS for TLS connections (Gmail, Outlook port 587)
                    with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                        if self.use_tls:
                            server.starttls()
                        server.login(self.username, self.password)
                        server.sendmail(from_email, recipients, msg.as_string())

                result = {
                    "status": "success",
                    "to": to,
                    "subject": subject,
                    "message_id": f"gmail_{datetime.now().timestamp()}"
                }

                self._log("send_email", "success", result)
                return result

            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    continue  # Retry
                else:
                    import traceback
                    error_result = {
                        "status": "error",
                        "to": to,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                        "attempts": attempt + 1
                    }
                    self._log("send_email", "error", error_result)
                    return error_result

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to email message"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read())
            attachment.add_header('Content-Disposition', 'attachment', filename=file_path.name)
            msg.attach(attachment)

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
            Dictionary with send results
        """
        if len(recipients) > self.max_recipients:
            return {
                "status": "error",
                "error": f"Too many recipients (max: {self.max_recipients})"
            }

        self._log("send_bulk_email", "started", {
            "total_recipients": len(recipients),
            "subject": subject
        })

        results = {
            "total": len(recipients),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        for recipient in recipients:
            result = self.send_email(
                to=recipient,
                subject=subject,
                content=content,
                from_email=from_email,
                html=html
            )

            if result["status"] == "success":
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "recipient": recipient,
                "status": result["status"]
            })

        self._log("send_bulk_email", "completed", {
            "total": results["total"],
            "successful": results["successful"],
            "failed": results["failed"]
        })

        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results


# Factory function to create email service based on config
def create_email_service(config_path: str = "config/api_config.yaml") -> BaseEmailService:
    """
    Factory function to create email service based on configuration

    The provider is determined by EMAIL_PROVIDER environment variable in .env:
    - "outlook" -> Uses Outlook SMTP
    - "qq" -> Uses QQ Mail SMTP
    - If not set, falls back to config file

    Args:
        config_path: Path to configuration file

    Returns:
        Email service instance
    """
    # Check environment variable for dynamic provider switching
    env_provider = os.getenv('EMAIL_PROVIDER', '').lower()

    # Map environment variable to provider names
    provider_map = {
        'outlook': 'OutlookSMTP',
        'qq': 'QQMailSMTP',
        'gmail': 'GmailSMTP'
    }

    # Use environment variable if set, otherwise fall back to config
    if env_provider in provider_map:
        provider = provider_map[env_provider]
    else:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        provider = config.get('email_service', {}).get('provider', 'OutlookSMTP')

    if provider == 'GmailSMTP':
        return GmailSMTPService(config_path, config_key='gmail_smtp')
    elif provider == 'QQMailSMTP':
        return GmailSMTPService(config_path, config_key='qqmail_smtp')
    elif provider == 'OutlookSMTP':
        return GmailSMTPService(config_path, config_key='outlook_smtp')
    # elif provider == 'SendGrid':
    #     return SendGridService(config_path)  # Future implementation
    else:
        raise ValueError(f"Unknown email service provider: {provider}")
