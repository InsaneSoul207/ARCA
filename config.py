"""
ARCA — Central Configuration
All paths, model hyper-parameters, speech settings, UI colours and fonts live here.
Import with:  from config import *   (UI files)
              from config import X, Y  (specific files)
"""
import os
 
# ── Identity ───────────────────────────────────────────────────────────────────
APP_NAME = "ARCA"
VERSION  = "MVP-1.0  |  Windows"
 
# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, "models", "intent_model.pkl")
INTENTS_JSON  = os.path.join(BASE_DIR, "models", "intents.json")   
LOG_PATH      = os.path.join(BASE_DIR, "alpha_log.txt")
NOTES_PATH    = os.path.join(BASE_DIR, "alpha_notes.txt")
 
# ── Speech / microphone ────────────────────────────────────────────────────────
ENERGY_THRESHOLD    = 200     # mic sensitivity — lower = picks up quieter speech
PAUSE_THRESHOLD     = 0.7     # seconds of silence that ends a phrase
PHRASE_TIME_LIMIT   = 12      # max seconds per single utterance
DYNAMIC_ENERGY      = True    # auto-adjust threshold to ambient noise
 
# ── Wake word ──────────────────────────────────────────────────────────────────
WAKE_WORD = "alpha"            # say this before every command  e.g. "ARCS open whatsapp"
                              # set to None to disable (every phrase processed)
 
# ── LSTM classifier hyper-parameters ──────────────────────────────────────────
MAX_SEQUENCE_LEN = 28         # max tokens per input phrase (increased from 20)
EMBEDDING_DIM    = 128        # word embedding size (increased from 64)
HIDDEN_DIM       = 256        # LSTM hidden state size (increased from 128)
EPOCHS           = 200        # training epochs (with early stopping)
LEARNING_RATE    = 0.001      # AdamW initial learning rate (tuned for larger model)
 
# ── UI — window sizes ──────────────────────────────────────────────────────────
FULL_W, FULL_H       = 900, 700    # main window
COMPACT_W, COMPACT_H = 360, 160    # floating compact pill
 
# ── UI — light futuristic colour palette ───────────────────────────────────────
# Backgrounds  (near-white, cold blue tint — "arctic frosted glass")
BG_BASE  = "#050505"    # Main window surface (Black)
BG_PANEL = "#0D0D0D"    # Card / panel surfaces (Dark Gray)
BG_DEEP  = "#121212"    # Inset / recessed areas, top bar, log pane
BG_GLASS = "#1A1A1A"    # Button default fill

# Accents (Retaining your theme_cyan)
ACCENT  = "#00D4FF"     # Primary — Electric Cyan (The "ARCA" Blue)
ACCENT2 = "#008FB3"     # Secondary — Muted Cyan
ACCENT3 = "#6E3FFF"     # Tertiary — Violet

# Text
TEXT_DARK  = "#FFFFFF"  # Pure White — Headings, result text
TEXT_MID   = "#E0E0E0"  # Light Gray — Body copy, log entries
TEXT_DIM   = "#888888"  # Muted Gray — Labels, hints
TEXT_GHOST = "#333333"  # Very Muted — Placeholders

# State / feedback colours
GREEN  = "#00C48C"      # Success
RED    = "#FF3B5C"      # Error / Muted
YELLOW = "#FFB800"      # Thinking
ORANGE = "#FF6B2B"      # Warning

# Borders
BORDER      = "#1F1F1F"  # Subtle dark border
BORDER_GLOW = "#00D4FF"  # Focused / Hover glow (ACCENT)

# ── UI — font stack (all Consolas — monospaced HUD aesthetic) ─────────────────
FONT_TITLE  = ("Consolas", 22, "bold")   # app name in top bar
FONT_HEAD   = ("Consolas", 11, "bold")   # button labels, section headers
FONT_BODY   = ("Consolas", 10)           # result text, heard text
FONT_SMALL  = ("Consolas",  9)           # status label, clock
FONT_MICRO  = ("Consolas",  8)           # card sub-labels ("VOICE INPUT", "INTENT")
FONT_LOG    = ("Consolas",  8)           # log pane entries
FONT_COMPACT= ("Consolas",  8)           # compact mode labels


CONTACTS={} #insert your contacts here in the format "Name": "Phone Number"
