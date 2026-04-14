import tkinter as tk
import threading, math, datetime, queue as _queue
import tasks.productivity_tasks as pt

from config import *
from core.logger              import log
from core.continuous_listener import ContinuousListener
from core.classifier          import IntentClassifier
from core.executor            import execute
from core.multi_task_parser   import is_multi_task
from core.speaker             import speak, stop_speaking, set_rate, set_volume



class WaveBar(tk.Canvas):

    def __init__(self, master, w=820, h=48, **kw):
        super().__init__(master, width=w, height=h, highlightthickness=0, **kw)
        self._cw     = w     
        self._ch     = h
        self._active = False
        self._t      = 0.0
        self.after_idle(self._tick)

    def set_active(self, v: bool):
        self._active = v

    def _tick(self):
        try:
            self.delete("all")
        except tk.TclError:
            return
        n, cy = 56, self._ch // 2
        self.create_line(0, cy, self._cw, cy, fill=BORDER, width=1)
        for i in range(n):
            x = i * self._cw / n + self._cw / n / 2
            if self._active:
                amp   = 16 * math.sin(self._t + i * 0.33) * math.sin(self._t * 0.6 + i * 0.11)
                frac  = i / n
                g     = int(98 + frac * 103)
                color = f"#00{g:02x}ff"
                width = 2
            else:
                amp   = 1.5 * math.sin(self._t * 0.3 + i * 0.18)
                color = BORDER
                width = 1
            self.create_line(x, cy - amp, x, cy + amp,
                             fill=color, width=width, capstyle=tk.ROUND)
        self._t += 0.09
        self.after(33, self._tick)


class GlowBtn(tk.Canvas):

    def __init__(self, master, text, cmd, w=120, h=34, **kw):
        super().__init__(master, width=w, height=h, highlightthickness=0, **kw)
        self._text  = text
        self._cmd   = cmd
        self._cw    = w     # use _cw/_ch — self._w is reserved by Tkinter internally
        self._ch    = h
        self._hov   = False
        self._press = False
        self.after_idle(self._draw)
        self.bind("<Enter>",           lambda e: self._s(hov=True))
        self.bind("<Leave>",           lambda e: self._s(hov=False, press=False))
        self.bind("<ButtonPress-1>",   lambda e: self._s(press=True))
        self.bind("<ButtonRelease-1>", self._rel)

    def _s(self, **kw):
        for k, v in kw.items():
            setattr(self, f"_{k}", v)
        self._draw()

    def _draw(self):
        try:
            self.delete("all")
        except tk.TclError:
            return
        w, h, r = self._cw, self._ch, 4
        fill = ACCENT       if self._press else "#E8F0FE" if self._hov else BG_GLASS
        tfg  = "#ffffff"    if self._press else ACCENT    if self._hov else TEXT_MID
        bc   = ACCENT       if (self._hov or self._press) else BORDER
        bw   = 2            if (self._hov or self._press) else 1
        for x0, y0, x1, y1 in [(r, 0, w-r, h), (0, r, w, h-r)]:
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")
        for x0, y0, x1, y1 in [(0, 0, r*2, r*2), (w-r*2, 0, w, r*2),
                                 (0, h-r*2, r*2, h), (w-r*2, h-r*2, w, h)]:
            self.create_oval(x0, y0, x1, y1, fill=fill, outline="")
        self.create_rectangle(bw//2, bw//2, w-bw//2, h-bw//2, outline=bc, width=bw)
        self.create_text(w // 2, h // 2, text=self._text,
                         font=FONT_HEAD, fill=tfg, anchor="center")

    def _rel(self, e):
        self._press = False
        self._draw()
        if self._cmd:
            self._cmd()

    def update_text(self, t: str):
        self._text = t
        self._draw()


# ─────────────────────────────────────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────────────────────────────────────

class Alpha2App:

    FULL_W,    FULL_H    = 1100, 800
    COMPACT_W, COMPACT_H = 360, 170

    def __init__(self, root: tk.Tk):
        self.root         = root
        self._alive       = True
        self._compact     = False
        self._muted       = False
        self._session_on  = False   # True when listener is ACTIVE (post wake word)

        self.classifier         = None
        self._classifier_ready  = False
        self._listener          = ContinuousListener()

        self._timer_q   = []   # timer completion messages (written by bg thread)
        self._retrain_q = []   # retrain log lines

        # Timer callback — bg thread writes to list, main thread reads
        def _timer_cb(m):
            self._timer_q.append(m)
        pt.timer_done_cb = _timer_cb

        self._setup_window()
        self._build_full()
        self._build_compact()
        self._show_full()

        # Start all main-thread pollers
        self._poll_classifier()
        self._poll_listener()
        self._poll_timer()
        self._tick_clock()
        self._animate_pulse()

        # Start loading classifier in background
        self._set_state("LOADING MODEL…", "thinking")
        self._log("[System] Loading LSTM classifier…", ACCENT)
        threading.Thread(target=self._load_classifier, daemon=True).start()

        # Keyboard shortcut
        self.root.bind("<Control-m>", lambda e: self._toggle_compact())
        self.root.bind("<Control-M>", lambda e: self._toggle_compact())

    # ── Window setup ──────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("ARCA")
        self.root.configure(bg=BG_BASE)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─────────────────────────────────────────────────────────────────────────
    # FULL MODE
    # ─────────────────────────────────────────────────────────────────────────
    def _build_full(self):
        self._full = tk.Frame(self.root, bg=BG_BASE)

        # Top bar
        top = tk.Frame(self._full, bg=BG_DEEP, height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="ALPHA", font=("Consolas", 20, "bold"),
                 fg=ACCENT, bg=BG_DEEP).pack(side="left", padx=(18, 0), pady=8)
        tk.Label(top, text=" 2.0", font=("Consolas", 20, "bold"),
                 fg=ACCENT3, bg=BG_DEEP).pack(side="left", pady=8)

        right = tk.Frame(top, bg=BG_DEEP)
        right.pack(side="right", padx=14)

        self._clock_full = tk.Label(right, font=FONT_SMALL, fg=TEXT_DIM, bg=BG_DEEP)
        self._clock_full.pack(side="right", padx=(8, 0))

        pill = tk.Frame(right, bg=BG_PANEL, padx=7, pady=2)
        pill.pack(side="right")
        self._pulse_cv_full = tk.Canvas(pill, width=14, height=14,
                                        bg=BG_PANEL, highlightthickness=0)
        self._pulse_cv_full.pack(side="left", padx=(0, 4))
        self._status_lbl_full = tk.Label(pill, text="INIT",
                                         font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL)
        self._status_lbl_full.pack(side="left")

        # Accent line
        tk.Frame(self._full, bg=ACCENT, height=2).pack(fill="x")

        # Session banner (shown when IDLE)
        self._banner_full = tk.Frame(self._full, bg="#FFF8E7", pady=6)
        self._banner_lbl_full = tk.Label(
            self._banner_full,
            text='🎙  Say  "ALPHA"  to activate — then speak your commands freely',
            font=("Consolas", 9), fg="#7A5800", bg="#FFF8E7")
        self._banner_lbl_full.pack()

        # Waveform
        wf = tk.Frame(self._full, bg=BG_BASE, pady=6)
        wf.pack(fill="x", padx=36)
        self._wave_full = WaveBar(wf, w=826, h=48, bg=BG_PANEL)
        self._wave_full.pack()

        # Heard / Intent row
        row = tk.Frame(self._full, bg=BG_BASE)
        row.pack(fill="x", padx=36, pady=(4, 0))

        hc = tk.Frame(row, bg=BG_PANEL, padx=12, pady=8)
        hc.pack(side="left", fill="both", expand=True, padx=(0, 5))
        tk.Label(hc, text="VOICE INPUT", font=FONT_MICRO,
                 fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        self._heard_lbl = tk.Label(hc, text="Waiting for wake word…",
                                   font=("Consolas", 10, "italic"), fg=TEXT_GHOST,
                                   bg=BG_PANEL, wraplength=380, justify="left")
        self._heard_lbl.pack(anchor="w")
        self._multi_badge = tk.Label(hc, text="", font=FONT_MICRO,
                                     fg=ACCENT3, bg=BG_PANEL)
        self._multi_badge.pack(anchor="w")

        ic = tk.Frame(row, bg=BG_PANEL, padx=12, pady=8)
        ic.pack(side="left", fill="y", padx=(5, 0))
        tk.Label(ic, text="INTENT", font=FONT_MICRO, fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        self._intent_lbl = tk.Label(ic, text="—", font=("Consolas", 12, "bold"),
                                    fg=ACCENT, bg=BG_PANEL)
        self._intent_lbl.pack(anchor="w")
        self._conf_lbl = tk.Label(ic, text="conf —", font=FONT_MICRO,
                                  fg=TEXT_DIM, bg=BG_PANEL)
        self._conf_lbl.pack(anchor="w")
        self._cbar_cv = tk.Canvas(ic, width=185, height=4,
                                  bg=BG_PANEL, highlightthickness=0)
        self._cbar_cv.pack(anchor="w", pady=(3, 0))

        # Result banner
        rw = tk.Frame(self._full, bg=BG_BASE)
        rw.pack(fill="x", padx=36, pady=(6, 0))
        rc = tk.Frame(rw, bg=BG_PANEL, padx=12, pady=8)
        rc.pack(fill="x")
        hr = tk.Frame(rc, bg=BG_PANEL)
        hr.pack(fill="x")
        tk.Label(hr, text="RESULT", font=FONT_MICRO, fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")
        self._res_tag_full = tk.Label(hr, text="", font=FONT_MICRO, fg=GREEN, bg=BG_PANEL)
        self._res_tag_full.pack(side="right")
        self._res_lbl_full = tk.Label(rc, text="",
                                      font=("Consolas", 10), fg=TEXT_DARK, bg=BG_PANEL,
                                      wraplength=840, justify="left", anchor="w")
        self._res_lbl_full.pack(fill="x")

        # Divider + Log
        tk.Frame(self._full, bg=BORDER, height=1).pack(fill="x", padx=36, pady=(6, 0))
        lw = tk.Frame(self._full, bg=BG_BASE)
        lw.pack(fill="both", expand=True, padx=36, pady=(4, 0))
        tk.Label(lw, text="LOG", font=FONT_MICRO, fg=TEXT_DIM, bg=BG_BASE).pack(anchor="w")
        li = tk.Frame(lw, bg=BG_DEEP)
        li.pack(fill="both", expand=True)
        self._log_box = tk.Text(li, bg=BG_DEEP, fg=TEXT_MID, font=("Consolas", 8),
                                bd=0, state="disabled", wrap="word", padx=8, pady=4)
        sb = tk.Scrollbar(li, command=self._log_box.yview, bg=BG_DEEP,
                          troughcolor=BG_DEEP, activebackground=ACCENT, width=7, bd=0)
        self._log_box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_box.pack(fill="both", expand=True)

        # Button row
        br = tk.Frame(self._full, bg=BG_DEEP, height=54)
        br.pack(fill="x", pady=(5, 0))
        br.pack_propagate(False)
        inn = tk.Frame(br, bg=BG_DEEP)
        inn.place(relx=.5, rely=.5, anchor="center")

        self._mute_btn_full = GlowBtn(inn, "⊘  MUTE", self._toggle_mute,
                                      w=110, h=34, bg=BG_BASE)
        self._mute_btn_full.pack(side="left", padx=5)
        GlowBtn(inn, "COMPACT", self._toggle_compact, w=100, h=34, bg=BG_BASE).pack(side="left", padx=5)
        GlowBtn(inn, "HELP",    self._show_help,       w=80,  h=34, bg=BG_BASE).pack(side="left", padx=5)
        GlowBtn(inn, "CLR LOG", self._clear_log,       w=90,  h=34, bg=BG_BASE).pack(side="left", padx=5)
        GlowBtn(inn, "RETRAIN",    self._retrain,         w=90,  h=34, bg=BG_BASE).pack(side="left", padx=5)
        GlowBtn(inn, "⏹ STOP VOICE", stop_speaking, w=200, h=34, bg=BG_BASE).pack(side="left", padx=5)

        tk.Label(br, text='Ctrl+M → compact',
                 font=("Consolas", 7), fg=TEXT_GHOST, bg=BG_DEEP).place(relx=0.98, rely=0.5, anchor="e")

    # ─────────────────────────────────────────────────────────────────────────
    # COMPACT MODE
    # ─────────────────────────────────────────────────────────────────────────
    def _build_compact(self):
        self._cwin = tk.Toplevel(self.root)
        self._cwin.withdraw()
        self._cwin.title("ARCA")
        self._cwin.geometry(f"{self.COMPACT_W}x{self.COMPACT_H}")
        self._cwin.resizable(False, False)
        self._cwin.configure(bg=BG_DEEP)
        self._cwin.attributes("-topmost", True)
        self._cwin.overrideredirect(True)

        self._drag_x = self._drag_y = 0
        self._cwin.bind("<ButtonPress-1>",  self._drag_start)
        self._cwin.bind("<B1-Motion>",       self._drag_move)

        outer = tk.Frame(self._cwin, bg=ACCENT, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=BG_DEEP)
        inner.pack(fill="both", expand=True)

        # Top strip
        top = tk.Frame(inner, bg=BG_DEEP, height=30)
        top.pack(fill="x", padx=8, pady=(5, 0))
        top.pack_propagate(False)

        tk.Label(top, text="ARCA", font=("Consolas", 10, "bold"),
                 fg=ACCENT, bg=BG_DEEP).pack(side="left")
        self._pulse_cv_compact = tk.Canvas(top, width=12, height=12,
                                           bg=BG_DEEP, highlightthickness=0)
        self._pulse_cv_compact.pack(side="left", padx=(6, 2))
        self._status_lbl_compact = tk.Label(top, text="INIT",
                                            font=("Consolas", 7), fg=TEXT_DIM, bg=BG_DEEP)
        self._status_lbl_compact.pack(side="left")
        self._clock_compact = tk.Label(top, font=("Consolas", 7), fg=TEXT_DIM, bg=BG_DEEP)
        self._clock_compact.pack(side="right")

        # Mini waveform
        self._wave_compact = WaveBar(inner, w=342, h=26, bg=BG_DEEP)
        self._wave_compact.pack(padx=8, pady=(2, 0))

        # Session banner (compact)
        self._banner_compact = tk.Frame(inner, bg="#FFF8E7")
        self._banner_lbl_compact = tk.Label(
            self._banner_compact,
            text='Say "ALPHA" to activate',
            font=("Consolas", 7), fg="#7A5800", bg="#FFF8E7")
        self._banner_lbl_compact.pack(padx=6, pady=2)

        # Heard
        hr = tk.Frame(inner, bg=BG_DEEP)
        hr.pack(fill="x", padx=8, pady=(3, 0))
        tk.Label(hr, text="▸", font=("Consolas", 8), fg=ACCENT2, bg=BG_DEEP).pack(side="left")
        self._heard_compact = tk.Label(hr, text="waiting…",
                                       font=("Consolas", 8, "italic"), fg=TEXT_DIM,
                                       bg=BG_DEEP, anchor="w")
        self._heard_compact.pack(side="left", fill="x", expand=True)

        # Result
        rr = tk.Frame(inner, bg=BG_DEEP)
        rr.pack(fill="x", padx=8, pady=(2, 0))
        tk.Label(rr, text="✓", font=("Consolas", 8), fg=GREEN, bg=BG_DEEP).pack(side="left")
        self._res_compact = tk.Label(rr, text="", font=("Consolas", 8), fg=TEXT_DARK,
                                     bg=BG_DEEP, anchor="w", wraplength=300)
        self._res_compact.pack(side="left", fill="x", expand=True)

        # Buttons
        btn_row = tk.Frame(inner, bg=BG_DEEP)
        btn_row.pack(fill="x", padx=8, pady=(5, 6))
        self._mute_btn_compact = GlowBtn(btn_row, "⊘ MUTE", self._toggle_mute,
                                         w=90, h=24, bg=BG_DEEP)
        self._mute_btn_compact.pack(side="left", padx=(0, 4))
        GlowBtn(btn_row, "⊞ EXPAND", self._toggle_compact,
                w=100, h=24, bg=BG_DEEP).pack(side="left", padx=(0, 4))
        GlowBtn(btn_row, "✕ CLOSE", self._on_close,
                w=100, h=24, bg=BG_DEEP).pack(side="left")

    # ── Mode switching ────────────────────────────────────────────────────────
    def _show_full(self):
        self._cwin.withdraw()
        self.root.deiconify()
        self.root.geometry(f"{self.FULL_W}x{self.FULL_H}")
        self._full.pack(fill="both", expand=True)
        self._compact = False

    def _show_compact(self):
        self._full.pack_forget()
        self.root.withdraw()
        sw = self.root.winfo_screenwidth()
        x  = sw - self.COMPACT_W - 20
        self._cwin.geometry(f"{self.COMPACT_W}x{self.COMPACT_H}+{x}+40")
        self._cwin.deiconify()
        self._cwin.lift()
        self._compact = True

    def _toggle_compact(self):
        if self._compact:
            self._show_full()
        else:
            self._show_compact()

    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag_move(self, e):
        x = self._cwin.winfo_x() + (e.x - self._drag_x)
        y = self._cwin.winfo_y() + (e.y - self._drag_y)
        self._cwin.geometry(f"+{x}+{y}")

    def _animate_pulse(self):
        if not self._alive:
            return
        COLORS = {
            "idle":      TEXT_GHOST,
            "active":    ACCENT2,
            "listening": ACCENT2,
            "thinking":  YELLOW,
            "ready":     GREEN,
            "error":     RED,
            "muted":     RED,
        }
        color = COLORS.get(getattr(self, "_pulse_state", "idle"), TEXT_GHOST)
        pulse = 0.5 + 0.5 * math.sin(getattr(self, "_pulse_t", 0.0) * 3)

        for cv in [self._pulse_cv_full, self._pulse_cv_compact]:
            try:
                sz  = int(cv["width"])
                cx  = sz // 2
                r   = sz // 2 - 2
                cv.delete("all")
                if getattr(self, "_pulse_state", "idle") in ("active", "listening", "thinking"):
                    o = int(r + 2 * pulse)
                    cv.create_oval(cx-o, cx-o, cx+o, cx+o, fill="", outline=color, width=1)
                cv.create_oval(cx-r, cx-r, cx+r, cx+r, fill=color, outline="")
            except tk.TclError:
                pass

        self._pulse_t = getattr(self, "_pulse_t", 0.0) + 0.08
        self.root.after(40, self._animate_pulse)

    def _set_state(self, text: str, state: str):
        self._pulse_state = state
        self._status_lbl_full.config(text=text)
        try:
            self._status_lbl_compact.config(text=text)
        except Exception:
            pass

    def _show_banner(self, visible: bool):
        if visible:
            self._banner_full.pack(fill="x")
            try:
                self._banner_compact.pack(fill="x", padx=8)
            except Exception:
                pass
        else:
            self._banner_full.pack_forget()
            try:
                self._banner_compact.pack_forget()
            except Exception:
                pass

    def _tick_clock(self):
        if not self._alive:
            return
        t = datetime.datetime.now().strftime("%H:%M:%S   %a %d %b")
        self._clock_full.config(text=t)
        try:
            self._clock_compact.config(text=datetime.datetime.now().strftime("%H:%M"))
        except Exception:
            pass
        self.root.after(1000, self._tick_clock)

    def _log(self, msg: str, color: str = ""):
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        self._log_box.config(state="normal")
        if color:
            tag = "c" + color.replace("#", "")
            self._log_box.tag_configure(tag, foreground=color)
            self._log_box.insert("end", line, tag)
        else:
            self._log_box.insert("end", line)
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")

    def _show_results(self, results: list):
        if not results:
            return
        if len(results) == 1:
            display  = results[0]["result"]
            tag_txt  = "✓ DONE"
            tag_col  = GREEN
        else:
            display  = "\n".join(f"[{i+1}] {r['intent']}: {r['result']}"
                                 for i, r in enumerate(results))
            tag_txt  = f"✓ {len(results)} TASKS DONE"
            tag_col  = ACCENT2

        self._res_lbl_full.config(text=display, fg=TEXT_DARK)
        self._res_tag_full.config(text=tag_txt, fg=tag_col)

        compact_txt = results[-1]["result"]
        if len(compact_txt) > 55:
            compact_txt = compact_txt[:52] + "…"
        try:
            self._res_compact.config(text=compact_txt, fg=TEXT_DARK)
        except Exception:
            pass

    def _update_cbar(self, conf: float):
        self._cbar_cv.delete("all")
        self._cbar_cv.create_rectangle(0, 0, 185, 4, fill=BG_DEEP, outline="")
        if conf > 0:
            c = GREEN if conf >= 0.75 else YELLOW if conf >= 0.5 else RED
            self._cbar_cv.create_rectangle(0, 0, int(185 * conf), 4, fill=c, outline="")

    def _load_classifier(self):
        self.classifier        = IntentClassifier()
        self._classifier_ready = True

    def _poll_classifier(self):
        if getattr(self, "_classifier_ready", False) and self.classifier is not None:
            self._on_classifier_ready()
            return
        self.root.after(100, self._poll_classifier)

    def _on_classifier_ready(self):
        n = len(self.classifier.le.classes_)
        self._set_state("IDLE", "idle")
        self._show_banner(True)
        self._log(f"[System] ARCA online — {n} intents loaded.", GREEN)
        self._log('[System] Say  "ALPHA"  to activate the session.', ACCENT2)
        from core.translator import status as translator_status
        self._log(f"[System] {translator_status()}", TEXT_DIM)
        speak("ARCA online. Say Alpha to activate.")
        self._wave_full.set_active(False)
        self._wave_compact.set_active(False)
        self._listener.start()

    def _poll_listener(self):
        if not self._alive:
            return
        try:
            while True:
                kind, data = self._listener.event_queue.get_nowait()
                if kind == "state":
                    self._handle_mic_state(data)
                elif kind == "wake":
                    self._on_wake()
                elif kind == "phrase":
                    self._on_phrase(data)
                elif kind == "sleep":
                    self._on_sleep()
                elif kind == "translated":
                    self._on_translated(data)
        except Exception:
            pass   
        self.root.after(50, self._poll_listener)

    def _handle_mic_state(self, state: str):
        if self._muted:
            return
        if state == "idle":
            self._set_state("IDLE — say ALPHA", "idle")
            self._wave_full.set_active(False)
            self._wave_compact.set_active(False)
        elif state == "active":
            self._set_state("ACTIVE  •  LISTENING", "active")
            self._wave_full.set_active(True)
            self._wave_compact.set_active(True)
        elif state == "thinking":
            self._set_state("PROCESSING…", "thinking")
        elif state == "error":
            self._set_state("MIC ERROR", "error")

    def _on_wake(self):
        self._session_on = True
        self._show_banner(False)
        self._set_state("ACTIVE  •  LISTENING", "active")
        self._wave_full.set_active(True)
        self._wave_compact.set_active(True)
        self._heard_lbl.config(
            text="Session active — speak your commands.",
            fg=ACCENT2, font=("Consolas", 10, "italic"))
        try:
            self._heard_compact.config(text="Session active…")
        except Exception:
            pass
        self._log("[System] Wake word heard — session ACTIVE. Say 'goodbye' to stop.", ACCENT2)
        speak("Session active. Ready for your commands.")

    def _on_sleep(self):
        self._session_on = False
        self._show_banner(True)
        self._set_state("IDLE — say ALPHA", "idle")
        self._wave_full.set_active(False)
        self._wave_compact.set_active(False)
        self._heard_lbl.config(
            text='Session ended. Say "ALPHA" to reactivate.',
            fg=TEXT_GHOST, font=("Consolas", 10, "italic"))
        try:
            self._heard_compact.config(text='Say "ALPHA" to reactivate.')
        except Exception:
            pass
        self._res_lbl_full.config(text="Goodbye! Session closed.", fg=TEXT_MID)
        self._res_tag_full.config(text="", fg=GREEN)
        self._log("[System] Session ended. Listener back to IDLE.", TEXT_DIM)
        speak("Session ended. Say Alpha to reactivate.")

    def _on_translated(self, data: tuple):
        original, translated, lang = data
        lang_names = {
            "hi": "Hindi", "mr": "Marathi", "gu": "Gujarati",
            "bn": "Bengali", "ta": "Tamil",  "te": "Telugu",
            "kn": "Kannada", "pa": "Punjabi"
        }
        lang_display = lang_names.get(lang, lang.upper())
        self._heard_lbl.config(
            text=f'{lang_display}: "{original}"  →  "{translated}"',
            fg=ACCENT3, font=("Consolas", 9))
        try:
            self._heard_compact.config(text=f'{lang_display}: "{translated[:35]}"')
        except Exception:
            pass
        self._log(f'[{lang_display}] "{original}"  →  "{translated}"', ACCENT3)

    def _on_phrase(self, text: str):
        if self._muted or not self.classifier:
            return

        self._heard_lbl.config(text=f'"{text}"', fg=TEXT_DARK, font=("Consolas", 10))
        compact_heard = text if len(text) <= 42 else text[:39] + "…"
        try:
            self._heard_compact.config(text=f'"{compact_heard}"')
        except Exception:
            pass
        self._log(f'[Voice] "{text}"', ACCENT2)

        self._multi_badge.config(text="⚡ multi-task" if is_multi_task(text) else "")
        intent, conf = self.classifier.predict(text)
        self._intent_lbl.config(text=intent)
        self._conf_lbl.config(text=f"conf {conf:.0%}")
        self._update_cbar(conf)
        self._log(f'[NLP]   {intent}  ({conf:.0%})', TEXT_MID)

        results = execute(intent, text, classifier=self.classifier)
        
        for r in results:
            if r["result"] == "__SHUTDOWN__":
                self._log("[System] Shutdown command — closing ARCA.", RED)
                self.root.after(800, self._on_close)
                return
            self._log(f"[Exec]  [{r['intent']}] {r['result']}", GREEN)

        self._show_results(results)

        self.root.update_idletasks() 

        if results:
            if len(results) == 1:
                speak_text = results[0]["result"]
            else:
                speak_text = ". ".join(r["result"] for r in results)
            
            self.root.after(100, lambda: speak(speak_text))


    def _poll_timer(self):
        while self._timer_q:
            msg = self._timer_q.pop(0)
            self._show_results([{"cmd": "timer", "intent": "start_timer",
                                  "conf": 1.0, "result": msg}])
            self._log(msg, YELLOW)
            speak(msg)
        self.root.after(300, self._poll_timer)

    def _toggle_mute(self):
        self._muted = not self._muted
        lbl = "▶ UNMUTE" if self._muted else "⊘  MUTE"
        self._mute_btn_full.update_text(lbl)
        try:
            self._mute_btn_compact.update_text(lbl)
        except Exception:
            pass

        if self._muted:
            self._listener.stop()
            self._set_state("MUTED", "muted")
            self._wave_full.set_active(False)
            self._wave_compact.set_active(False)
            self._log("[System] Microphone muted.", RED)
        else:
            self._log("[System] Microphone unmuted.", GREEN)
            self._listener = ContinuousListener()
            self._listener.start()
            if self._session_on:
                self._set_state("ACTIVE  •  LISTENING", "active")
                self._wave_full.set_active(True)
                self._wave_compact.set_active(True)
            else:
                self._set_state("IDLE — say ALPHA", "idle")

    def _show_help(self):
        from tasks.info_tasks import show_help
        self._res_lbl_full.config(text=show_help(), fg=TEXT_MID)
        self._res_tag_full.config(text="HELP", fg=ACCENT)

    def _retrain(self):
        self._set_state("TRAINING…", "thinking")
        self._log("[System] Retraining LSTM model…", YELLOW)
        self._retrain_q = []

        def _do():
            from models.train_classifier import train
            def cb(ep, total, loss):
                if ep % 10 == 0:
                    self._retrain_q.append(f"  epoch {ep}/{total}  loss={loss:.4f}")
            train(progress_cb=cb)
            from core.classifier import IntentClassifier as IC
            self.classifier = IC()
            self._retrain_q.append("__DONE__")

        def _poll():
            while self._retrain_q:
                msg = self._retrain_q.pop(0)
                if msg == "__DONE__":
                    self._on_classifier_ready()
                    return
                self._log(msg, TEXT_DIM)
            self.root.after(200, _poll)

        threading.Thread(target=_do, daemon=True).start()
        self.root.after(200, _poll)

    def _on_close(self):
        self._alive = False
        self._listener.stop()
        try:
            self._cwin.destroy()
        except Exception:
            pass
        self.root.destroy()
