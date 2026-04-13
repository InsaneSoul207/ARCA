import threading, re, time
import pyttsx3
from core.logger import log

_engine      = None
_engine_lock = threading.Lock()
_speak_lock  = threading.Lock()

_RATE    = 160  
_VOLUME  = 0.8 
_VOICE   = "hazel"
_LONG_RESULT_INTENTS = {
    "get_news", "search_and_summarize", "get_trends",
    "hourly_weather", "weekly_weather", "list_week_events",
    "search_files", "find_recent_files", "show_notes",
}

_MAX_CHARS = {
    "default":              350,
    "get_news":             150,
    "search_and_summarize": 300,
    "get_trends":           150,
    "hourly_weather":       200,
    "weekly_weather":       200,
    "list_week_events":     200,
    "list_today_events":    300,
    "check_weather":        200,
}


def _get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = pyttsx3.init(driverName="sapi5")
            _engine.setProperty("rate",   _RATE)
            _engine.setProperty("volume", _VOLUME)
            _set_voice_internal(_engine, _VOICE)
            log(f"[TTS] Engine initialised (rate={_RATE})")
        return _engine


def _set_voice_internal(engine, preference):
    if preference is None:
        return
    voices = engine.getProperty("voices")
    pref   = preference.lower()
    for v in voices:
        if pref in v.name.lower() or pref in v.id.lower():
            engine.setProperty("voice", v.id)
            log(f"[TTS] Voice: {v.name}")
            return


def _clean_for_speech(text: str) -> str:
    text = re.sub(r'https?://\S+', '', text)  
    text = re.sub(r'[─═─┼│┤├┬┴╔╗╚╝║╠╣╦╩]', '', text) 
    text = re.sub(r'[●•·▸▶►◉✓✗⚡⏰📅🔋💾⚠]', '', text) 
    text = re.sub(r'\*{1,3}', '', text)               
    text = re.sub(r'#{1,6}\s', '', text)              
    text = re.sub(r'\[(\d+)\]', '', text)             
    text = re.sub(r'──+.*?──+', '', text)             
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def _truncate(text: str, intent: str = "default") -> str:
    """Truncate for speech — long intents get a shorter limit."""
    limit = _MAX_CHARS.get(intent, _MAX_CHARS["default"])
    if len(text) <= limit:
        return text
    # Cut at sentence boundary
    cut      = text[:limit]
    last_dot = cut.rfind(".")
    if last_dot > limit // 2:
        return cut[:last_dot + 1] + " And more."
    return cut + "… and more."


def _speak_worker(text: str):
    with _speak_lock:
        try:
            engine = _get_engine()
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            global _engine
            with _engine_lock:
                _engine = None
            try:
                engine = _get_engine()
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                log(f"[TTS] Retry failed: {e}", "ERROR")
        except Exception as e:
            log(f"[TTS] Speech error: {e}", "ERROR")


def speak(text: str, intent: str = "default"):
    if not text or not text.strip():
        return
    if text == "__SHUTDOWN__":
        return

    clean = _clean_for_speech(text)
    if not clean:
        return

    spoken = _truncate(clean, intent)
    log(f'[TTS] "{spoken[:60]}{"…" if len(spoken) > 60 else ""}"')
    
    # REMOVED: threading.Thread(target=_speak_worker, args=(spoken,), daemon=True).start()
    # ADDED: Direct call to worker
    _speak_worker(spoken)


def speak_immediate(text: str):
    clean = _clean_for_speech(text)
    if clean:
        threading.Thread(target=_speak_worker, args=(clean,), daemon=True).start()


def stop_speaking():
    try:
        _get_engine().stop()
    except Exception:
        pass


def set_rate(wpm: int):
    global _RATE
    _RATE = wpm
    try:
        _get_engine().setProperty("rate", wpm)
    except Exception:
        pass


def set_volume(vol: float):
    global _VOLUME
    _VOLUME = max(0.0, min(1.0, vol))
    try:
        _get_engine().setProperty("volume", _VOLUME)
    except Exception:
        pass


def set_voice(preference: str):
    global _VOICE
    _VOICE = preference
    try:
        _set_voice_internal(_get_engine(), preference)
    except Exception:
        pass


def list_voices() -> str:
    try:
        voices = _get_engine().getProperty("voices")
        lines  = ["Available TTS voices:"]
        for i, v in enumerate(voices):
            lines.append(f"  [{i}] {v.name}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not list voices: {e}"
    
if __name__ == "__main__":
    speak("Hello! This is a test of the text-to-speech system. It should speak this message aloud.")
    time.sleep(5)