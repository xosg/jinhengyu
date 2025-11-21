# Quick Start Guide for Professor

**Student:** Jin Hengyu
**Project:** Multi-API Integration System
**Main Entry Point:** `examples/demo_comprehensive_workflow_enhanced.py`

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Credentials

Edit the `.env` file and add API credentials:

```bash
# These credentials are provided separately for security
OUTLOOK_USER=h.jin@student.xu-university.de
OUTLOOK_PASSWORD=<provided separately>

GOOGLE_API_KEY=<provided separately>
GOOGLE_SEARCH_ENGINE_ID=<provided separately>

PANDADOC_API_KEY=<provided separately>

# MinIO (already configured - no changes needed)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

**Note:** All API credentials are test/sandbox keys provided separately for security.

### Step 3: Start MinIO Server

**Windows:**
```bash
start_minio.bat
```

**Linux/Mac:**
```bash
./minio server minio_data --console-address ":9001"
```

This starts:
- MinIO API: http://localhost:9000
- MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)

### Step 4: Run the Demo

```bash
python examples/demo_comprehensive_workflow_enhanced.py
```

When prompted, enter search keywords (or press Enter for default).

---

## 📋 What the Demo Does

The demo executes a **7-step workflow** demonstrating multiple API integrations:

1. **Google Custom Search API** - Searches for user-provided keywords
2. **Web Scraping** - Scrapes content from search results (Selenium + BeautifulSoup)
3. **Screenshot Capture** - Captures webpage screenshots
4. **PDF Generation** - Creates research report (ReportLab)
5. **MinIO Storage** - Uploads PDF to S3-compatible storage
6. **PandaDoc E-Signature** - Sends document for signature
7. **Email Notification** - Sends HTML email with results

### Expected Output

After completion, check:
- `collected_data/comprehensive_demo/` - Generated PDFs and screenshots
- `logs/api_call_log.jsonl` - Detailed API call logs
- MinIO Console (http://localhost:9001) - Uploaded files in "research-reports" bucket
- Email inbox - HTML report with embedded screenshots

---

## 🎯 Technologies Demonstrated

### Real APIs/Services:
1. ✅ **Google Custom Search API** - Real web search
2. ✅ **PandaDoc API** - Real e-signature service (sandbox)
3. ✅ **MinIO** - Real S3-compatible object storage
4. ✅ **Outlook SMTP** - Real email sending
5. ✅ **Selenium WebDriver** - Browser automation

### Python Libraries:
1. ✅ **requests** - HTTP client
2. ✅ **beautifulsoup4** - HTML parsing
3. ✅ **selenium** - Web automation
4. ✅ **ReportLab** - PDF generation
5. ✅ **PyYAML** - Configuration management
6. ✅ **python-dotenv** - Environment variables
7. ✅ **minio** - S3 client

### Architecture Patterns:
1. ✅ **Factory Pattern** - Service creation
2. ✅ **Abstract Base Classes** - Pluggable architecture
3. ✅ **Configuration-driven** - YAML + environment variables
4. ✅ **Error Handling** - Retry logic and graceful degradation
5. ✅ **Structured Logging** - JSONL format

---

## 📂 Project Structure

```
jinhengyu/
├── examples/
│   └── demo_comprehensive_workflow_enhanced.py  # MAIN ENTRY POINT
├── src/
│   ├── api_integration/         # Real API integrations
│   │   ├── search_service.py   # Google Custom Search
│   │   ├── storage_service.py  # MinIO S3
│   │   ├── minio_service.py    # MinIO implementation
│   │   ├── signature_service.py # PandaDoc
│   │   └── email_service.py    # Outlook SMTP
│   ├── collection/              # Data collection
│   │   ├── web_scraper.py      # Web scraping
│   │   ├── email_monitor.py    # Email monitoring
│   │   └── attachment_handler.py # File handling
│   └── utils/                   # Utilities
│       ├── pdf_generator.py    # PDF creation
│       └── screenshot_service.py # Screenshot capture
├── config/
│   ├── api_config.yaml         # API configurations
│   └── collection_config.yaml  # Data collection configs
├── minio.exe                    # MinIO server (Windows)
├── start_minio.bat             # Start MinIO (Windows)
├── stop_minio.bat              # Stop MinIO (Windows)
├── requirements.txt            # Python dependencies
├── .env                        # Credentials (template)
└── 需求.pdf                     # Original requirements (Chinese)
```

---

## 🔧 Alternative: Run Other Demos

### Test Individual Services:

```bash
# Test Google Search API
python examples/test_google_search.py

# Test web scraping
python examples/test_search_and_scrape.py

# Test PandaDoc integration
python examples/demo_docusign_workflow.py

# Test individual modules
python examples/demo_api.py
python examples/demo_collection.py
```

---

## 🐛 Troubleshooting

### MinIO won't start
```bash
# Check if port is in use
netstat -ano | findstr :9000

# Kill existing MinIO process
taskkill /F /IM minio.exe

# Start again
start_minio.bat
```

### Google API errors
- Verify `GOOGLE_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` in `.env`
- Check API quota at: https://console.cloud.google.com/

### PandaDoc errors
- Ensure using sandbox API key (not production)
- Verify key in `.env` file

### Email errors
- Verify Outlook credentials
- Check if 2FA is enabled (may need app password)

### Selenium/WebDriver issues
- Chrome browser must be installed
- `webdriver-manager` auto-downloads ChromeDriver

---

## 📊 Evaluation Criteria Demonstrated

### Technical Skills:
✅ Multiple API integrations (Google, PandaDoc, MinIO, Outlook)
✅ Web scraping (static & dynamic sites)
✅ PDF generation from scraped data
✅ S3-compatible object storage
✅ E-signature workflow
✅ Email automation

### Software Architecture:
✅ Modular design (separation of concerns)
✅ Abstract base classes (polymorphism)
✅ Factory pattern (service creation)
✅ Configuration-driven (YAML + env vars)
✅ Error handling & retry logic
✅ Structured logging

### Code Quality:
✅ Type hints and docstrings
✅ Comprehensive error handling
✅ Security best practices (no hardcoded credentials)
✅ Clean code organization
✅ Detailed documentation

---

## 📞 Contact

**Student:** Jin Hengyu
**Email:** h.jin@student.xu-university.de

For questions or issues running the demo, please contact the student.

---

## 📝 Notes

- All API keys provided are **test/sandbox keys** - safe for educational use
- MinIO data is stored locally in `minio_data/` directory
- Logs are written to `logs/` directory in JSONL format
- Output files are saved to `collected_data/` directory
- The project demonstrates **real API integration** skills for employment

---

**Estimated run time:** 2-5 minutes (depending on network speed and number of search results)

**System requirements:**
- Python 3.8+
- Chrome browser (for Selenium)
- ~500MB disk space (including MinIO)
- Internet connection (for API calls)
