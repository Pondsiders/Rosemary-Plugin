#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich", "html2text"]
# ///

"""
Email skill - Check inbox, read messages, send replies
rosemary@harrell-pena-amalgamated.com via Spacemail

Message numbering: 1 = newest, 2 = second newest, etc.
This matches how the inbox displays (most recent first).
"""

import sys
import os
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import formatdate, make_msgid, parsedate_to_datetime
from datetime import datetime
from rich.console import Console
from rich.table import Table
import html2text

# Spacemail configuration
IMAP_SERVER = "mail.spacemail.com"
SMTP_SERVER = "mail.spacemail.com"
LOGIN_EMAIL = "rosemary@harrell-pena-amalgamated.com"
SEND_AS = "rosemary@harrell-pena-amalgamated.com"


def get_password() -> str:
    """Retrieve email password from environment"""
    password = os.environ.get("SPACEMAIL_PASSWORD")
    if not password:
        raise RuntimeError("SPACEMAIL_PASSWORD not set in environment")
    return password

console = Console()

# HTML to text converter (reuse instance)
_h2t = html2text.HTML2Text()
_h2t.ignore_links = False
_h2t.ignore_images = True
_h2t.body_width = 78


def decode_mime_header(header):
    """Decode MIME encoded header"""
    if not header:
        return ""
    decoded_parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def get_body(msg):
    """Extract text body from email.

    Tries text/plain first. Falls back to text/html converted via html2text.
    """
    html_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='replace')
            elif content_type == 'text/html' and html_body is None:
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode('utf-8', errors='replace')
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode('utf-8', errors='replace')
            if content_type == 'text/plain':
                return text
            elif content_type == 'text/html':
                html_body = text

    # Fall back to HTML -> plaintext conversion
    if html_body:
        return _h2t.handle(html_body).strip()

    return "(no text body)"


def _get_reversed_nums(imap) -> list[bytes]:
    """Get all IMAP message numbers, newest first."""
    status, messages = imap.search(None, 'ALL')
    msg_nums = messages[0].split()
    return list(reversed(msg_nums))


def _resolve_msg_num(imap, logical_num: int) -> bytes:
    """Convert logical message number (1=newest) to IMAP message number."""
    reversed_nums = _get_reversed_nums(imap)
    if not reversed_nums:
        raise ValueError("Inbox is empty")
    idx = logical_num - 1
    if idx < 0 or idx >= len(reversed_nums):
        raise ValueError(f"Message {logical_num} not found (inbox has {len(reversed_nums)} messages)")
    return reversed_nums[idx]


def cmd_inbox(limit=10):
    """Show inbox summary"""
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    imap.login(LOGIN_EMAIL, get_password())
    imap.select('INBOX')

    reversed_nums = _get_reversed_nums(imap)

    console.print(f"\n[bold]📬 Inbox: {len(reversed_nums)} messages[/bold]\n")

    if not reversed_nums:
        console.print("[dim]No messages[/dim]")
        imap.logout()
        return

    # Show most recent first, with logical numbering (1 = newest)
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("From", width=30)
    table.add_column("Subject", width=40)
    table.add_column("Date", width=20)

    for logical_num, imap_num in enumerate(reversed_nums[:limit], 1):
        status, msg_data = imap.fetch(imap_num, '(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])')
        if msg_data[0]:
            header = msg_data[0][1].decode('utf-8', errors='replace')

            from_addr = ""
            subject = ""
            date_str = ""

            for line in header.split('\n'):
                line = line.strip()
                if line.lower().startswith('from:'):
                    from_addr = decode_mime_header(line[5:].strip())[:30]
                elif line.lower().startswith('subject:'):
                    subject = decode_mime_header(line[8:].strip())[:40]
                elif line.lower().startswith('date:'):
                    date_str = line[5:].strip()[:20]

            table.add_row(str(logical_num), from_addr, subject, date_str)

    console.print(table)
    imap.logout()

def cmd_read(msg_num):
    """Read a specific message (1 = newest)"""
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    imap.login(LOGIN_EMAIL, get_password())
    imap.select('INBOX')

    imap_num = _resolve_msg_num(imap, int(msg_num))
    status, msg_data = imap.fetch(imap_num, '(RFC822)')

    if not msg_data[0]:
        console.print(f"[red]Message {msg_num} not found[/red]")
        imap.logout()
        return

    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)

    from_addr = decode_mime_header(msg['From'])
    to_addr = decode_mime_header(msg['To'])
    subject = decode_mime_header(msg['Subject'])
    date = msg['Date']
    body = get_body(msg)

    console.print(f"\n[bold]Message {msg_num}[/bold]")
    console.print(f"[dim]{'='*60}[/dim]")
    console.print(f"[bold]From:[/bold] {from_addr}")
    console.print(f"[bold]To:[/bold] {to_addr}")
    console.print(f"[bold]Subject:[/bold] {subject}")
    console.print(f"[bold]Date:[/bold] {date}")
    console.print(f"[dim]{'='*60}[/dim]\n")
    console.print(body)
    console.print()

    imap.logout()

def cmd_send(to_addr, subject, body):
    """Send an email"""
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = f'Rosemary <{SEND_AS}>'
    msg['To'] = to_addr
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain='harrell-pena-amalgamated.com')

    smtp = smtplib.SMTP_SSL(SMTP_SERVER, 465)
    smtp.login(LOGIN_EMAIL, get_password())
    smtp.send_message(msg)
    smtp.quit()

    console.print(f"[green]✓ Email sent to {to_addr}[/green]")

def cmd_reply(msg_num, body):
    """Reply to a message (1 = newest)"""
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    imap.login(LOGIN_EMAIL, get_password())
    imap.select('INBOX')

    imap_num = _resolve_msg_num(imap, int(msg_num))
    status, msg_data = imap.fetch(imap_num, '(RFC822)')

    if not msg_data[0]:
        console.print(f"[red]Message {msg_num} not found[/red]")
        imap.logout()
        return

    raw = msg_data[0][1]
    original = email.message_from_bytes(raw)

    # Get reply-to or from address
    reply_to = original['Reply-To'] or original['From']
    original_subject = decode_mime_header(original['Subject'])
    original_body = get_body(original)
    original_date = original['Date']

    # Build reply subject
    if not original_subject.lower().startswith('re:'):
        reply_subject = f"Re: {original_subject}"
    else:
        reply_subject = original_subject

    # Build reply body with quote
    quoted = '\n'.join(f'> {line}' for line in original_body.split('\n')[:20])
    full_body = f"{body}\n\nOn {original_date}, {original['From']} wrote:\n{quoted}"

    imap.logout()

    # Send the reply
    cmd_send(reply_to, reply_subject, full_body)

def main():
    if len(sys.argv) < 2:
        console.print("\n[bold]Email Skill[/bold] - rosemary@harrell-pena-amalgamated.com")
        console.print("\nUsage:")
        console.print("  email inbox [limit]       Show inbox (default: 10 messages)")
        console.print("  email read <num>          Read message (1 = newest)")
        console.print("  email send <to> <subj>    Send email (body from stdin or arg)")
        console.print("  email reply <num>         Reply to message (1 = newest)")
        console.print()
        return

    cmd = sys.argv[1].lower()

    try:
        if cmd == 'inbox':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            cmd_inbox(limit)

        elif cmd == 'read':
            if len(sys.argv) < 3:
                console.print("[red]Error: specify message number (1 = newest)[/red]")
                return
            cmd_read(sys.argv[2])

        elif cmd == 'send':
            if len(sys.argv) < 4:
                console.print("[red]Error: specify recipient and subject[/red]")
                console.print("Usage: email send <to> <subject> [body]")
                return
            to_addr = sys.argv[2]
            subject = sys.argv[3]
            body = sys.argv[4] if len(sys.argv) > 4 else sys.stdin.read()
            cmd_send(to_addr, subject, body)

        elif cmd == 'reply':
            if len(sys.argv) < 3:
                console.print("[red]Error: specify message number (1 = newest)[/red]")
                return
            msg_num = sys.argv[2]
            body = sys.argv[3] if len(sys.argv) > 3 else sys.stdin.read()
            cmd_reply(msg_num, body)

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise

if __name__ == '__main__':
    main()
