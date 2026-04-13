from core.logger import log

_langdetect_ok   = False
_translator_ok   = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    _langdetect_ok = True
except ImportError:
    log("[Translator] langdetect not installed — language detection disabled", "WARN")

try:
    from deep_translator import GoogleTranslator
    _translator_ok = True
except ImportError:
    log("[Translator] deep-translator not installed — translation disabled", "WARN")


_TRANSLATE_FROM = {"hi", "mr", "gu", "bn", "ta", "te", "kn", "pa"}
def detect_language(text: str) -> str:
    if not _langdetect_ok or not text.strip():
        return "en"
    try:
        lang = detect(text)
        return lang
    except Exception as e:
        log(f"[Translator] Detection failed: {e}", "WARN")
        return "en"


def translate_to_english(text: str, source_lang: str = "auto") -> str:
    if not _translator_ok:
        return text
    try:
        translated = GoogleTranslator(
            source=source_lang, target="en"
        ).translate(text)
        return translated.strip() if translated else text
    except Exception as e:
        log(f"[Translator] Translation failed: {e}", "WARN")
        return text


def process(text: str) -> tuple[str, str]:
    if not text or not text.strip():
        return text, "en"

    lang = detect_language(text)
    log(f"[Translator] Detected language: {lang}")

    if lang not in _TRANSLATE_FROM:
        return text, lang

    log(f"[Translator] Translating from '{lang}': {text[:60]}")
    translated = translate_to_english(text, source_lang=lang)
    log(f"[Translator] → '{translated[:60]}'")

    return translated, lang


def is_available() -> bool:
    return _langdetect_ok and _translator_ok


def status() -> str:
    if _langdetect_ok and _translator_ok:
        return "Translation: active (Hindi + 7 Indian languages supported)"
    missing = []
    if not _langdetect_ok:
        missing.append("langdetect")
    if not _translator_ok:
        missing.append("deep-translator")
    return f"Translation: disabled — install: pip install {' '.join(missing)}"
