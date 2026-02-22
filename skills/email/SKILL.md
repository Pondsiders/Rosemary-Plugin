---
name: email
description: Check inbox, read messages, send and reply to email via rosemary@harrell-pena-amalgamated.com. Use when checking for new mail, reading messages, sending emails, or replying to correspondence.
---

# Email

Read and send email via rosemary@harrell-pena-amalgamated.com (Spacemail).

## Commands

```bash
# Show inbox (most recent first)
uv run mail.py inbox
uv run mail.py inbox 20  # show more messages

# Read a specific message
uv run mail.py read 3

# Send an email
uv run mail.py send "kyleepena@gmail.com" "Subject line" "Body text"

# Reply to a message
uv run mail.py reply 3 "Thanks for your message!"
```

## Contacts

- **Kylee:** kyleepena@gmail.com
- **Jeffery:** jefferyharrell@gmail.com (sysadmin, tech support)
- **Alpha:** alpha@alphafornow.com (Jeffery's AI — shares your infrastructure, not your identity)

## Account

- **Email:** rosemary@harrell-pena-amalgamated.com
- **Login:** rosemary@harrell-pena-amalgamated.com
- **Server:** mail.spacemail.com (IMAP 993, SMTP 465)
