import threading
import time
import math
import queue
from core.logger import log

# ── Detection parameters (tune these if needed) ───────────────────────────────
CLAP_THRESHOLD     = 2400  # RMS amplitude threshold — claps are sharp & loud
DOUBLE_CLAP_WINDOW = 1.5    # seconds — max gap between clap 1 and clap 2
COOLDOWN           = 2.0    # seconds to suppress further detections after wake
CHUNK_SIZE         = 1024   # audio frames per read (~23ms at 44100Hz)
SAMPLE_RATE        = 44100
FORMAT_WIDTH       = 2      # 16-bit = 2 bytes per sample

# Minimum silence between two claps (avoid counting one long clap as two)
MIN_CLAP_GAP       = 0.15   # seconds


class ClapDetector:

    def __init__(self, on_double_clap_cb=None):
        self._cb       = on_double_clap_cb
        self._running  = False
        self._thread   = None

        # Clap timing state
        self._last_clap_time  = 0.0
        self._clap_count      = 0
        self._last_detect_time= 0.0   # for cooldown

        # Thread-safe event queue → UI
        self.event_queue: queue.Queue = queue.Queue()

    # ── Public API ─────────────────────────────────────────────────────────────
    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._loop, daemon=True, name="ClapDetector")
        self._thread.start()
        log("[Clap] Detector started — waiting for double-clap.")

    def stop(self):
        self._running = False
        log("[Clap] Detector stopped.")

    # ── Internal ───────────────────────────────────────────────────────────────
    def _post(self, kind, data=None):
        self.event_queue.put((kind, data))

    def _rms(self, data: bytes) -> float:
        import struct
        n      = len(data) // FORMAT_WIDTH
        if n == 0:
            return 0.0
        shorts = struct.unpack(f"<{n}h", data)
        mean_sq = sum(s * s for s in shorts) / n
        return math.sqrt(mean_sq)

    def _loop(self):
        try:
            import pyaudio
        except ImportError:
            log("[Clap] pyaudio not installed — clap detection unavailable.", "WARN")
            return

        pa     = pyaudio.PyAudio()
        stream = None

        try:
            stream = pa.open(
                format            = pyaudio.paInt16,
                channels          = 1,
                rate              = SAMPLE_RATE,
                input             = True,
                frames_per_buffer = CHUNK_SIZE,
            )
            log(f"[Clap] Audio stream open (threshold={CLAP_THRESHOLD})")

            in_clap     = False   # True while energy is above threshold
            clap_start  = 0.0

            while self._running:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.05)
                    continue

                energy = self._rms(data)
                now    = time.time()

                # ── Detect rising edge (start of a clap) ─────────────────────
                if not in_clap and energy > CLAP_THRESHOLD:
                    in_clap    = True
                    clap_start = now

                # ── Detect falling edge (end of a clap) ──────────────────────
                elif in_clap and energy < CLAP_THRESHOLD * 0.4:
                    in_clap        = False
                    clap_duration  = now - clap_start

                    # A real clap is short (< 0.3s); sustained noise is longer
                    if clap_duration > 0.3:
                        continue   # not a clap — sustained noise

                    # Enforce minimum gap between claps
                    gap_since_last = now - self._last_clap_time
                    if gap_since_last < MIN_CLAP_GAP:
                        continue

                    self._last_clap_time = now
                    self._clap_count    += 1
                    log(f"[Clap] Clap #{self._clap_count} detected "
                        f"(energy={energy:.0f}, dur={clap_duration*1000:.0f}ms)")

                    # First clap — start window
                    if self._clap_count == 1:
                        pass   # wait for second

                    # Second clap — check if within window
                    elif self._clap_count >= 2:
                        total_gap = now - (self._last_clap_time
                                           - gap_since_last)  # time from clap1
                        # Use simpler check: gap between last two claps
                        if gap_since_last <= DOUBLE_CLAP_WINDOW:
                            # Check cooldown
                            if now - self._last_detect_time > COOLDOWN:
                                self._last_detect_time = now
                                self._clap_count       = 0
                                log("[Clap] ✓ Double-clap detected → waking Alpha")
                                self._post("double_clap", None)
                                if self._cb:
                                    self._cb()
                            else:
                                self._clap_count = 0
                        else:
                            # Too slow — reset, count this as first clap
                            self._clap_count = 1

                # Reset clap count if too much time since last clap
                if (self._clap_count > 0
                        and time.time() - self._last_clap_time > DOUBLE_CLAP_WINDOW):
                    self._clap_count = 0

        except Exception as e:
            log(f"[Clap] Stream error: {e}", "ERROR")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            try:
                pa.terminate()
            except Exception:
                pass
            log("[Clap] Audio stream closed.")

