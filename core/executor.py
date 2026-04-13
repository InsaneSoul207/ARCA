import re
from core.logger import log
from core.multi_task_parser import split_commands, is_multi_task
from core.speaker import speak
from tasks import (system_tasks, browser_tasks, file_tasks,
                   communication_tasks, productivity_tasks, info_tasks,ai_mail)
from tasks.app_launcher import launch_app, KNOWN_APPS

def _try_import(path):
    try:
        import importlib
        return importlib.import_module(path), True
    except Exception as e:
        log(f"[Executor] Module unavailable: {path} — {e}", "WARN")
        speak(f"Some features may be unavailable: {path.split('.')[-1].replace('_', ' ')} module failed to load.")
        return None, False

_whatsapp,  _wa_ok   = _try_import("tasks.whatsapp")
_ai_email,  _em_ok   = _try_import("tasks.ai_mail")
_news,      _nw_ok   = _try_import("tasks.scraper_news")
_trends,    _tr_ok   = _try_import("tasks.scraper_trends")
_weather,   _wt_ok   = _try_import("tasks.scraper_weather")
_calendar,  _cal_ok  = _try_import("tasks.calendar_tasks")
_summarize, _sm_ok   = _try_import("tasks.search_summarize")
_fsearch,   _fs_ok   = _try_import("tasks.file_search")
_ocr,       _ocr_ok  = _try_import("tasks.ocr_tasks")
_proactive, _pro_ok  = _try_import("tasks.proactive")
_spotify,   _sp_ok   = _try_import("tasks.spotify_tasks")
_friday,    _fr_ok   = _try_import("tasks.friday_personality")

CONFIDENCE_THRESHOLD = 0.50



def _after(pattern, text, default=""):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else default

def extract_whatsapp_info(text: str):
    pattern = r"to\s+(.+?)\s+(?:says|say|saying that|saying|that|message|content|telling|asking)\s+(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None

def _extract_search_query(raw: str) -> str:
    patterns = [
        r"search\s+google\s+for\s+(.+)",
        r"search\s+the\s+web\s+for\s+(.+)",
        r"search\s+the\s+internet\s+for\s+(.+)",
        r"search\s+online\s+for\s+(.+)",
        r"do\s+a\s+(?:google|web)\s+search\s+for\s+(.+)",
        r"google\s+search\s+for\s+(.+)",
        r"google\s+search\s+(.+)",
        r"look\s+up\s+information\s+(?:about|on)\s+(.+)",
        r"look\s+up\s+(.+)",
        r"find\s+information\s+(?:about|on)\s+(.+)",
        r"find\s+details\s+(?:about|on)\s+(.+)",
        r"find\s+out\s+about\s+(.+)",
        r"search\s+for\s+(.+)",
        r"tell\s+me\s+about\s+(.+)",
        r"research\s+(.+)",
        r"google\s+(.+)",
    ]
    for p in patterns:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            q = m.group(1).strip()
            if q:
                return q
    return raw


def _extract_app_name(text: str) -> str:
    _T = r"(?:open|launch|start|run|load|bring up|pull up|fire up|get me|show me)\s+"
    stripped = re.sub(_T, "", text.strip().lower(), count=1)
    if stripped in KNOWN_APPS:
        return stripped
    best = ""
    for key in KNOWN_APPS:
        if key in text.lower() and len(key) > len(best):
            best = key
    return best or stripped


def _timer_secs(raw: str) -> int:
    m = re.search(r"(\d+)\s*(second|minute|hour)", raw, re.IGNORECASE)
    if m:
        val, unit = int(m.group(1)), m.group(2).lower()
        return val * (3600 if "hour" in unit else 60 if "minute" in unit else 1)
    return 60


def _na(name): return f"{name} module unavailable — check requirements.txt"



def _route(intent: str, raw: str) -> str:  # noqa: C901

    if intent == "open_app":
        app = _extract_app_name(raw)
        return launch_app(app) if app else "Which app? Try: 'open whatsapp'"

    if intent == "open_browser":      return system_tasks.open_browser()
    if intent == "open_calculator":   return system_tasks.open_calculator()
    if intent == "open_notepad":      return system_tasks.open_notepad()
    if intent == "open_task_manager": return system_tasks.open_task_manager()
    if intent == "take_screenshot":   return system_tasks.take_screenshot()
    if intent == "shutdown":          return system_tasks.shutdown()
    if intent == "restart":           return system_tasks.restart()
    if intent == "lock_screen":       return system_tasks.lock_screen()
    if intent == "sleep_pc":          return system_tasks.sleep_pc()
    if intent == "check_battery":     return system_tasks.check_battery()
    if intent == "check_cpu":         return system_tasks.check_cpu()
    if intent == "check_memory":      return system_tasks.check_memory()
    if intent == "check_disk":        return system_tasks.check_disk()
    if intent == "check_network":     return system_tasks.check_network()
    if intent == "volume_up":         return system_tasks.volume_up()
    if intent == "volume_down":       return system_tasks.volume_down()
    if intent == "mute":              return system_tasks.mute()

    if intent == "open_spotify":
        if not _sp_ok:
            return _na("Spotify PyAutoGUI")
        t = raw.lower()
        if any(w in t for w in ["pause", "stop music", "stop playing"]):
            return _spotify.play_pause()
        if any(w in t for w in ["next", "skip", "forward"]):
            return _spotify.next_track()
        if any(w in t for w in ["previous", "prev", "back", "last song"]):
            return _spotify.previous_track()
        if any(w in t for w in ["like", "heart", "save song"]):
            return _spotify.like_current_song()
        if "play" in t and len(t) > 10:
            query = re.sub(r"\bplay\b", "", t).strip()
            if query:
                return _spotify.search_and_play(query)
        return _spotify.open_spotify()

    if intent == "open_youtube":  return browser_tasks.open_youtube()
    if intent == "open_github":   return browser_tasks.open_github()

    if intent == "search_and_summarize":
        if not _sm_ok:
            return _na("Search+Summarize (beautifulsoup4)")
        return _summarize.search_and_summarize(raw)

    if intent == "open_file":
        return _fsearch.open_file(raw) if _fs_ok else _na("File search")
    if intent == "search_files":
        return _fsearch.search_files(raw) if _fs_ok else _na("File search")
    if intent == "find_recent_files":
        return _fsearch.find_recent_files() if _fs_ok else _na("File search")

    if intent == "set_reminder":
        text = _after(r"remind\s+me\s+(?:to|about|that)?\s*(.+)", raw) or raw
        return communication_tasks.set_reminder(text)

    if intent == "whatsapp_message":
        contact_name, message = extract_whatsapp_info(raw)
        if contact_name and message:
            return _whatsapp.send_whatsapp_message(contact_name, message) if _wa_ok else _na("WhatsApp (pywhatkit)")
        else:
            return "Could not parse WhatsApp command. Try: 'send whatsapp message to [contact] saying [message]'"

    if intent in ("send_email", "ai_draft_email"):
        return _ai_email.draft_and_send_email(raw) if _em_ok else _na("AI Email (Ollama)")

    if intent == "get_news":
        return _news.get_news_headlines(raw) if _nw_ok else _na("News scraper")

    if intent == "get_trends":
        return _trends.get_trending(raw) if _tr_ok else _na("Trends scraper")

    if intent == "check_weather":
        return _weather.get_current_weather(raw) if _wt_ok else _na("Weather scraper")
    if intent == "hourly_weather":
        return _weather.get_hourly_weather(raw) if _wt_ok else _na("Weather scraper")
    if intent == "weekly_weather":
        return _weather.get_weekly_weather(raw) if _wt_ok else _na("Weather scraper")
    if intent == "list_today_events":
        return _calendar.list_today_events() if _cal_ok else _na("Google Calendar")
    if intent == "list_week_events":
        return _calendar.list_week_events() if _cal_ok else _na("Google Calendar")
    if intent == "create_event":
        return _calendar.create_event(raw) if _cal_ok else _na("Google Calendar")
    if intent == "find_free_slots":
        return _calendar.find_free_slots(raw) if _cal_ok else _na("Google Calendar")
    if intent == "delete_event":
        return _calendar.delete_event(raw) if _cal_ok else _na("Google Calendar")
    if intent == "open_calendar":
        return productivity_tasks.open_calendar()

    if intent == "start_monitoring":
        return _proactive.start_monitoring() if _pro_ok else _na("Proactive monitor")
    if intent == "stop_monitoring":
        return _proactive.stop_monitoring() if _pro_ok else _na("Proactive monitor")
    if intent == "monitoring_status":
        return _proactive.monitoring_status() if _pro_ok else _na("Proactive monitor")

    if intent == "read_screen":
        return _ocr.read_screen() if _ocr_ok else _na("OCR (pytesseract)")
    if intent == "read_clipboard_image":
        return _ocr.read_clipboard_image() if _ocr_ok else _na("OCR (pytesseract)")

    if intent == "start_timer":   return productivity_tasks.start_timer(_timer_secs(raw))
    if intent == "stop_timer":    return productivity_tasks.stop_timer()
    if intent == "take_note":
        text = _after(r"(?:note|down|that|this|remember|jot)\s+(.+)", raw) or raw
        return productivity_tasks.take_note(text)
    if intent == "show_notes":    return productivity_tasks.show_notes()
    if intent == "clear_notes":   return productivity_tasks.clear_notes()

    if intent == "tell_time":  return info_tasks.tell_time()
    if intent == "tell_date":  return info_tasks.tell_date()
    if intent == "tell_joke":  return info_tasks.tell_joke()
    if intent == "tell_fact":  return info_tasks.tell_fact()
    if intent == "greet":      return info_tasks.greet()
    if intent == "goodbye":    return info_tasks.goodbye()
    if intent == "help":       return info_tasks.show_help()

    return f'Intent "{intent}" not mapped. Say "help" for commands.'



def execute(intent: str, raw: str, classifier=None) -> list[dict]:

    last_conf = getattr(execute, "_last_conf", 1.0)

    if last_conf < CONFIDENCE_THRESHOLD:
        from tasks.friday_personality import get_not_understood
        msg = get_not_understood(last_conf) if _fr_ok else \
              f"Not sure what you mean ({last_conf:.0%}). Try rephrasing."
        return [{"cmd": raw, "intent": "unknown", "conf": last_conf, "result": msg}]

    if classifier and is_multi_task(raw):
        results = []
        for cmd in split_commands(raw):
            si, sc = classifier.predict(cmd)
            results.append({"cmd": cmd, "intent": si, "conf": sc, "result": _route(si, cmd)})
            if results[-1]["result"] == "__SHUTDOWN__":
                break
        return results

    result = _route(intent, raw)
    return [{"cmd": raw, "intent": intent, "conf": last_conf, "result": result}]

