# Google Custom Search API Setup Guide

⚠️ **IMPORTANT SECURITY WARNING** ⚠️

You shared your API key publicly in our conversation: `AIzaSyCmt-qmMSyEjQhCQBYWkmNpPnK-scZvXYQ`

**YOU MUST REGENERATE IT IMMEDIATELY** to prevent unauthorized usage!

---

## Step 1: Regenerate Your API Key (CRITICAL!)

1. Go to: https://console.cloud.google.com/apis/credentials
2. Find your existing API key (`AIzaSyCmt-qmMSyEjQhCQBYWkmNpPnK-scZvXYQ`)
3. Click the **three dots** (⋮) next to it → **Delete**
4. Click **"+ CREATE CREDENTIALS"** → **API Key**
5. Copy the new key (looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX`)
6. **NEVER share this key publicly again!**

---

## Step 2: Create a Custom Search Engine

1. Go to: https://programmablesearchengine.google.com/
2. Click **"Add"** or **"Create a new search engine"**
3. Fill in the form:
   - **Search engine name**: `Multi-Source Data Scraper`
   - **What to search**: Select **"Search the entire web"**
   - ✅ Check **"Image search"** (optional, for image search feature)
   - ✅ Check **"Search suggestions"** (optional)
4. Click **"Create"**
5. Click **"Customize"** → Copy the **Search engine ID**
   - Looks like: `a12b34c56d78e90f1`
   - Or: `0123456789abcdef:ghijklmnop`

---

## Step 3: Update Your .env File

Open `C:\Users\invet\Desktop\jinhengyu\.env` and update:

```bash
# Google Custom Search API Credentials
GOOGLE_API_KEY=YOUR_NEW_REGENERATED_API_KEY_HERE
GOOGLE_SEARCH_ENGINE_ID=YOUR_SEARCH_ENGINE_ID_HERE
```

**Example:**
```bash
GOOGLE_API_KEY=AIzaSyDEMO_1234567890_NEWKEY
GOOGLE_SEARCH_ENGINE_ID=a12b34c56d78e90f1
```

---

## Step 4: Enable Google Custom Search API

1. Go to: https://console.cloud.google.com/apis/library
2. Search for: **"Custom Search API"**
3. Click on **"Custom Search API"**
4. Click **"ENABLE"**
5. Wait a few seconds for activation

---

## Step 5: Test Your Setup

### Test with Demo Script:

```bash
python examples/demo_api.py
```

Look for the "DEMO 4: Search Service" section. If configured correctly, it will use real Google Search!

### Or Test Directly:

```python
from src.api_integration.search_service import create_search_service

# Make sure provider is set to "GoogleSearch" in config
search = create_search_service()
results = search.search("Python tutorials", num_results=5)

for result in results:
    print(f"{result['title']}: {result['url']}")
```

---

## Step 6: Switch to Real Google Search (Optional)

To use the real API instead of mock:

1. Open `config/api_config.yaml`
2. Find the `search_service` section (around line 106)
3. Change:
   ```yaml
   provider: "MockGoogleSearch"  # Change this line
   ```
   To:
   ```yaml
   provider: "GoogleSearch"  # Use real API
   ```

---

## API Limits & Pricing

### Free Tier:
- ✅ **100 queries per day** (free)
- ✅ **10 results per query** (max)
- ✅ **10,000 queries per month** (after that, $5 per 1000 queries)

### Rate Limits:
- 100 queries per 100 seconds
- Monitor usage at: https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas

---

## What You Can Do With Google Search API

### 1. **Smart Website Discovery**
```python
from src.api_integration.search_service import GoogleSearchService

search = GoogleSearchService()
results = search.search("Python machine learning tutorials", num_results=10)

# Auto-discover websites to scrape
urls = [r['url'] for r in results]
# Then scrape these URLs automatically!
```

### 2. **Related Content Finder**
```python
# After scraping github.com/python
results = search.search("site:github.com python machine learning")
# Find similar GitHub repositories
```

### 3. **News Search**
```python
results = search.search_news("Python 3.13 release")
# Find latest articles to scrape
```

### 4. **Image Search**
```python
results = search.search_images("Python logo")
# Download related images
```

---

## Security Best Practices

### ✅ DO:
- Store API keys in `.env` file
- Add `.env` to `.gitignore`
- Regenerate keys if exposed
- Use API key restrictions (HTTP referrers, IP addresses)

### ❌ DON'T:
- Share API keys in conversations/emails
- Commit `.env` to git
- Hardcode keys in source code
- Leave keys unrestricted

### API Key Restrictions (Recommended):

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your API key
3. Under **"API restrictions"**:
   - Select **"Restrict key"**
   - Choose: **"Custom Search API"**
4. Under **"Application restrictions"** (optional):
   - Select **"IP addresses"**
   - Add your IP for extra security

---

## Troubleshooting

### Error: "API key not valid"
- ✅ Check you copied the key correctly
- ✅ Make sure API key is not restricted
- ✅ Verify Custom Search API is enabled

### Error: "Invalid search engine ID"
- ✅ Check the ID is copied correctly
- ✅ Verify the search engine exists at https://programmablesearchengine.google.com/

### Error: "Quota exceeded"
- ❌ You've used 100 queries today
- ✅ Wait until tomorrow (resets at midnight PST)
- ✅ Or switch back to MockGoogleSearch

### Error: "Module not found: googleapiclient"
```bash
pip install google-api-python-client
```

---

## Next Steps

Once set up, you can:

1. ✅ Replace mock Google Search with real API
2. ✅ Use the "Smart Website Discovery" feature I'm about to implement
3. ✅ Auto-find websites to scrape based on keywords
4. ✅ Demonstrate real Google API integration in your presentation

---

**Questions?** Check:
- Google Custom Search API Docs: https://developers.google.com/custom-search/v1/overview
- API Console: https://console.cloud.google.com/
- Programmable Search Engine: https://programmablesearchengine.google.com/

---

**REMEMBER**: Always regenerate exposed API keys! 🔒
