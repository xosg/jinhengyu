# How to Switch Between Email Providers

## ✅ **Setup Complete!**

You now have two email providers configured:
1. **Outlook** (h.jin@student.xu-university.de)
2. **QQ Mail** (inveta@qq.com)

---

## 🔄 **How to Switch (1 Line Change!)**

Open `.env` file and change **ONE variable**:

```bash
# ============================================================================
# EMAIL SERVICE CONFIGURATION
# ============================================================================
# Switch between email providers by changing this single variable:
# Options: "outlook", "qq"
EMAIL_PROVIDER=qq              👈 CHANGE THIS LINE!
```

### Switch to QQ Mail:
```bash
EMAIL_PROVIDER=qq
```

### Switch to Outlook:
```bash
EMAIL_PROVIDER=outlook
```

That's it! No other changes needed. The system automatically:
- ✅ Selects the correct SMTP server
- ✅ Uses the correct credentials
- ✅ Sends to the correct email address

---

## 📧 **Email Configurations**

### Outlook Configuration:
- **Server:** smtp.office365.com
- **Port:** 587 (STARTTLS)
- **User:** ${OUTLOOK_USER}
- **Password:** ${OUTLOOK_PASSWORD}

### QQ Mail Configuration:
- **Server:** smtp.qq.com
- **Port:** 465 (SSL)
- **User:** ${QQMAIL_USER}
- **Password:** ${QQMAIL_PASSWORD}

---

## 🧪 **How to Test**

### Test Current Provider:
```bash
python examples/test_qq_mail.py    # If EMAIL_PROVIDER=qq
```

### Test Full Workflow:
```bash
python examples/demo_comprehensive_workflow_enhanced.py
```

The workflow will automatically:
1. Send emails using the configured provider
2. Display "Provider: QQ Mail" or "Provider: OUTLOOK Mail" in output
3. Send to the correct email address

---

## 📝 **Current Configuration**

**Active Provider:** QQ Mail (EMAIL_PROVIDER=qq)

**Configured Emails:**
- Outlook: h.jin@student.xu-university.de
- QQ Mail: inveta@qq.com ✅ (Currently Active)

---

##  **Example Workflow Output**

When using QQ Mail:
```
[Step 6/7] Enhanced Email Notification
--------------------------------------------------------------------------------
  [OK] HTML email sent to: inveta@qq.com
  - Provider: QQ Mail                          👈 Confirms active provider
  -   [+] Screenshots embedded in email
  -   [+] 1 attachment(s) included
```

---

## 🔧 **Technical Details**

### File Locations:
- **Configuration:** `.env` (EMAIL_PROVIDER variable)
- **SMTP Settings:** `config/api_config.yaml`
- **Email Service:** `src/api_integration/email_service.py`

### How It Works:
1. `EMAIL_PROVIDER` in `.env` is read by `create_email_service()`
2. Factory function maps "qq" → QQMailSMTP, "outlook" → OutlookSMTP
3. Correct SMTP config is loaded from `api_config.yaml`
4. Credentials are resolved from environment variables

---

## ⚠️ **Important Notes**

1. **QQ Mail** uses SSL on port 465 (not STARTTLS)
2. **Outlook** uses STARTTLS on port 587
3. System handles the difference automatically
4. If EMAIL_PROVIDER is not set, defaults to Outlook
5. QQ Mail authorization code is NOT your login password (it's from SMTP settings)

---

## 🎯 **Quick Reference**

| Provider | .env Setting | Email | Port | Protocol |
|----------|-------------|-------|------|----------|
| Outlook  | `EMAIL_PROVIDER=outlook` | h.jin@student.xu-university.de | 587 | STARTTLS |
| QQ Mail  | `EMAIL_PROVIDER=qq` | inveta@qq.com | 465 | SSL |

---

**That's it!** Switch providers with a single line change in `.env` 🚀
