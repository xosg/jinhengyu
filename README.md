# Multi-Source Data Collection & API Integration System

A lightweight, pluggable Python toolkit for collecting data from multiple sources (web, email) and integrating with third-party APIs (email, storage, search, e-signature).

## Project Overview

This project demonstrates a modular architecture for:
- **Module 1**: Multi-source data collection (web scraping, email monitoring, attachment handling)
- **Module 2**: Third-party API integration with unified interfaces (pluggable design)

**Important**: Module 1 and Module 2 are **completely independent** - they demonstrate different APIs/libraries and do not connect or share data. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

**Design Philosophy**: All APIs use abstract base classes for easy swapping between mock and real services.

## Features

### Module 1: Data Collection Engine
- Web scraping (static sites with `requests`, dynamic sites with `selenium`)
- Email monitoring via Outlook/Office 365 IMAP
- Attachment download and classification
- YAML-based configuration
- Error handling with retry logic

### Module 2: API Integration Engine
- **Email Service**: Outlook/Office 365 SMTP (send to yourself for testing)
- **Storage Service**: Mock S3 (local filesystem with S3-like interface)
- **E-Signature Service**: Mock DocuSign (simulated workflow)
- **Search Service**: Mock Google Search (simulated results)
- **Physical Mail Service**: Mock Lob (simulated mail sending)
- Unified interfaces for easy provider switching
- Configuration-driven (YAML + environment variables)

## Project Structure

```
jinhengyu/
├── src/
│   ├── collection/          # Module 1: Data Collection
│   │   ├── __init__.py
│   │   ├── web_scraper.py
│   │   ├── email_monitor.py
│   │   └── attachment_handler.py
│   └── api_integration/     # Module 2: API Integration
│       ├── __init__.py
│       ├── base.py          # Abstract base classes
│       ├── email_service.py # QQ Mail/Gmail SMTP
│       ├── storage_service.py # Mock S3
│       ├── signature_service.py # Mock DocuSign
│       ├── search_service.py # Mock Google
│       └── mail_service.py  # Mock Lob (optional)
├── config/
│   ├── collection_config.yaml
│   └── api_config.yaml
├── examples/
│   ├── demo_collection.py
│   └── demo_api.py
├── logs/                    # Auto-generated logs (JSONL format)
├── collected_data/          # Auto-generated output
├── requirements.txt
├── README.md
└── PROJECT_PROGRESS.md
```

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```
   # Outlook/Office 365 credentials for Module 1 (email monitoring) and Module 2 (email sending)
   OUTLOOK_USER=your.email@outlook.com
   OUTLOOK_PASSWORD=your_password

   # Note: Use your regular Outlook password
   # If you have 2FA enabled, you may need an App Password
   ```

4. **Configure services**:
   - Edit `config/collection_config.yaml` for data collection rules
   - Edit `config/api_config.yaml` for API service settings

## Quick Start

### Module 1: Data Collection

```python
# See examples/demo_collection.py
from src.collection.web_scraper import WebScraper
from src.collection.email_monitor import EmailMonitor

# Scrape a website
scraper = WebScraper(config_path="config/collection_config.yaml")
scraper.scrape_static_site("https://example.com")

# Monitor emails
monitor = EmailMonitor(config_path="config/collection_config.yaml")
monitor.fetch_emails(sender_filter="no-reply@example.com")
```

### Module 2: API Integration

```python
# See examples/demo_api.py
from src.api_integration.email_service import create_email_service
from src.api_integration.storage_service import create_storage_service

# Send email (uses Outlook by default, configurable)
email_service = create_email_service()
email_service.send_email(
    to="your.email@outlook.com",
    subject="Test Email",
    content="Hello from the API integration module!"
)

# Store file
storage = create_storage_service()
storage.upload_file("document.pdf", bucket="my-bucket", key="docs/document.pdf")
```

## Configuration

All services are configured via YAML files:

- `config/collection_config.yaml`: Web scraping rules, email filters, storage paths
- `config/api_config.yaml`: API service providers, credentials (via env vars), default parameters

Secrets are loaded from environment variables using the pattern: `${ENV:VARIABLE_NAME}`

## Logging

All operations are logged in JSONL format (one JSON object per line):
- `logs/collection_log.jsonl`: Data collection activities
- `logs/api_call_log.jsonl`: API integration calls

## Architecture Highlights

### Pluggable Design
All services implement abstract base classes (see `src/api_integration/base.py`), making it easy to swap implementations:

```python
# Switch from mock to real S3 by changing config only
storage_service:
  provider: "MockS3Service"  # or "AWSS3Service" (future)
  bucket: "my-bucket"
```

### Error Handling
- Automatic retry with exponential backoff (max 3 attempts)
- Graceful degradation (skip corrupted files, continue processing)
- Detailed error logging for debugging

## Testing

Run the demo scripts to verify functionality:

```bash
python examples/demo_collection.py
python examples/demo_api.py
```

## Future Enhancements

- Swap mock services for real APIs (SendGrid, AWS S3, DocuSign, Google Search API)
- Add support for multiple email providers (Outlook, etc.)
- Implement service provider failover
- Add progress visualization
- Create proper Python package distribution

## License

Educational project - free to use and modify.

## Author

Created as a homework assignment to demonstrate AI-assisted development and modular architecture design.
