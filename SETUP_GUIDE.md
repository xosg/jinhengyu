# Setup and Testing Guide

This guide will help you set up and test the Multi-Source Data Collection & API Integration System.

## Prerequisites

- Python 3.8 or higher
- Gmail account (for email features)
- Internet connection (for web scraping)

## Step 1: Install Dependencies

Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

This will install all required packages:
- Web scraping: `requests`, `selenium`, `beautifulsoup4`, `webdriver-manager`
- Configuration: `PyYAML`, `python-dotenv`
- File handling: `filetype`, `python-magic-bin` (Windows) or `python-magic` (Linux/Mac)
- Progress bars: `tqdm`

## Step 2: Set Up Gmail App Password

The system uses Gmail for both:
- Module 1: Monitoring/reading emails (IMAP)
- Module 2: Sending emails (SMTP)

### Generate Gmail App Password

1. Go to your Google Account: https://myaccount.google.com
2. Select "Security" from the left menu
3. Under "How you sign in to Google", select "2-Step Verification"
   - If not enabled, enable it first
4. Scroll to the bottom and select "App passwords"
5. Select "Mail" and "Windows Computer" (or your OS)
6. Click "Generate"
7. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Create .env File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   GMAIL_USER=your.email@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```

   **Important**: Remove spaces from the app password!

## Step 3: Configure Collection and API Settings

### Module 1 Configuration (config/collection_config.yaml)

Edit `config/collection_config.yaml` to customize:

1. **Web Scraping**: Update URLs and CSS selectors
2. **Email Monitoring**: Set sender filters and attachment types
3. **Output Paths**: Change where collected data is saved

### Module 2 Configuration (config/api_config.yaml)

The default configuration uses:
- Gmail SMTP for email (free)
- Mock S3 for storage (local filesystem)
- Mock DocuSign for signatures (simulated)
- Mock Google Search (simulated)

No changes needed unless you want to use real paid services later.

## Step 4: Test Module 1 (Data Collection)

Run the Module 1 demo script:

```bash
python examples/demo_collection.py
```

### What it does:

1. **Web Scraping Demo**:
   - Scrapes example.com (static site)
   - Extracts headers and paragraphs
   - Saves HTML and extracted data to `collected_data/web/static/`

2. **Email Monitoring Demo**:
   - Connects to your Gmail inbox via IMAP
   - Fetches emails based on filters in config
   - Downloads attachments to `collected_data/email/`
   - Note: If no matching emails, it will report 0 fetched (this is normal)

3. **Attachment Organization Demo**:
   - Creates sample test files (PDF, Excel, images)
   - Organizes files by type into folders
   - Creates a file inventory JSON

### Expected Output:

```
============================================================
MODULE 1: DATA COLLECTION ENGINE - DEMO
============================================================

============================================================
DEMO 1: Web Scraping
============================================================

1. Scraping static site (example.com)...
   ✓ Success! Output: collected_data/web/static/Example_Site_20241106_...

2. Scraping all configured static sites...
   ✓ Scraped 1/1 sites

============================================================
DEMO 2: Email Monitoring
============================================================

1. Connecting to email server...
   ✓ Connected successfully!

2. Fetching emails by configured filters...
   ✓ Fetched X emails
   ✓ Downloaded Y attachments

============================================================
DEMO 3: Attachment Organization
============================================================

   Creating sample test files for demo...
   ✓ Created sample files in collected_data/test_files

1. Creating file inventory...
   ✓ Found 4 files
   ✓ Total size: X MB
   ✓ Categories: ['pdf', 'excel', 'images', 'text']

2. Organizing files by type...
   ✓ Organized 4 files
   ✓ By category: {'pdf': 1, 'excel': 1, 'images': 1, 'text': 1}

============================================================
DEMO COMPLETED!
============================================================
```

### Check Results:

- Web scraping: `collected_data/web/`
- Email monitoring: `collected_data/email/`
- Organized files: `collected_data/organized/`
- Logs: `logs/collection_log.jsonl`

## Step 5: Test Module 2 (API Integration)

Run the Module 2 demo script:

```bash
python examples/demo_api.py
```

### What it does:

1. **Email Service Demo**:
   - Sends a test email to yourself using Gmail SMTP
   - Validates email address formats
   - Check your inbox for the test email!

2. **Storage Service Demo**:
   - Creates a test file
   - Uploads to Mock S3 (local filesystem at `collected_data/mock_s3/`)
   - Lists files in bucket
   - Downloads file back
   - Generates presigned URLs

3. **Signature Service Demo**:
   - Creates a mock contract document
   - Creates a signature envelope with multiple signers
   - Simulates signature workflow
   - Saves envelope data to `collected_data/signatures/`

4. **Search Service Demo**:
   - Performs web searches (returns mock results)
   - Performs image searches (returns mock results)
   - Shows how results would look with real Google Search API

5. **Architecture Demo**:
   - Explains pluggable design
   - Shows how to swap providers by changing config only

### Expected Output:

```
============================================================
MODULE 2: API INTEGRATION ENGINE - DEMO
============================================================

============================================================
DEMO 1: Email Service (Gmail SMTP)
============================================================

1. Sending test email to yourself...
   ✓ Email sent successfully!
   ✓ Recipient: your.email@gmail.com
   ✓ Subject: Test Email from API Integration Module

2. Validating email addresses...
   ✓ Valid: valid@example.com
   ✗ Invalid: invalid-email
   ✓ Valid: another.valid@test.org

============================================================
DEMO 2: Storage Service (Mock S3)
============================================================

1. Uploading file to storage...
   ✓ File uploaded successfully!
   ✓ Bucket: demo-bucket
   ✓ Key: documents/test_document.txt
   ✓ URL: mock-s3://demo-bucket/documents/test_document.txt

2. Listing files in bucket...
   ✓ Found 1 file(s):
      - documents/test_document.txt (0.0 MB)

3. Generating presigned URL...
   ✓ URL: mock-s3://demo-bucket/documents/test_document.txt?expires=...

4. Downloading file...
   ✓ File downloaded to: collected_data/test_files/downloaded_test.txt

============================================================
DEMO 3: Signature Service (Mock DocuSign)
============================================================

1. Creating signature envelope...
   ✓ Envelope created successfully!
   ✓ Envelope ID: mock-env-...
   ✓ Status: sent
   ✓ Signers: 2

2. Checking envelope status...
   ✓ Envelope Status: sent
   ✓ Created: 2024-11-06T...
   Note: In real DocuSign, you'd wait for signers to complete

3. Simulating signed document download...
   Note: Mocking completion for demo purposes...
   ✓ In production, you'd check status and download when completed

============================================================
DEMO 4: Search Service (Mock Google Search)
============================================================

1. Performing web search...
   ✓ Found 5 results:
      1. Result 1: Python data collection - Wikipedia
         URL: https://www.wikipedia.org/search?q=Python+data+collection&result=1
         Snippet: Learn about Python data collection with comprehensive guides and...

      ...

2. Performing image search...
   ✓ Found 3 image results:
      1. Image 1: Python logo
         Image URL: https://picsum.photos/id/10/800/600
         Dimensions: 800x600

============================================================
DEMO COMPLETED!
============================================================
```

### Check Results:

- Mock S3 storage: `collected_data/mock_s3/`
- Signature envelopes: `collected_data/signatures/`
- API call logs: `logs/api_call_log.jsonl`
- Your Gmail inbox (for test email)

## Troubleshooting

### Issue: "Authentication failed" when connecting to Gmail

**Solution**:
1. Make sure you're using an App Password, not your regular Gmail password
2. Check that 2-Step Verification is enabled
3. Verify the password in `.env` has no spaces
4. Try generating a new App Password

### Issue: "Module not found" errors

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Selenium/Chrome driver errors

**Solution**:
The `webdriver-manager` package automatically downloads the correct Chrome driver. If you see errors:
1. Make sure Chrome browser is installed
2. Or switch to Firefox in `config/collection_config.yaml`:
   ```yaml
   browser:
     driver: "firefox"  # Change from "chrome"
   ```

### Issue: "python-magic" import errors on Windows

**Solution**:
Windows users should have `python-magic-bin` installed automatically. If you still see errors:
```bash
pip uninstall python-magic
pip install python-magic-bin
```

### Issue: No emails found during email monitoring

**Solution**:
This is normal if you don't have emails matching the filters. To test:
1. Send yourself an email with "Daily Report" in the subject
2. Or update the filters in `config/collection_config.yaml` to match your actual emails

## View Logs

All operations are logged in JSONL format (one JSON object per line):

```bash
# Module 1 logs
cat logs/collection_log.jsonl

# Module 2 logs
cat logs/api_call_log.jsonl
```

You can also open these files in any text editor or parse them with Python:

```python
import json

with open('logs/api_call_log.jsonl', 'r') as f:
    for line in f:
        log_entry = json.loads(line)
        print(f"{log_entry['timestamp']} - {log_entry['action']} - {log_entry['status']}")
```

## Next Steps

### For Your Homework Submission

1. Run both demo scripts successfully
2. Take screenshots of the output
3. Include sample collected data in your submission
4. Show the log files
5. Explain the pluggable architecture in your report

### To Switch to Real Paid Services

When you're ready to use real APIs instead of mocks:

1. **SendGrid** (instead of Gmail SMTP):
   - Sign up at https://sendgrid.com
   - Get API key
   - Update `config/api_config.yaml`:
     ```yaml
     email_service:
       provider: "SendGrid"
       sendgrid:
         api_key: "${ENV:SENDGRID_API_KEY}"
     ```

2. **AWS S3** (instead of Mock S3):
   - Create AWS account
   - Create S3 bucket
   - Get access keys
   - Update `config/api_config.yaml`:
     ```yaml
     storage_service:
       provider: "AWSS3"
       aws_s3:
         access_key_id: "${ENV:AWS_ACCESS_KEY_ID}"
         secret_access_key: "${ENV:AWS_SECRET_ACCESS_KEY}"
         region: "us-east-1"
         default_bucket: "my-bucket"
     ```

3. **DocuSign** (instead of Mock DocuSign):
   - Sign up at https://www.docusign.com
   - Get integration key
   - Update config similarly

4. **Google Search API** (instead of Mock):
   - Enable Google Custom Search API
   - Get API key and search engine ID
   - Update config similarly

The code doesn't change - only the configuration!

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review the logs in `logs/` directory
3. Check the configuration files in `config/`
4. Verify your `.env` file has correct credentials

Good luck with your homework! 🚀
