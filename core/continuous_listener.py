import threading, queue, time
import speech_recognition as sr
from core.logger import log
# Removed translate_process import
from config import (ENERGY_THRESHOLD, PAUSE_THRESHOLD,
                   PHRASE_TIME_LIMIT, DYNAMIC_ENERGY)

WAKE_WORDS  = {"alpha", "alfa"}
SLEEP_WORDS = {"goodbye", "good bye", "bye", "exit", "quit",
               "close alpha", "stop alpha", "deactivate", "sleep alpha"}


class ContinuousListener:

    def __init__(self):
        self._rec = sr.Recognizer()
        self._rec.energy_threshold         = ENERGY_THRESHOLD
        self._rec.dynamic_energy_threshold = DYNAMIC_ENERGY
        self._rec.pause_threshold          = PAUSE_THRESHOLD
        self._rec.phrase_threshold         = 0.3
        self._rec.non_speaking_duration    = 0.4

        self.event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._active  = False
        self._thread  = None

    def start(self):
        self._running = True
        self._active  = False
        self._thread  = threading.Thread(
            target=self._loop, daemon=True, name="ContinuousListener")
        self._thread.start()
        log("Listener started — waiting for wake word 'alpha'.")

    def stop(self):
        self._running = False
        log("Listener stopped.")

    @property
    def is_active(self):
        return self._active

    def _post(self, kind: str, data=None):
        self.event_queue.put((kind, data))

    def _loop(self):
        mic = sr.Microphone()
        with mic as src:
            self._rec.adjust_for_ambient_noise(src, duration=1.0)
            log(f"Mic calibrated (energy={self._rec.energy_threshold:.0f})")
            self._post("state", "idle")

            while self._running:
                try:
                    self._post("state", "active" if self._active else "idle")
                    audio = self._rec.listen(
                        src,
                        timeout=None,
                        phrase_time_limit=PHRASE_TIME_LIMIT,
                    )
                    self._post("state", "thinking")
                    threading.Thread(
                        target=self._recognise,
                        args=(audio,),
                        daemon=True,
                    ).start()

                except sr.WaitTimeoutError:
                    pass
                except OSError as e:
                    log(f"Mic error: {e}", "ERROR")
                    self._post("state", "error")
                    time.sleep(2.0)
                    try:
                        self._rec.adjust_for_ambient_noise(src, duration=0.5)
                    except Exception:
                        pass
                except Exception as e:
                    log(f"Listener error: {e}", "ERROR")
                    time.sleep(1.0)

    def _recognise(self, audio):
        text = ""
        # 1. Try English recognition
        try:
            text = self._rec.recognize_google(audio, language="en-IN").strip()
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            log(f"STT (en) error: {e}", "ERROR")
            self._post("state", "error")
            return

        # 2. If no English, try Hindi recognition
        if not text:
            try:
                text = self._rec.recognize_google(audio, language="hi-IN").strip()
                if text:
                    log(f'[Mic] Hindi STT: "{text}"')
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                log(f"STT (hi) error: {e}", "ERROR")

        if not text:
            return

        # Log what was heard without translation
        log(f'[Mic] Heard: "{text}"')

        # Standardize for logic checks (wake/sleep words)
        clean_text = text.lower().strip()
        if not clean_text:
            return

        # 3. Handle Wake Words
        if not self._active:
            if any(w in clean_text for w in WAKE_WORDS):
                self._active = True
                log("[Listener] Wake word → ACTIVE")
                self._post("wake", None)
            return

        # 4. Handle Sleep Words
        if any(w in clean_text for w in SLEEP_WORDS):
            self._active = False
            log("[Listener] Sleep word → IDLE")
            self._post("sleep", None)
            return

        # 5. Post the raw phrase
        self._post("phrase", clean_text)