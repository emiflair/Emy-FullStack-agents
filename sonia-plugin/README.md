# Sonia AI Assistant

Autonomous AI assistant plugin for OpenClaw with human-like capabilities.

## Capabilities

### Email (sonia@wazhop.com)
- **sonia_send_email** - Send emails to anyone
- **sonia_check_email** - Check and read incoming emails
- **sonia_reply_email** - Reply to emails

### Account Creation
- **sonia_create_account** - Create accounts on websites using browser automation
  - Fills signup forms automatically
  - Handles email verification
  - Stores credentials securely

### Social Media
- **sonia_social_post** - Post content with media to:
  - Twitter/X
  - LinkedIn
  - Instagram
  - Facebook
  - TikTok
- **sonia_social_engage** - Like, comment, share, follow

### Web Browsing
- **sonia_browse_web** - Full browser automation
  - Navigate to URLs
  - Click elements
  - Fill forms
  - Extract data
  - Take screenshots

### Task Automation
- **sonia_complete_task** - Execute complex multi-step tasks
  - Autonomous execution
  - Reports results via WhatsApp or email
- **sonia_schedule_task** - Schedule tasks for later
  - One-time or recurring
  - Uses system cron/at
- **sonia_research** - Research topics across the web
  - Multiple source compilation
  - Customizable depth and format

## Usage

### Via WhatsApp
Message Sonia on WhatsApp:
```
"Sonia, send an email to john@example.com with subject 'Meeting Tomorrow' and tell him about our 3pm meeting"
```

### Via OpenClaw CLI
```bash
openclaw agent --agent sonia -m "Create a LinkedIn post about AI trends in 2026"
```

### Direct API
```bash
curl -X POST http://localhost:18789/tools/sonia_send_email \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Hello", "body": "Test message"}'
```

## Configuration

Email: `sonia@wazhop.com` (Zoho)
Default WhatsApp: `+971551994544`
Workspace: `/opt/emy-fullstack/sonia-workspace`

## Requirements

- OpenClaw gateway running
- Chrome CDP service (headless browser)
- msmtp (email sending)
- fetchmail (email receiving)
