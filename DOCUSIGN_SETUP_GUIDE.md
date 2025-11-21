# DocuSign Setup Guide

This guide will help you complete the DocuSign integration setup for your project.

## Your DocuSign Credentials

You have:
- **Integration Key (Client ID)**: `c05831ad-c8a1-462c-a0f0-eb273e69d096`
- **User ID (API Username)**: `e8623f90-79d2-4e76-bd07-5b79b2ff087f`

## Steps to Complete Setup

### Step 1: Generate RSA Key Pair

You need to generate an RSA key pair for JWT authentication:

1. Go to your DocuSign Developer Account: https://admindemo.docusign.com/
2. Navigate to: **Settings** → **Apps and Keys**
3. Find your integration: `c05831ad-c8a1-462c-a0f0-eb273e69d096`
4. Click **"Add RSA Keypair"** button
5. **IMPORTANT**: Click **"Download Private Key"** and save it to your computer
   - Save as: `docusign_private_key.txt`
   - Keep this file secure - never commit it to version control!
   - Suggested location: `C:\Users\invet\Desktop\docusign_private_key.txt`

### Step 2: Get Your Account ID

1. Still in DocuSign admin panel: https://admindemo.docusign.com/
2. Go to: **Settings** → **Organization Administration** → **Account**
3. Look for **"API Account ID"** or **"Account ID"**
4. Copy this value (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)

### Step 3: Grant Consent (One-Time Setup)

DocuSign requires you to grant consent to your integration. This is a one-time step:

1. Open this URL in your browser (replace YOUR_INTEGRATION_KEY):

```
https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation&client_id=c05831ad-c8a1-462c-a0f0-eb273e69d096&redirect_uri=https://localhost
```

2. Log in with your DocuSign Developer account
3. Click **"Allow Access"** to grant consent
4. You'll be redirected to `https://localhost/?code=...` (this will show an error page, which is expected)
5. The consent is now granted - you don't need the code

### Step 4: Update Your .env File

Edit your `.env` file (create it from `.env.example` if you don't have one):

```bash
# DocuSign Configuration
DOCUSIGN_INTEGRATION_KEY=c05831ad-c8a1-462c-a0f0-eb273e69d096
DOCUSIGN_USER_ID=e8623f90-79d2-4e76-bd07-5b79b2ff087f
DOCUSIGN_ACCOUNT_ID=your_account_id_here  # From Step 2
DOCUSIGN_PRIVATE_KEY_PATH=C:\Users\invet\Desktop\docusign_private_key.txt  # Your private key path
```

**Important**: Replace `your_account_id_here` with the actual Account ID from Step 2.

### Step 5: Update Configuration File

Edit `config/api_config.yaml` and change the signature service provider:

```yaml
signature_service:
  # Change from "MockDocuSign" to "DocuSign"
  provider: "DocuSign"
```

### Step 6: Test the Integration

Run the simple test script to verify everything works:

```bash
python examples/test_docusign_simple.py
```

This will:
1. Test the connection to DocuSign API
2. Create a simple test PDF
3. Send it for signature to an email you specify

## Troubleshooting

### Error: "consent_required"
- You need to complete Step 3 (Grant Consent)
- Make sure you're using the correct integration key in the consent URL

### Error: "Private key file not found"
- Check that the path in `DOCUSIGN_PRIVATE_KEY_PATH` is correct
- Make sure you downloaded the private key in Step 1
- Use absolute path (e.g., `C:\Users\invet\Desktop\docusign_private_key.txt`)

### Error: "Account not found" or "User not found"
- Double-check your Account ID from Step 2
- Make sure you're using the **Demo/Developer** account, not production
- Verify User ID matches your API Username

### Error: "Invalid credentials"
- Verify all environment variables are set correctly
- Check that there are no extra spaces in your .env file
- Restart your Python environment after changing .env

## Testing with Demo Account

Your integration is set up for the **Demo environment**:
- Base URL: `https://demo.docusign.net/restapi`
- OAuth Host: `account-d.docusign.com`

**Documents signed in demo mode are for testing only and are not legally binding.**

## Full Workflow Demo

Once the simple test works, you can run the complete workflow:

```bash
python examples/demo_docusign_workflow.py
```

This will:
1. Search Google for a topic
2. Scrape content from top result
3. Generate a professional PDF
4. Send it for signature via DocuSign

## Security Notes

⚠️ **NEVER commit these files to version control:**
- `.env` (contains your credentials)
- `docusign_private_key.txt` (your private key)

✓ These are already in `.gitignore` for your protection.

## Resources

- DocuSign Developer Center: https://developers.docusign.com/
- DocuSign API Reference: https://developers.docusign.com/docs/esign-rest-api/reference/
- JWT Authentication Guide: https://developers.docusign.com/platform/auth/jwt/

## Need Help?

If you encounter issues:
1. Check the log file: `logs/api_call_log.jsonl`
2. Review the error messages carefully
3. Verify all setup steps were completed
4. Test with the simple script first before the full workflow
