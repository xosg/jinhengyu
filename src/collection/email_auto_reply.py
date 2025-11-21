"""
Email Auto-Reply Service
Monitors QQ Mail inbox via IMAP and automatically replies to new emails with the same content
"""

import os
import sys
import imaplib
import email
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from email.header import decode_header
from email.utils import parseaddr

import yaml

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from api_integration.email_service import create_email_service
except ImportError:
    print("Warning: Email service not available")
    create_email_service = None


class EmailAutoReplyService:
    """Monitor email inbox and auto-reply to new messages"""

    LOCK_FILE = ".email_auto_reply.lock"

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize email auto-reply service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        self.lock_file_path = Path(self.LOCK_FILE)

        # IMAP connection
        self.mail = None
        self.is_running = False

        # Track processed emails to avoid duplicates
        self.processed_uids: Set[str] = set()
        self.initial_uids: Set[str] = set()  # UIDs present when service started
        self.initialized = False  # Flag to skip existing emails on first poll

        # QQ Mail IMAP settings
        self.imap_server = "imap.qq.com"
        self.imap_port = 993

        # Get credentials from environment
        self.username = os.getenv('QQMAIL_USER', '')
        self.password = os.getenv('QQMAIL_PASSWORD', '')

        # Polling interval (seconds)
        self.poll_interval = 10

        # Initialize SMTP email service for sending replies
        self.email_service = None
        if create_email_service:
            try:
                self.email_service = create_email_service(config_path=config_path)
            except Exception as e:
                self._log("init", "warning", {
                    "message": "Failed to initialize email service",
                    "error": str(e)
                })

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            return {}

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = 'logs/email_auto_reply_log.jsonl'

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "email_auto_reply",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _acquire_lock(self) -> bool:
        """Acquire lock file to prevent multiple instances"""
        if self.lock_file_path.exists():
            try:
                with open(self.lock_file_path, 'r') as f:
                    pid = int(f.read().strip())
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                       capture_output=True, text=True)
                if str(pid) in result.stdout:
                    return False
            except (ValueError, FileNotFoundError, subprocess.SubprocessError):
                pass

        with open(self.lock_file_path, 'w') as f:
            f.write(str(os.getpid()))
        return True

    def _release_lock(self):
        """Release lock file"""
        try:
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
        except Exception:
            pass

    def _decode_header_value(self, value: str) -> str:
        """Decode email header value"""
        if value is None:
            return ""

        decoded_parts = []
        for part, charset in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
                except (LookupError, UnicodeDecodeError):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract email body text"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                # Get text content
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        break  # Prefer plain text
                    except Exception:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        # Simple HTML to text conversion
                        import re
                        body = re.sub(r'<[^>]+>', '', body)
                    except Exception:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
            except Exception:
                body = str(msg.get_payload())

        return body.strip()

    def connect(self) -> bool:
        """Connect to QQ Mail IMAP server"""
        if not self.username or not self.password:
            print("[ERROR] QQ Mail credentials not configured!")
            print("        Set QQMAIL_USER and QQMAIL_PASSWORD in .env")
            return False

        print(f"[{datetime.now().strftime('%H:%M:%S')}] [CONNECT] Connecting to {self.imap_server}...")

        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.username, self.password)
            self.mail.select('INBOX')

            print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Connected to QQ Mail as {self.username}")
            self._log("connect", "success", {"server": self.imap_server, "username": self.username})
            return True

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Connection failed: {e}")
            self._log("connect", "error", {"error": str(e)})
            return False

    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass
            self.mail = None

    def _safe_print(self, text: str):
        """Print text safely, handling encoding issues on Windows"""
        try:
            print(text)
        except UnicodeEncodeError:
            # Replace problematic characters with ?
            print(text.encode('ascii', 'replace').decode('ascii'))

    def _get_new_emails(self) -> List[Dict]:
        """Fetch new unread emails"""
        new_emails = []

        try:
            # Search for unseen (unread) emails
            status, messages = self.mail.search(None, 'UNSEEN')

            if status != 'OK':
                return []

            email_ids = messages[0].split()

            # On first poll, just record existing UIDs and skip replying
            if not self.initialized:
                for email_id in email_ids:
                    uid = email_id.decode()
                    self.initial_uids.add(uid)
                    self.processed_uids.add(uid)
                self.initialized = True
                self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [INIT] Skipped {len(email_ids)} existing unread emails")
                self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}]        Will only reply to NEW incoming emails")
                return []

            for email_id in email_ids:
                uid = email_id.decode()

                # Skip if already processed or was present at startup
                if uid in self.processed_uids or uid in self.initial_uids:
                    continue

                # Fetch the email
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                # Parse the email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract email details
                from_header = msg.get('From', '')
                sender_name, sender_email = parseaddr(from_header)
                sender_name = self._decode_header_value(sender_name)

                subject = self._decode_header_value(msg.get('Subject', '(No Subject)'))
                body = self._get_email_body(msg)
                date = msg.get('Date', '')
                message_id = msg.get('Message-ID', '')

                # Skip emails from ourselves (avoid infinite loops!)
                if self.username.lower() in sender_email.lower():
                    self.processed_uids.add(uid)
                    continue

                new_emails.append({
                    'uid': uid,
                    'from_email': sender_email,
                    'from_name': sender_name,
                    'subject': subject,
                    'body': body,
                    'date': date,
                    'message_id': message_id
                })

                self.processed_uids.add(uid)

        except Exception as e:
            self._log("fetch_emails", "error", {"error": str(e)})

        return new_emails

    def _send_reply(self, original_email: Dict) -> bool:
        """Send auto-reply with same content"""
        if not self.email_service:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Email service not available")
            return False

        sender_email = original_email['from_email']
        original_subject = original_email['subject']
        original_body = original_email['body']

        # Create reply subject
        if not original_subject.lower().startswith('re:'):
            reply_subject = f"Re: {original_subject}"
        else:
            reply_subject = original_subject

        # Create reply body with original content echoed back
        reply_body = f"""This is an auto-reply echoing your message:

--- Original Message ---
From: {original_email['from_name']} <{sender_email}>
Subject: {original_subject}
Date: {original_email['date']}

{original_body}
--- End of Original Message ---

This reply was automatically generated by Email Auto-Reply Service.
"""

        self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [REPLY] Sending reply to {sender_email}...")

        try:
            result = self.email_service.send_email(
                to=sender_email,
                subject=reply_subject,
                content=reply_body,
                html=False
            )

            if result.get('status') == 'success':
                self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Reply sent to {sender_email}")
                self._log("send_reply", "success", {
                    "to": sender_email,
                    "subject": reply_subject
                })
                return True
            else:
                self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Failed to send reply: {result.get('error')}")
                self._log("send_reply", "error", {"error": result.get('error')})
                return False

        except Exception as e:
            self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Exception: {e}")
            self._log("send_reply", "error", {"error": str(e)})
            return False

    def start_monitoring(self):
        """Start monitoring inbox for new emails"""
        if self.is_running:
            print("Auto-reply service is already running")
            return

        # Check for existing instance
        if not self._acquire_lock():
            print("[ERROR] Another auto-reply instance is already running!")
            print("        Kill the other process first or delete .email_auto_reply.lock")
            return

        # Connect to IMAP
        if not self.connect():
            self._release_lock()
            return

        self.is_running = True

        print()
        print("=" * 60)
        print("EMAIL AUTO-REPLY SERVICE")
        print("=" * 60)
        print(f"Monitoring: {self.username}")
        print(f"Poll interval: {self.poll_interval} seconds")
        print("Press Ctrl+C to stop.")
        print("=" * 60)
        print()

        self._log("start_monitoring", "started", {
            "username": self.username,
            "poll_interval": self.poll_interval
        })

    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.is_running:
            return

        self.disconnect()
        self._release_lock()
        self.is_running = False

        print()
        print("Auto-reply service stopped.")
        self._log("stop_monitoring", "completed", {})

    def monitor_forever(self):
        """Start monitoring and block until interrupted"""
        self.start_monitoring()

        if not self.is_running:
            return

        try:
            while self.is_running:
                # Check for new emails
                self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [POLL] Checking for new emails...")

                new_emails = self._get_new_emails()

                if new_emails:
                    self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [NEW] Found {len(new_emails)} new email(s)")

                    for email_data in new_emails:
                        self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] [EMAIL] From: {email_data['from_email']}")
                        self._safe_print(f"[{datetime.now().strftime('%H:%M:%S')}]         Subject: {email_data['subject']}")

                        # Send auto-reply
                        self._send_reply(email_data)
                        print()

                # Wait before next poll
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            self.stop_monitoring()


# Factory function
def create_auto_reply_service(config_path: str = "config/api_config.yaml") -> EmailAutoReplyService:
    """Create email auto-reply service instance"""
    return EmailAutoReplyService(config_path)
