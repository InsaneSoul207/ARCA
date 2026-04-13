import time, threading, datetime
from core.logger import log


_notes = []
_timer_thread = None
_timer_running = False
_timer_callback = None   # set by UI to display elapsed time


def start_timer(seconds=60, callback=None):
    global _timer_thread, _timer_running, _timer_callback
    _timer_running = True
    _timer_callback = callback

    def _run():
        global _timer_running
        start = time.time()
        while _timer_running:
            elapsed = time.time() - start
            if elapsed >= seconds:
                _timer_running = False
                log(f"Timer done: {seconds}s elapsed")
                if _timer_callback:
                    _timer_callback(f"TIMER DONE! ({seconds}s)")
                return
            time.sleep(0.5)

    _timer_thread = threading.Thread(target=_run, daemon=True)
    _timer_thread.start()
    return f"Timer started for {seconds} seconds."

def stop_timer():
    global _timer_running
    _timer_running = False
    return "Timer stopped."

def take_note(text=""):
    if not text:
        text = "Empty note"
    ts = datetime.datetime.now().strftime("%H:%M")
    _notes.append(f"[{ts}] {text}")
    return f"Note saved: '{text}'"

def show_notes():
    if not _notes:
        return "No notes yet."
    return "Notes:\n" + "\n".join(f"  {n}" for n in _notes)

def clear_notes():
    _notes.clear()
    return "All notes cleared."

def open_calendar():
    import webbrowser
    webbrowser.open("https://calendar.google.com")
    return "Opened Google Calendar."