# QQ Mail Setup Guide (QQ邮箱设置指南)

This guide shows you how to set up QQ Mail authorization code for this project.

## 什么是授权码？(What is Authorization Code?)

QQ Mail requires an **authorization code (授权码)** instead of your regular password for third-party applications. This is similar to Gmail's App Password and provides better security.

## 步骤 1: 生成授权码 (Step 1: Generate Authorization Code)

### 中文步骤：

1. **登录QQ邮箱**
   - 访问：https://mail.qq.com
   - 使用您的QQ号码和密码登录

2. **进入设置**
   - 点击顶部的 "设置"
   - 选择 "账户"

3. **开启IMAP/SMTP服务**
   - 找到 "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
   - 开启 **IMAP/SMTP服务**（如果还没开启）
   - 可能需要发送短信验证

4. **生成授权码**
   - 在同一页面，找到 "生成授权码"
   - 点击 "生成授权码"
   - 按要求发送短信验证
   - **保存显示的16位授权码**（例如：abcdefghijklmnop）

### English Steps:

1. **Login to QQ Mail**
   - Visit: https://mail.qq.com
   - Login with your QQ number and password

2. **Open Settings**
   - Click "Settings" (设置) at the top
   - Select "Account" (账户)

3. **Enable IMAP/SMTP Service**
   - Find "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV Services"
   - Enable **IMAP/SMTP Service** (if not already enabled)
   - May require SMS verification

4. **Generate Authorization Code**
   - On the same page, find "Generate Authorization Code" (生成授权码)
   - Click to generate
   - Follow SMS verification
   - **Save the 16-character authorization code** (e.g., abcdefghijklmnop)

## 步骤 2: 配置项目 (Step 2: Configure Project)

### 1. 复制环境变量模板 (Copy Environment Template)

```bash
cp .env.example .env
```

### 2. 编辑 .env 文件 (Edit .env File)

Open `.env` file and add your credentials:

```bash
# Replace with your actual QQ email and authorization code
QQMAIL_USER=your_qq_number@qq.com
QQMAIL_AUTH_CODE=abcdefghijklmnop
```

**重要提示 (Important Notes):**
- ✅ Use your **full email address** (e.g., 123456789@qq.com)
- ✅ Use the **16-character authorization code**, not your QQ password
- ✅ Remove any spaces from the authorization code
- ❌ Never commit .env file to version control (it's in .gitignore)

### 示例 (Example):

If your QQ number is 123456789 and authorization code is abcdefghijklmnop:

```bash
QQMAIL_USER=123456789@qq.com
QQMAIL_AUTH_CODE=abcdefghijklmnop
```

## 步骤 3: 测试连接 (Step 3: Test Connection)

Run the demo scripts to test:

```bash
# Test Module 1 (Email monitoring with IMAP)
python examples/demo_collection.py

# Test Module 2 (Email sending with SMTP)
python examples/demo_api.py
```

## 常见问题 (Troubleshooting)

### 问题1：Authentication failed

**原因 (Reason):**
- Using wrong password (should use authorization code)
- Authorization code has spaces
- IMAP/SMTP service not enabled

**解决方法 (Solution):**
1. Make sure you're using the **authorization code**, not your QQ password
2. Check that IMAP/SMTP service is enabled in QQ Mail settings
3. Verify there are no spaces in the authorization code in .env file
4. Try generating a new authorization code

### 问题2：Connection timeout

**原因 (Reason):**
- Firewall blocking port 993 (IMAP) or 587 (SMTP)
- Network issues

**解决方法 (Solution):**
1. Check your firewall settings
2. Try a different network
3. Verify you can access mail.qq.com in browser

### 问题3：No emails fetched

**原因 (Reason):**
- Filters in config don't match any emails
- Date range too narrow

**解决方法 (Solution):**
1. Check `config/collection_config.yaml` filters
2. Send yourself a test email to match the filters
3. Increase `days_back` in filters configuration

## QQ Mail vs Gmail 对比 (QQ Mail vs Gmail Comparison)

| Feature | QQ Mail | Gmail |
|---------|---------|-------|
| Authorization | 授权码 (Authorization Code) | App Password |
| IMAP Server | imap.qq.com:993 | imap.gmail.com:993 |
| SMTP Server | smtp.qq.com:587 | smtp.gmail.com:587 |
| Free Tier | ✅ Free | ✅ Free |
| Phone Required | Yes (for authorization code) | Yes (for 2FA) |
| Mainland China | ✅ Works well | ⚠️ May be blocked |

## 支持的邮箱 (Supported Mail Services)

This project currently supports:
- ✅ QQ Mail (qq.com)
- ✅ Gmail (gmail.com) - if you have access
- 🔜 163 Mail (163.com) - can be added if needed
- 🔜 Outlook (outlook.com) - can be added if needed

Want to add another mail service? It's easy! Just update the config files with the new IMAP/SMTP server settings.

## 更多帮助 (More Help)

If you encounter other issues:

1. Check the main `SETUP_GUIDE.md` file
2. Review logs in `logs/` directory
3. Verify your configuration in `config/` directory
4. Try generating a new authorization code

## 安全提示 (Security Tips)

- 🔒 Never share your authorization code
- 🔒 Don't commit .env file to git
- 🔒 Regenerate authorization code periodically
- 🔒 Revoke unused authorization codes in QQ Mail settings

Good luck! 祝你好运！🚀
