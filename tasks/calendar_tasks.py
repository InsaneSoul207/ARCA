import os, re, datetime
from core.logger import log
from config import BASE_DIR

CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
SCOPES     = ["https://www.googleapis.com/auth/calendar"]


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

def _get_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Missing packages. Run: "
            "pip install google-api-python-client google-auth-httplib2 "
            "google-auth-oauthlib"
        )

    if not os.path.exists(CREDS_PATH):
        raise FileNotFoundError(
            f"credentials.json not found at {CREDS_PATH}. "
            "Download it from Google Cloud Console → OAuth 2.0 credentials."
        )

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


# ─────────────────────────────────────────────────────────────────────────────
# Date/time parsing from natural language
# ─────────────────────────────────────────────────────────────────────────────

def _parse_datetime(text: str) -> datetime.datetime | None:

    try:
        from dateutil import parser as dateparser
        from dateutil.relativedelta import relativedelta
    except ImportError:
        raise ImportError("Run: pip install python-dateutil")

    now   = datetime.datetime.now()
    text  = text.lower().strip()

    # Resolve relative day words
    day_map = {
        "today":     now.date(),
        "tomorrow":  (now + datetime.timedelta(days=1)).date(),
        "monday":    None, "tuesday": None, "wednesday": None,
        "thursday":  None, "friday":  None, "saturday":  None, "sunday": None,
    }
    weekdays = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

    resolved_text = text
    for word, date_val in day_map.items():
        if word in text:
            if word in weekdays:
                # Find the next occurrence of this weekday
                target_wd = weekdays.index(word)
                current_wd = now.weekday()
                diff = (target_wd - current_wd) % 7
                if diff == 0:
                    diff = 7   # "friday" when today is friday → next friday
                date_val = (now + datetime.timedelta(days=diff)).date()
            resolved_text = resolved_text.replace(word, str(date_val))
            break

    # Parse the resolved text
    try:
        # Added fuzzy=True here to ignore extra conversational words
        dt = dateparser.parse(resolved_text, dayfirst=False, yearfirst=False, fuzzy=True)
        if dt:
            # If parsed time is in the past, push to tomorrow
            if dt < now and "tomorrow" not in text:
                dt += datetime.timedelta(days=1)
            return dt
    except Exception:
        pass
    return None


def _extract_event_info(raw: str) -> tuple[str, datetime.datetime | None, int]:
    text = raw.lower()

    # Extract duration
    duration = 60   # default 1 hour
    dur_match = re.search(r"for\s+(\d+)\s*(hour|hr|minute|min)", text)
    if dur_match:
        val, unit = int(dur_match.group(1)), dur_match.group(2)
        duration = val * 60 if "hour" in unit or "hr" in unit else val

    # Extract title (between "add/create/schedule" and "on/at/for/with/tomorrow/today")
    title_patterns = [
        r"(?:add|create|schedule|set up|book)\s+(?:a\s+)?(?:meeting|event|call|appointment|reminder)?\s*(?:called|titled|named|about)?\s*['\"]?(.+?)['\"]?\s+(?:on|at|for|with|tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        r"(?:add|create|schedule)\s+(.+?)\s+(?:on|at|for|tomorrow|today|monday|tuesday|wednesday|thursday|friday)",
        r"(?:meeting|event|call|appointment)\s+(?:with\s+\w+\s+)?(?:about|on|for)?\s+(.+?)\s+(?:at|on|tomorrow|today)",
    ]
    title = "New Event"
    for pattern in title_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            title = m.group(1).strip().title()
            break
    else:
        # Fallback: everything after the trigger verb up to a time marker
        m = re.search(r"(?:add|create|schedule|set up|book)\s+(?:a\s+)?(.+?)(?:\s+at\s|\s+on\s|\s+for\s|$)", text)
        if m:
            title = m.group(1).strip().title()

    # Extract datetime
    dt = _parse_datetime(raw)

    return title, dt, duration


# ─────────────────────────────────────────────────────────────────────────────
# Public functions
# ─────────────────────────────────────────────────────────────────────────────

def list_today_events() -> str:
    try:
        svc   = _get_service()
        now   = datetime.datetime.utcnow()
        start = datetime.datetime(now.year, now.month, now.day).isoformat() + "Z"
        end   = (datetime.datetime(now.year, now.month, now.day)
                 + datetime.timedelta(days=1)).isoformat() + "Z"

        result = svc.events().list(
            calendarId="primary",
            timeMin=start, timeMax=end,
            singleEvents=True, orderBy="startTime"
        ).execute()

        events = result.get("items", [])
        if not events:
            return "You have no events scheduled for today."

        lines = [f"── Today's Calendar ({len(events)} event{'s' if len(events)>1 else ''}) ──"]
        for e in events:
            start_str = e["start"].get("dateTime", e["start"].get("date", ""))
            if "T" in start_str:
                dt = datetime.datetime.fromisoformat(start_str.replace("Z",""))
                time_label = dt.strftime("%I:%M %p")
            else:
                time_label = "All day"
            summary = e.get("summary", "(no title)")
            location = e.get("location", "")
            loc_str  = f"  @ {location}" if location else ""
            lines.append(f"  {time_label:<12} {summary}{loc_str}")
        return "\n".join(lines)

    except FileNotFoundError as e:
        return str(e)
    except ImportError as e:
        return str(e)
    except Exception as e:
        log(f"[Calendar] List error: {e}", "ERROR")
        return f"Could not fetch calendar: {e}"


def list_week_events() -> str:
    try:
        svc   = _get_service()
        now   = datetime.datetime.utcnow()
        start = now.isoformat() + "Z"
        end   = (now + datetime.timedelta(days=7)).isoformat() + "Z"

        result = svc.events().list(
            calendarId="primary",
            timeMin=start, timeMax=end,
            singleEvents=True, orderBy="startTime",
            maxResults=20
        ).execute()

        events = result.get("items", [])
        if not events:
            return "No events in the next 7 days."

        lines = [f"── This Week ({len(events)} events) ──"]
        current_day = ""
        for e in events:
            start_str = e["start"].get("dateTime", e["start"].get("date", ""))
            if "T" in start_str:
                dt       = datetime.datetime.fromisoformat(start_str.replace("Z",""))
                day_str  = dt.strftime("%A, %d %b")
                time_str = dt.strftime("%I:%M %p")
            else:
                day_str  = datetime.datetime.fromisoformat(start_str).strftime("%A, %d %b")
                time_str = "All day"

            if day_str != current_day:
                lines.append(f"\n  {day_str}")
                current_day = day_str
            lines.append(f"    {time_str:<12} {e.get('summary','(no title)')}")
        return "\n".join(lines)

    except Exception as e:
        return f"Could not fetch weekly calendar: {e}"


def create_event(raw: str) -> str:
    try:
        svc             = _get_service()
        title, dt, dur  = _extract_event_info(raw)

        if not dt:
            return (
                "Could not parse the date/time. Try: "
                "\"add meeting tomorrow at 3pm\" or "
                "\"schedule call with John on Friday at 5pm\""
            )

        end_dt = dt + datetime.timedelta(minutes=dur)

        # Build attendees if "with <name>" mentioned
        attendees = []
        with_match = re.search(r"with\s+([\w\s]+?)(?:\s+at|\s+on|\s+for|$)", raw, re.IGNORECASE)
        if with_match:
            name = with_match.group(1).strip()
            # Check CONTACTS for email
            try:
                from config import CONTACTS
                email = CONTACTS.get(name.lower(), {})
                if isinstance(email, str) and "@" in email:
                    attendees.append({"email": email})
            except Exception:
                pass

        event_body = {
            "summary": title,
            "start":   {"dateTime": dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end":     {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "reminders": {
                "useDefault": False,
                "overrides":  [
                    {"method": "popup",  "minutes": 15},
                    {"method": "email",  "minutes": 30},
                ]
            }
        }
        if attendees:
            event_body["attendees"] = attendees

        created = svc.events().insert(
            calendarId="primary", body=event_body
        ).execute()

        link = created.get("htmlLink", "")
        return (
            f"Event created: '{title}'\n"
            f"  Date: {dt.strftime('%A, %d %b %Y')}\n"
            f"  Time: {dt.strftime('%I:%M %p')} — {end_dt.strftime('%I:%M %p')}\n"
            f"  Link: {link}"
        )

    except Exception as e:
        log(f"[Calendar] Create error: {e}", "ERROR")
        return f"Could not create event: {e}"

def find_free_slots(raw: str = "") -> str:
    try:
        svc  = _get_service()
        
        # Grab current time, but make it timezone-aware based on the system's local timezone
        now  = datetime.datetime.now().astimezone() 
        
        # Start and end of working day (8 AM to 10 PM), using the aware timezone info
        start_of_day = datetime.datetime(now.year, now.month, now.day, 8, 0, tzinfo=now.tzinfo)
        end_of_day   = datetime.datetime(now.year, now.month, now.day, 22, 0, tzinfo=now.tzinfo)

        # .isoformat() on an aware datetime automatically includes the correct offset 
        # (e.g., +05:30) instead of blindly appending "Z"
        result = svc.events().list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(), 
            timeMax=end_of_day.isoformat(),
            singleEvents=True, orderBy="startTime"
        ).execute()

        events    = result.get("items", [])
        busy_slots = []
        for e in events:
            s = e["start"].get("dateTime")
            en= e["end"].get("dateTime")
            if s and en:
                # Replace 'Z' with explicit +00:00 to ensure fromisoformat() always 
                # creates an aware datetime, preventing crashes on older Python versions.
                s = s.replace("Z", "+00:00")
                en = en.replace("Z", "+00:00")
                busy_slots.append((
                    datetime.datetime.fromisoformat(s),
                    datetime.datetime.fromisoformat(en)
                ))

        # Find gaps >= 30 minutes
        free = []
        cursor = start_of_day

        for bs, be in sorted(busy_slots):
            if cursor < bs:
                gap_mins = int((bs - cursor).total_seconds() / 60)
                if gap_mins >= 30:
                    free.append((cursor, bs, gap_mins))
            cursor = max(cursor, be)

        if cursor < end_of_day:
            gap_mins = int((end_of_day - cursor).total_seconds() / 60)
            if gap_mins >= 30:
                free.append((cursor, end_of_day, gap_mins))

        if not free:
            return "You're fully booked today — no free slots of 30+ minutes."

        lines = ["── Free slots today ──"]
        for s, e, mins in free:
            h = mins // 60; m = mins % 60
            dur_str = f"{h}h {m}m" if h else f"{m}m"
            lines.append(f"  {s.strftime('%I:%M %p')} — {e.strftime('%I:%M %p')}  ({dur_str} free)")
        return "\n".join(lines)

    except Exception as e:
        return f"Could not check free slots: {e}"
def delete_event(raw: str) -> str:
    try:
        svc  = _get_service()
        now  = datetime.datetime.utcnow()

        # Extract event name from command
        m = re.search(
            r"(?:delete|remove|cancel|clear)\s+(?:the\s+)?(.+?)(?:\s+meeting|\s+event|\s+appointment|$)",
            raw, re.IGNORECASE)
        query = m.group(1).strip() if m else raw

        result = svc.events().list(
            calendarId="primary",
            timeMin=now.isoformat() + "Z",
            q=query,
            maxResults=5,
            singleEvents=True
        ).execute()

        events = result.get("items", [])
        if not events:
            return f"No upcoming events found matching '{query}'."

        # Delete the first match
        e = events[0]
        svc.events().delete(calendarId="primary", eventId=e["id"]).execute()
        return f"Deleted event: '{e.get('summary', query)}'"

    except Exception as e:
        return f"Could not delete event: {e}"


def calendar_status() -> str:
    if not os.path.exists(CREDS_PATH):
        return (
            "Google Calendar: not configured.\n"
            "Download credentials.json from Google Cloud Console and place it in the project root."
        )
    if os.path.exists(TOKEN_PATH):
        return "Google Calendar: connected (token.json present)."
    return "Google Calendar: credentials found but not authenticated yet. Say 'my meetings today' to trigger login."