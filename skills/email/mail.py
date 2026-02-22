#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich"]
# ///

"""
Email skill - Check inbox, read messages, send replies
rosemary@harrell-pena-amalgamated.com via Spacemail
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
    """Extract plain text body from email"""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode('utf-8', errors='replace')
    return "(no text body)"

def cmd_inbox(limit=10):
    """Show inbox summary"""
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    imap.login(LOGIN_EMAIL, get_password())
    imap.select('INBOX')

    status, messages = imap.search(None, 'ALL')
    msg_nums = messages[0].split()

    console.print(f"\n[bold]Inbox: {len(msg_nums)} messages[/bold]\n")

    if not msg_nums:
        console.print("[dim]No messages[/dim]")
        imap.logout()
        return

    # Show most recent first
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("From", width=30)
    table.add_column("Subject", width=40)
    table.add_column("Date", width=20)

    for num in reversed(msg_nums[-limit:]):
        status, msg_data = imap.fetch(num, '(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])')
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

            table.add_row(num.decode(), from_addr, subject, date_str)

    console.print(table)
    imap.logout()

def cmd_read(msg_num):
    """Read a specific message"""
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    imap.login(LOGIN_EMAIL, get_password())
    imap.select('INBOX')

    status, msg_data = imap.fetch(str(msg_num).encode(), '(RFC822)')

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

    console.print(f"[green]Sent to {to_addr}[/green]")

def cmd_reply(msg_num, body):
    """Reply to a message"""
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    imap.login(LOGIN_EMAIL, get_password())
    imap.select('INBOX')

    status, msg_data = imap.fetch(str(msg_num).encode(), '(RFC822)')

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
        console.print("  email read <num>          Read message by number")
        console.print("  email send <to> <subj>    Send email (body from stdin or arg)")
        console.print("  email reply <num>         Reply to message (body from stdin or arg)")
        console.print()
        return

    cmd = sys.argv[1].lower()

    try:
        if cmd == 'inbox':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            cmd_inbox(limit)

        elif cmd == 'read':
            if len(sys.argv) < 3:
                console.print("[red]Error: specify message number[/red]")
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
                console.print("[red]Error: specify message number[/red]")
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
