import os
import re
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.logger import log


SENDER_EMAIL  = os.getenv("ALPHA_EMAIL", "YOUR_EMAIL")
APP_PASSWORD  = os.getenv("ALPHA_EMAIL_PASSWORD", "YOUR_APP_PASS")
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587

_draft = {
    "to":      "",
    "subject": "",
    "body":    "",
}

def _extract_email_address(text: str) -> str:
    m = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    return m.group(0) if m else ""


def _extract_recipient_name(text: str) -> str:
    m = re.search(
        r"(?:to|for|email|mail)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _check_credentials() -> str | None:
    if not SENDER_EMAIL or not APP_PASSWORD:
        return (
            "Email credentials not set. "
            "Set the ALPHA_EMAIL and ALPHA_EMAIL_PASSWORD environment variables, "
            "or edit tasks/email_tasks.py directly."
        )
    return None



def _send_smtp(to: str, subject: str, body: str) -> tuple[bool, str]:
    err = _check_credentials()
    if err:
        return False, err
    if not to:
        return False, "No recipient address — cannot send."

    try:
        msg = MIMEMultipart()
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = to
        msg["Subject"] = subject or "(no subject)"
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to, msg.as_string())

        log(f"[Email] Sent to {to} — subject: {subject}")
        return True, f"Email sent to {to}."

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Check your App Password."
    except smtplib.SMTPRecipientsRefused:
        return False, f"Recipient refused: {to}. Check the address."
    except Exception as e:
        return False, f"Email send failed: {e}"


def draft_and_send_email(raw: str) -> str:
    recipient_email = _extract_email_address(raw)
    recipient_name  = _extract_recipient_name(raw)

    subject_hint = ""
    m = re.search(r"(?:about|regarding|re|subject)\s+(.+)", raw, re.IGNORECASE)
    if m:
        subject_hint = m.group(1).strip()

    if not SENDER_EMAIL or not APP_PASSWORD:
        import urllib.parse, webbrowser
        to  = recipient_email or (recipient_name + "@gmail.com" if recipient_name else "")
        url = (f"mailto:{to}"
               f"?subject={urllib.parse.quote(subject_hint)}"
               f"&body=")
        webbrowser.open(url)
        tip = ("Tip: set ALPHA_EMAIL and ALPHA_EMAIL_PASSWORD env vars "
               "to enable direct send without opening a mail client.")
        return (f"Opened mail client for {recipient_name or recipient_email or 'recipient'}. "
                f"{tip}")

    def _interactive():
        print("\n" + "─" * 56)
        print("  ALPHA 2.0  —  Email Composer")
        print("─" * 56)

        to = recipient_email
        if not to:
            name = recipient_name or input("  Recipient name or email: ").strip()
            if "@" not in name:
                to = input(f"  Email address for '{name}': ").strip()
            else:
                to = name

        print(f"  To:      {to}")
        subj = subject_hint or input("  Subject: ").strip()
        print(f"  Subject: {subj}")
        print("  Body (type your message, then press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        body = "\n".join(lines).strip()

        print()
        print(f"  To:      {to}")
        print(f"  Subject: {subj}")
        print(f"  Body:    {body[:80]}{'…' if len(body) > 80 else ''}")
        confirm = input("\n  Send this email? (yes / no): ").strip().lower()

        if confirm in ("yes", "y", "send"):
            ok, msg = _send_smtp(to, subj, body)
            print(f"\n  {'✓' if ok else '✗'}  {msg}")
        else:
            print("  Email cancelled.")
        print("─" * 56 + "\n")

    threading.Thread(target=_interactive, daemon=True).start()

    recipient_display = recipient_name or recipient_email or "recipient"
    return (f"Email composer opened in the terminal for {recipient_display}. "
            f"Fill in the details there.")


def send_quick_email(to: str, subject: str, body: str) -> str:
    ok, msg = _send_smtp(to, subject, body)
    return msg


def check_email_config() -> str:
    if SENDER_EMAIL and APP_PASSWORD:
        return f"Email configured: sending as {SENDER_EMAIL} via Gmail SMTP."
    return ("Email not configured. Set ALPHA_EMAIL and "
            "ALPHA_EMAIL_PASSWORD environment variables.")
