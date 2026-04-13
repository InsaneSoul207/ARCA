import os, re, threading, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.logger import log

OLLAMA_URL    = "http://localhost:11434/api/generate"
OLLAMA_MODEL  = "llama3"
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SENDER_EMAIL  = os.getenv("ALPHA_EMAIL", "YOUR_MAIL")
APP_PASSWORD  = os.getenv("ALPHA_EMAIL_PASSWORD", "YOUR_APP_PASS")


# ─────────────────────────────────────────────────────────────────────────────
# Ollama — plain text format (NO JSON to avoid control character errors)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_email(prompt: str, recipient_name: str = "",
                    tone: str = "professional") -> dict:
    """
    Ask Ollama to write a complete email.
    Returns {"subject": str, "body": str}.

    Uses SUBJECT:/BODY: plain-text format — avoids JSON entirely.
    JSON control-character errors are impossible with this approach.
    """
    import requests

    recipient_ctx = f"to {recipient_name}" if recipient_name else ""

    ollama_prompt = f"""You are an expert email writer. Write a complete email {recipient_ctx}.

Request: {prompt}
Tone: {tone}

Write your response in EXACTLY this format — two sections, nothing else:
SUBJECT: [your subject line here]
BODY:
[complete email body here — include a proper greeting, full paragraphs, and a sign-off]"""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model":   OLLAMA_MODEL,
            "prompt":  ollama_prompt,
            "stream":  False,
            "options": {"temperature": 0.4, "num_predict": 800}
        }, timeout=45)
        r.raise_for_status()
        raw = r.json().get("response", "").strip()

        if not raw:
            raise RuntimeError("Ollama returned an empty response.")

        log(f"[AIEmail] Response received ({len(raw)} chars)")

        # ── Parse SUBJECT: and BODY: sections ─────────────────────────────
        subject = ""
        body    = ""

        # Extract SUBJECT line
        subj_m = re.search(r"^SUBJECT:\s*(.+)", raw, re.IGNORECASE | re.MULTILINE)
        if subj_m:
            subject = subj_m.group(1).strip()

        # Extract BODY: everything after the BODY: marker
        body_m = re.search(r"^BODY:\s*\n?([\s\S]+)", raw, re.IGNORECASE | re.MULTILINE)
        if body_m:
            body = body_m.group(1).strip()

        # ── Fallbacks if format wasn't followed ────────────────────────────
        if not body and len(raw) > 30:
            # Ollama ignored format — use entire response as body
            body    = raw
            subject = f"Re: {prompt[:60]}"
            log("[AIEmail] Format not followed — using raw response as body", "WARN")

        if not subject:
            subject = f"Re: {prompt[:60]}"

        if not body or len(body) < 20:
            raise RuntimeError(
                "AI did not generate a usable email body. "
                "Try a more specific prompt, e.g. 'sick leave for tomorrow'."
            )

        log(f"[AIEmail] Subject: {subject[:50]} | Body: {len(body)} chars")
        return {"subject": subject, "body": body}

    except requests.ConnectionError:
        raise ConnectionError(
            "Ollama is not running.\n"
            "1. Download from https://ollama.com\n"
            "2. Run: ollama serve\n"
            "3. Run: ollama pull llama3"
        )
    except Exception as e:
        if "ConnectionError" in type(e).__name__:
            raise
        raise RuntimeError(f"Email generation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SMTP send
# ─────────────────────────────────────────────────────────────────────────────

def _smtp_send(to: str, subject: str, body: str) -> tuple[bool, str]:
    if not SENDER_EMAIL or not APP_PASSWORD:
        return False, (
            "Email not configured.\n"
            "Set these environment variables:\n"
            "  set ALPHA_EMAIL=yourname@gmail.com\n"
            "  set ALPHA_EMAIL_PASSWORD=your-16-char-app-password\n"
            "Get app password: myaccount.google.com → Security → App Passwords"
        )
    try:
        msg            = MIMEMultipart()
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo(); s.starttls()
            s.login(SENDER_EMAIL, APP_PASSWORD)
            s.sendmail(SENDER_EMAIL, to, msg.as_string())

        log(f"[Email] Sent to {to}")
        return True, f"Email sent to {to}."
    except smtplib.SMTPAuthenticationError:
        return False, (
            "Gmail authentication failed.\n"
            "Make sure ALPHA_EMAIL_PASSWORD is a 16-character App Password,\n"
            "not your actual Gmail password."
        )
    except Exception as e:
        return False, f"Send failed: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Command parsing
# ─────────────────────────────────────────────────────────────────────────────

def _detect_tone(raw: str) -> str:
    t = raw.lower()
    if any(w in t for w in ["formal", "professional", "official"]): return "formal and professional"
    if any(w in t for w in ["casual", "friendly", "informal"]):     return "casual and friendly"
    if any(w in t for w in ["apologetic", "sorry", "apology"]):     return "apologetic and sincere"
    if any(w in t for w in ["urgent", "asap", "immediately"]):      return "urgent and professional"
    return "professional"


def _extract_email_address(text: str) -> str:
    m = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    return m.group(0) if m else ""


def _extract_recipient_name(raw: str) -> str:
    patterns = [
        r"(?:email|mail|write to|compose.*?to|send.*?to)\s+(?:my\s+)?(\w[\w\s]{0,20}?)(?:\s+about|\s+asking|\s+saying|\s+regarding|$)",
        r"to\s+my\s+(\w+(?:\s+\w+)?)",
        r"to\s+(\w+)(?:\s+about|\s+asking|\s+for|\s+saying|$)",
    ]
    skip = {"email","mail","draft","compose","write","send","the","a","an",
            "my","ai","generate","create","me","for","about"}
    for p in patterns:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if name.lower() not in skip and len(name) > 1:
                return name.title()
    return ""


def _extract_prompt(raw: str) -> str:
    """Extract the writing intent — what the email is about."""
    # Try "about/for/asking/regarding X"
    m = re.search(r"\b(?:about|for|asking|regarding|saying)\s+(.+)", raw, re.IGNORECASE)
    if m:
        result = m.group(1).strip()
        if len(result) > 3:
            return result
    # Strip verbs and return the rest
    stripped = re.sub(
        r"\b(?:write|compose|draft|create|generate|send|email|mail|a|an|the|me|my|please)\b",
        "", raw, flags=re.IGNORECASE
    )
    stripped = re.sub(r"\s{2,}", " ", stripped).strip()
    return stripped if len(stripped) > 3 else raw


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def draft_and_send_email(raw: str) -> str:
    """
    Called by executor. Opens interactive terminal email composer.
    Generates COMPLETE email via Ollama, shows draft, then sends via SMTP.
    """
    recipient_email = _extract_email_address(raw)
    recipient_name  = _extract_recipient_name(raw)
    prompt          = _extract_prompt(raw)
    tone            = _detect_tone(raw)

    def _flow():
        W = 62
        print("\n" + "═" * W)
        print("  ALPHA 2.0  ·  AI Email Composer  (FRIDAY)")
        print("═" * W)

        # Gather recipient
        to = recipient_email
        if not to:
            name = recipient_name or input("  Recipient name or email: ").strip()
            if "@" not in name:
                try:
                    from config import CONTACTS
                    contact_email = CONTACTS.get(name.lower(), "")
                    if contact_email and "@" in str(contact_email):
                        to = contact_email
                        print(f"  Found: {name} → {to}")
                except Exception:
                    pass
                if not to:
                    to = input(f"  Email address for '{name}': ").strip()
            else:
                to = name

        rname = recipient_name or to.split("@")[0].replace(".", " ").title()
        print(f"\n  To:     {to}")
        print(f"  Tone:   {tone}")
        print(f"  About:  {prompt[:80]}")
        print(f"\n  ⏳ AI is writing the full email...")

        try:
            email_data = _generate_email(
                prompt         = prompt,
                recipient_name = rname,
                tone           = tone,
            )
        except (ConnectionError, RuntimeError) as e:
            print(f"\n  ✗ {e}")
            return

        # Display complete draft
        print()
        print("─" * W)
        print(f"  To:      {to}")
        print(f"  Subject: {email_data['subject']}")
        print(f"\n  Body:\n")
        for line in email_data["body"].split("\n"):
            print(f"    {line}")
        print("─" * W)

        action = input("\n  [S]end   [E]dit   [D]iscard  →  ").strip().lower()

        if action == "e":
            new_subj = input(f"\n  Subject [{email_data['subject']}]: ").strip()
            if new_subj:
                email_data["subject"] = new_subj
            print("  New body (Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            new_body = "\n".join(lines).strip()
            if new_body:
                email_data["body"] = new_body
            action = "s"

        if action in ("s", "send"):
            ok, msg = _smtp_send(to, email_data["subject"], email_data["body"])
            print(f"\n  {'✓' if ok else '✗'}  {msg}")
        else:
            print("\n  Email discarded.")

        print("═" * W + "\n")

    threading.Thread(target=_flow, daemon=True).start()
    rname = recipient_name or recipient_email or "the recipient"
    return (f"Email composer opened in the terminal for {rname}. "
            f"Check the terminal to review the AI draft and press S to send.")


# Alias used by some executor versions
def draft_email_with_ai(raw: str) -> str:
    return draft_and_send_email(raw)


def ai_email_status() -> str:
    import requests as req
    lines = []
    try:
        r = req.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        lines.append(f"Ollama:  running — models: {', '.join(models) or 'none'}")
    except Exception:
        lines.append("Ollama:  NOT running — start with: ollama serve")
    lines.append(
        f"Email:   {'configured (' + SENDER_EMAIL + ')' if SENDER_EMAIL else 'not set — add ALPHA_EMAIL env var'}"
    )
    return "\n".join(lines)
