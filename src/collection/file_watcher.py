"""
File Watcher Service
Monitors directories for file changes and sends email notifications with attachments
"""

import os
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict

import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Try to import email service
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from api_integration.email_service import create_email_service
except ImportError:
    print("Warning: Email service not available. Please ensure src/api_integration/email_service.py exists.")
    create_email_service = None


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events"""

    def __init__(self, callback):
        """
        Initialize event handler

        Args:
            callback: Function to call when file changes are detected
        """
        super().__init__()
        self.callback = callback

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if not event.is_directory:
            self.callback(event.src_path, 'created')

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if not event.is_directory:
            self.callback(event.src_path, 'modified')

    def on_moved(self, event: FileSystemEvent):
        """Handle file move events"""
        if not event.is_directory:
            self.callback(event.dest_path, 'moved')


class FileWatcherService:
    """Monitor directories and send email notifications on file changes"""

    LOCK_FILE = ".file_watcher.lock"

    def __init__(self, config_path: str = "config/collection_config.yaml"):
        """
        Initialize file watcher service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        self.lock_file_path = Path(self.LOCK_FILE)

        # File watching configuration
        watch_config = self.config.get('file_watching', {})
        self.watched_dirs = watch_config.get('watched_directories', [])
        settings = watch_config.get('settings', {})

        self.debounce_delay = settings.get('debounce_delay_seconds', 2)
        self.max_file_size_mb = settings.get('max_file_size_mb', 100)
        self.send_email_on_change = settings.get('send_email_on_change', True)
        self.cooldown_seconds = settings.get('cooldown_seconds', 10)  # Prevent duplicate emails

        # State tracking
        self.observers: List[Observer] = []
        self.pending_changes: Dict[str, Set[str]] = defaultdict(set)  # {directory: {files}}
        self.pending_event_types: Dict[str, str] = {}  # {file_path: event_type}
        self.debounce_timers: Dict[str, threading.Timer] = {}
        self.recently_processed: Dict[str, float] = {}  # {file_path: timestamp} - cooldown tracking
        self.is_running = False

        # Initialize email service if available
        self.email_service = None
        if create_email_service:
            try:
                self.email_service = create_email_service(config_path="config/api_config.yaml")
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
            print(f"Warning: Config file not found: {self.config_path}")
            return {}

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
            "module": "file_watcher",
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

    def _on_file_change(self, file_path: str, event_type: str):
        """
        Callback when a file change is detected

        Args:
            file_path: Path to the changed file
            event_type: Type of change (created, modified, moved)
        """
        file_path = os.path.abspath(file_path)

        # Check if file exists and size is acceptable
        if not os.path.exists(file_path):
            return

        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                self._log("file_change", "skipped", {
                    "file": file_path,
                    "reason": f"File too large ({file_size_mb:.2f} MB > {self.max_file_size_mb} MB)"
                })
                return
        except OSError:
            return  # File might be in use or deleted

        # Find which watched directory this file belongs to
        watched_dir = None
        for dir_config in self.watched_dirs:
            dir_path = os.path.abspath(dir_config.get('path', ''))
            if file_path.startswith(dir_path):
                watched_dir = dir_path
                break

        if not watched_dir:
            return

        # Check cooldown - skip if file was recently processed
        current_time = time.time()
        if file_path in self.recently_processed:
            last_processed = self.recently_processed[file_path]
            if current_time - last_processed < self.cooldown_seconds:
                # File was recently processed, skip to prevent duplicate email
                return

        # Add to pending changes
        self.pending_changes[watched_dir].add(file_path)
        self.pending_event_types[file_path] = event_type

        # Console output for immediate feedback
        file_name = Path(file_path).name
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [DETECT] {file_name} ({event_type})")

        self._log("file_change", "detected", {
            "file": file_path,
            "event_type": event_type,
            "watched_dir": watched_dir
        })

        # Cancel existing timer for this directory
        if watched_dir in self.debounce_timers:
            self.debounce_timers[watched_dir].cancel()

        # Start new debounce timer
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WAIT] Batching changes (waiting {self.debounce_delay}s)...")

        timer = threading.Timer(
            self.debounce_delay,
            self._process_pending_changes,
            args=[watched_dir]
        )
        timer.daemon = True
        timer.start()
        self.debounce_timers[watched_dir] = timer

    def _process_pending_changes(self, watched_dir: str):
        """
        Process all pending changes for a watched directory

        Args:
            watched_dir: Directory path
        """
        if watched_dir not in self.pending_changes:
            return

        changed_files = list(self.pending_changes[watched_dir])
        if not changed_files:
            return

        # Clear pending changes for this directory
        self.pending_changes[watched_dir].clear()

        # Filter out files that no longer exist
        existing_files = [f for f in changed_files if os.path.exists(f)]

        if not existing_files:
            return

        # Console output
        file_names = [Path(f).name for f in existing_files]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [PROCESS] {len(existing_files)} file(s): {', '.join(file_names)}")

        self._log("process_changes", "started", {
            "watched_dir": watched_dir,
            "file_count": len(existing_files)
        })

        # Get directory config
        dir_config = None
        for config in self.watched_dirs:
            if os.path.abspath(config.get('path', '')) == watched_dir:
                dir_config = config
                break

        if not dir_config:
            return

        # Send email notification if configured
        if dir_config.get('notify_on_change', True) and self.send_email_on_change:
            self._send_notification_email(watched_dir, existing_files, dir_config)

    def _send_notification_email(self, watched_dir: str, files: List[str], dir_config: Dict):
        """
        Send email notification with file attachments

        Args:
            watched_dir: Directory being watched
            files: List of changed file paths
            dir_config: Directory configuration
        """
        if not self.email_service:
            self._log("send_notification", "error", {
                "error": "Email service not initialized"
            })
            return

        # Get email configuration
        notify_email = self._resolve_env_var(dir_config.get('notify_email', ''))
        from_email = self._resolve_env_var(dir_config.get('from_email', None))

        if not notify_email:
            self._log("send_notification", "error", {
                "error": "No notification email configured"
            })
            return

        # Build email content
        subject = f"File Changes Detected in {Path(watched_dir).name}"

        # Create file list with event types
        file_list = []
        for file_path in files:
            event_type = self.pending_event_types.get(file_path, 'changed')
            file_size = os.path.getsize(file_path)
            file_size_kb = file_size / 1024

            file_list.append(f"  - {Path(file_path).name} ({event_type}, {file_size_kb:.1f} KB)")

        content = f"""File changes detected in monitored directory:

Directory: {watched_dir}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Files Changed: {len(files)}

Changed Files:
{chr(10).join(file_list)}

The changed files are attached to this email.

---
This is an automated notification from File Watcher Service.
"""

        # Send email with attachments
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [EMAIL] Sending to {notify_email}...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}]         Connecting to SMTP server...")

            result = self.email_service.send_email(
                to=notify_email,
                subject=subject,
                content=content,
                from_email=from_email,
                attachments=files,
                html=False
            )

            if result.get('status') == 'success':
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Email sent! ({len(files)} file(s) attached)")
                print()

                # Mark files as processed to prevent duplicate emails
                current_time = time.time()
                for f in files:
                    self.recently_processed[f] = current_time

                self._log("send_notification", "success", {
                    "watched_dir": watched_dir,
                    "recipient": notify_email,
                    "file_count": len(files),
                    "files": [Path(f).name for f in files]
                })
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Email failed: {result.get('error', 'Unknown error')}")
                print()

                self._log("send_notification", "error", {
                    "watched_dir": watched_dir,
                    "error": result.get('error', 'Unknown error')
                })

        except Exception as e:
            import traceback
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Exception: {str(e)}")
            print()

            self._log("send_notification", "error", {
                "watched_dir": watched_dir,
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    def _acquire_lock(self) -> bool:
        """Acquire lock file to prevent multiple instances"""
        if self.lock_file_path.exists():
            # Check if the process that created the lock is still running
            try:
                with open(self.lock_file_path, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is still running (Windows-compatible)
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                       capture_output=True, text=True)
                if str(pid) in result.stdout:
                    return False  # Another instance is running
            except (ValueError, FileNotFoundError, subprocess.SubprocessError):
                pass  # Lock file is stale, we can overwrite it

        # Write our PID to the lock file
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

    def start_watching(self):
        """Start monitoring all configured directories"""
        if self.is_running:
            print("File watcher is already running")
            return

        if not self.watched_dirs:
            print("No directories configured for watching")
            return

        # Check for existing instance
        if not self._acquire_lock():
            print("[ERROR] Another file watcher instance is already running!")
            print("        Kill the other process first or delete .file_watcher.lock")
            return

        self._log("start_watching", "started", {
            "directories": [d.get('path') for d in self.watched_dirs]
        })

        for dir_config in self.watched_dirs:
            if not dir_config.get('enabled', True):
                continue

            watch_path = dir_config.get('path', '')
            watch_path = os.path.abspath(watch_path)

            # Create directory if it doesn't exist
            Path(watch_path).mkdir(parents=True, exist_ok=True)

            # Create observer
            event_handler = FileChangeHandler(self._on_file_change)
            observer = Observer()
            observer.schedule(
                event_handler,
                watch_path,
                recursive=dir_config.get('recursive', False)
            )
            observer.start()
            self.observers.append(observer)

            print(f"Started watching: {watch_path}")
            self._log("watching_directory", "started", {
                "path": watch_path,
                "recursive": dir_config.get('recursive', False)
            })

        self.is_running = True
        print(f"\nFile Watcher is running. Monitoring {len(self.observers)} directories...")
        print(f"Debounce delay: {self.debounce_delay} seconds")
        print("Press Ctrl+C to stop.\n")

    def stop_watching(self):
        """Stop monitoring all directories"""
        if not self.is_running:
            return

        self._log("stop_watching", "started", {})

        # Cancel all pending timers
        for timer in self.debounce_timers.values():
            timer.cancel()
        self.debounce_timers.clear()

        # Stop all observers
        for observer in self.observers:
            observer.stop()
            observer.join()

        self.observers.clear()
        self.is_running = False

        # Release lock file
        self._release_lock()

        print("\nFile watcher stopped.")
        self._log("stop_watching", "completed", {})

    def watch_forever(self):
        """Start watching and block until interrupted"""
        self.start_watching()

        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            self.stop_watching()


# Convenience function for quick setup
def create_file_watcher(config_path: str = "config/collection_config.yaml") -> FileWatcherService:
    """
    Factory function to create file watcher service

    Args:
        config_path: Path to configuration file

    Returns:
        FileWatcherService instance
    """
    return FileWatcherService(config_path)
