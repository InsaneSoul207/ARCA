import webbrowser, urllib.parse
import pyperclip
from core.logger import log

_reminders = []


def draft_email(recipient="", subject="", body=""):
    recipient = recipient or "example@email.com"
    subject   = subject or "Message from ARCA"
    body      = body or "Hello,"
    url = (f"mailto:{recipient}?subject={urllib.parse.quote(subject)}"
           f"&body={urllib.parse.quote(body)}")
    webbrowser.open(url)
    return f"Email draft opened for: {recipient}"

def copy_to_clipboard(text=""):
    text = text or "ARCA — Clipboard test"
    try:
        pyperclip.copy(text)
        return f'Copied to clipboard: "{text[:40]}..."'
    except Exception as e:
        return f"Clipboard error: {e}"

def set_reminder(text=""):
    import datetime
    reminder = {"time": datetime.datetime.now().strftime("%H:%M"), "text": text or "Check in"}
    _reminders.append(reminder)
    return f"Reminder set: '{reminder['text']}' at {reminder['time']}"

def show_reminders():
    if not _reminders:
        return "No reminders set."
    return "Reminders:\n" + "\n".join(f"  [{r['time']}] {r['text']}" for r in _reminders)