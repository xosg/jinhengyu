"""
Email Monitor Module
Monitors email inbox via IMAP and downloads attachments
"""

import os
import imaplib
import email
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.header import decode_header

import yaml


class EmailMonitor:
    """Email monitoring via IMAP (supports Gmail, Outlook, etc.)"""

    def __init__(self, config_path: str = "config/collection_config.yaml"):
        """
        Initialize email monitor with configuration

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.mail = None
        self._setup_logging()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/collection_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "email_monitor",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def connect(self):
        """Connect to IMAP server"""
        email_config = self.config.get('email_monitoring', {})

        server = email_config.get('imap_server', 'imap.gmail.com')
        port = email_config.get('imap_port', 993)
        username = self._resolve_env_var(email_config.get('username', ''))
        password = self._resolve_env_var(email_config.get('password', ''))

        self._log("connect", "started", {"server": server, "port": port, "username": username})

        try:
            # Connect to IMAP server
            self.mail = imaplib.IMAP4_SSL(server, port)
            self.mail.login(username, password)

            self._log("connect", "success", {"server": server, "username": username})
            return True

        except Exception as e:
            self._log("connect", "error", {"error": str(e)})
            raise

    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass
            self.mail = None

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def fetch_emails_by_filters(self) -> Dict[str, Any]:
        """
        Fetch emails for all enabled filters in config

        Returns:
            Dictionary with fetch results
        """
        filters = self.config.get('email_monitoring', {}).get('filters', [])
        results = {
            "total_filters": 0,
            "successful": 0,
            "failed": 0,
            "total_emails_fetched": 0,
            "total_attachments_downloaded": 0,
            "details": []
        }

        # Connect once for all filters
        self.connect()

        try:
            for filter_config in filters:
                if not filter_config.get('enabled', True):
                    continue

                results["total_filters"] += 1
                try:
                    filter_result = self.fetch_emails(filter_config)
                    results["successful"] += 1
                    results["total_emails_fetched"] += filter_result.get("emails_fetched", 0)
                    results["total_attachments_downloaded"] += filter_result.get("attachments_downloaded", 0)
                    results["details"].append(filter_result)
                except Exception as e:
                    results["failed"] += 1
                    self._log("fetch_emails_by_filters", "error", {
                        "filter": filter_config.get('name'),
                        "error": str(e)
                    })
        finally:
            self.disconnect()

        return results

    def fetch_emails(self, filter_config: Dict) -> Dict[str, Any]:
        """
        Fetch emails based on filter configuration

        Args:
            filter_config: Filter configuration dictionary

        Returns:
            Dictionary with fetch results
        """
        filter_name = filter_config.get('name', 'Unknown Filter')
        self._log("fetch_emails", "started", {"filter": filter_name})

        try:
            # Select inbox
            self.mail.select('INBOX')

            # Build search criteria
            search_criteria = self._build_search_criteria(filter_config)

            # Search for emails
            status, messages = self.mail.search(None, *search_criteria)
            if status != 'OK':
                raise Exception(f"Search failed: {status}")

            email_ids = messages[0].split()
            total_emails = len(email_ids)

            self._log("fetch_emails", "found", {
                "filter": filter_name,
                "total_emails": total_emails
            })

            # Process each email
            emails_processed = 0
            attachments_downloaded = 0
            output_dir = Path(filter_config.get('output_dir', 'collected_data/email'))
            output_dir.mkdir(parents=True, exist_ok=True)

            for email_id in email_ids:
                try:
                    email_data = self._fetch_single_email(email_id)

                    # Save email content
                    email_file = self._save_email_content(email_data, output_dir)

                    # Download attachments if enabled
                    if filter_config.get('download_attachments', True):
                        attachment_types = filter_config.get('attachment_types', [])
                        downloaded = self._download_attachments(
                            email_data,
                            output_dir,
                            attachment_types
                        )
                        attachments_downloaded += downloaded

                    emails_processed += 1

                except Exception as e:
                    self._log("fetch_single_email", "error", {
                        "email_id": email_id.decode(),
                        "error": str(e)
                    })
                    continue

            result = {
                "filter": filter_name,
                "status": "success",
                "emails_found": total_emails,
                "emails_fetched": emails_processed,
                "attachments_downloaded": attachments_downloaded,
                "output_dir": str(output_dir)
            }

            self._log("fetch_emails", "success", result)
            return result

        except Exception as e:
            error_result = {
                "filter": filter_name,
                "status": "error",
                "error": str(e)
            }
            self._log("fetch_emails", "error", error_result)
            raise

    def _build_search_criteria(self, filter_config: Dict) -> tuple:
        """Build IMAP search criteria from filter config"""
        criteria = []

        # Filter by sender
        sender = filter_config.get('sender')
        if sender:
            criteria.append(f'FROM "{sender}"')

        # Filter by subject
        subject = filter_config.get('subject_contains')
        if subject:
            criteria.append(f'SUBJECT "{subject}"')

        # Filter by date range
        date_range = filter_config.get('date_range', {})
        if 'days_back' in date_range:
            days_back = date_range['days_back']
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            criteria.append(f'SINCE {since_date}')

        # If no criteria specified, get all emails
        if not criteria:
            criteria = ['ALL']

        return tuple(criteria)

    def _fetch_single_email(self, email_id: bytes) -> Dict[str, Any]:
        """Fetch a single email by ID"""
        status, msg_data = self.mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            raise Exception(f"Failed to fetch email {email_id}")

        # Parse email
        msg = email.message_from_bytes(msg_data[0][1])

        # Extract headers
        subject = self._decode_header(msg.get('Subject', ''))
        from_addr = self._decode_header(msg.get('From', ''))
        to_addr = self._decode_header(msg.get('To', ''))
        date_str = msg.get('Date', '')

        # Extract body
        body = self._extract_body(msg)

        # Extract attachments info
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename:
                attachments.append({
                    'filename': self._decode_header(filename),
                    'content_type': part.get_content_type(),
                    'size': len(part.get_payload(decode=True)),
                    'part': part
                })

        return {
            'id': email_id.decode(),
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date_str,
            'body': body,
            'attachments': attachments
        }

    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ''

        decoded_parts = decode_header(header)
        decoded_string = ''

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part

        return decoded_string

    def _extract_body(self, msg) -> str:
        """Extract email body (text or HTML)"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())

        return body

    def _save_email_content(self, email_data: Dict, output_dir: Path) -> Path:
        """Save email content to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject = "".join(c for c in email_data['subject'][:50] if c.isalnum() or c in (' ', '-', '_'))

        email_file = output_dir / f"email_{timestamp}_{safe_subject}.json"

        # Prepare data for saving (exclude attachment content)
        save_data = {
            'id': email_data['id'],
            'subject': email_data['subject'],
            'from': email_data['from'],
            'to': email_data['to'],
            'date': email_data['date'],
            'body': email_data['body'],
            'attachments': [
                {
                    'filename': att['filename'],
                    'content_type': att['content_type'],
                    'size': att['size']
                }
                for att in email_data['attachments']
            ]
        }

        with open(email_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        return email_file

    def _download_attachments(self, email_data: Dict, output_dir: Path,
                             allowed_types: List[str] = None) -> int:
        """
        Download email attachments

        Args:
            email_data: Email data dictionary
            output_dir: Directory to save attachments
            allowed_types: List of allowed file extensions (e.g., ['pdf', 'xlsx'])

        Returns:
            Number of attachments downloaded
        """
        attachments_dir = output_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)

        downloaded_count = 0

        for attachment in email_data['attachments']:
            filename = attachment['filename']

            # Check file type if filter specified
            if allowed_types:
                file_ext = Path(filename).suffix.lstrip('.').lower()
                if file_ext not in allowed_types:
                    continue

            # Check file size
            max_size_mb = self.config.get('email_monitoring', {}).get('attachments', {}).get('max_size_mb', 25)
            if attachment['size'] > max_size_mb * 1024 * 1024:
                self._log("download_attachment", "skipped", {
                    "filename": filename,
                    "reason": "file too large",
                    "size_mb": attachment['size'] / (1024 * 1024)
                })
                continue

            # Download attachment
            try:
                file_path = attachments_dir / filename

                # Avoid filename conflicts
                counter = 1
                while file_path.exists():
                    stem = Path(filename).stem
                    suffix = Path(filename).suffix
                    file_path = attachments_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

                # Save attachment
                with open(file_path, 'wb') as f:
                    f.write(attachment['part'].get_payload(decode=True))

                downloaded_count += 1
                self._log("download_attachment", "success", {
                    "filename": filename,
                    "path": str(file_path),
                    "size": attachment['size']
                })

            except Exception as e:
                self._log("download_attachment", "error", {
                    "filename": filename,
                    "error": str(e)
                })

        return downloaded_count

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
