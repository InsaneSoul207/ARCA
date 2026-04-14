# ARCA — Intelligent Voice Automation Engine

> Say **"Alpha"** to wake it up. Speak your command. Done.

ARCA is a fully offline-capable, voice-controlled desktop automation assistant for Windows. It listens continuously, understands natural English and Hindi, classifies your intent using a trained LSTM neural network, and executes real system tasks — opening apps, sending emails, scraping live data, controlling WhatsApp, and more.

---

## Table of Contents

- [Demo Flow](#demo-flow)
- [Features](#features)
- [File Structure](#file-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Voice Commands](#voice-commands)
- [Hindi / Multilingual Support](#hindi--multilingual-support)
- [Compact Mode](#compact-mode)
- [Multi-Task Chaining](#multi-task-chaining)
- [Adding New Commands](#adding-new-commands)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)

---

## Demo Flow

```
You say:   "Alpha"
Alpha:     "Session active. Ready for your commands."

You say:   "Open WhatsApp"
Alpha:     Opens WhatsApp desktop app

You say:   "Send WhatsApp to John hey are you free tonight"
Alpha:     Navigates WhatsApp Web → opens John's chat → sends message

You say:   "What's trending"
Alpha:     Scrapes Google Trends → displays top 10 trending topics

You say:   "मौसम कैसा है"  (Hindi: how is the weather)
Alpha:     Detects Hindi → translates → fetches weather → speaks result

You say:   "Goodbye"
Alpha:     "Session ended. Say Alpha to reactivate."
```

---

## Features

### Core
| Feature | Details |
|---|---|
| **Always-on listener** | Runs continuously in the background, no button press needed |
| **Wake word** | Say `"Alpha"` to activate, `"Goodbye"` to deactivate |
| **Session mode** | Once activated, every phrase is a command until you say goodbye |
| **Voice output (TTS)** | Speaks every result aloud using Windows SAPI5 — fully offline |
| **Hindi support** | Speaks Hindi → auto-detected → translated to English → executed |
| **Multi-task chaining** | `"Open Chrome and search for Python tutorials"` runs both in sequence |
| **Compact mode** | 360×170 floating pill that stays on top of all windows while you work |
| **LSTM classifier** | Trained neural network with 43 intents and 2,100+ training phrases |

### Automation
| Category | Commands |
|---|---|
| **System** | Open apps, screenshot, shutdown, restart, lock, sleep, task manager |
| **Hardware** | CPU usage, RAM, disk space, battery, network status |
| **Volume** | Up, down, mute/unmute |
| **Files** | Create, list, open Downloads / Documents / Desktop, empty recycle bin |
| **Browser** | Search Google, open YouTube / GitHub / Spotify |
| **Apps** | Open any installed app by name — 60+ known apps + Start Menu fallback |
| **WhatsApp** | Send messages via WhatsApp Web (Selenium) |
| **Email** | Draft and send via Gmail SMTP |
| **Productivity** | Timer, notes (persistent), calendar |
| **Scraping** | Live news (BBC / TOI / Reuters), Google Trends, detailed weather |
| **Info** | Time, date, jokes, facts |

---

## File Structure

```
alpha2/
│
├── main.py                        # Entry point
├── config.py                      # All settings, colours, paths, constants
├── requirements.txt               # pip dependencies
│
├── core/
│   ├── continuous_listener.py     # Always-on mic, wake/sleep state machine
│   ├── classifier.py              # Loads + runs the LSTM intent classifier
│   ├── executor.py                # Routes intent → task function
│   ├── multi_task_parser.py       # Splits "do X and Y" into [X, Y]
│   ├── translator.py              # Hindi/Hinglish → English translation
│   ├── speaker.py                 # Text-to-speech (pyttsx3 / SAPI5)
│   └── logger.py                  # In-memory + file logger
│
├── models/
│   ├── intents.json               # 43 intents × ~50 phrases = 2,100+ examples
│   ├── train_classifier.py        # LSTM training script
│   └── intent_model.pkl           # Saved model (auto-generated on first run)
│
├── tasks/
│   ├── app_launcher.py            # Opens any Windows app by name
│   ├── system_tasks.py            # OS-level: battery, CPU, RAM, power, volume
│   ├── browser_tasks.py           # Web: search, YouTube, GitHub
│   ├── file_tasks.py              # File and folder operations
│   ├── communication_tasks.py     # Clipboard, reminders
│   ├── productivity_tasks.py      # Timer, notes, calendar
│   ├── info_tasks.py              # Time, date, jokes, facts, help
│   ├── email_tasks.py             # Draft + send email via Gmail SMTP
│   ├── whatsapp_tasks.py          # WhatsApp Web automation via Selenium
│   ├── scraper_news.py            # Live headlines: BBC, TOI, Reuters
│   ├── scraper_trends.py          # Google Trends + Twitter/X trending
│   └── scraper_weather.py         # Detailed weather: current, hourly, weekly
│
└── ui/
    └── app_window.py              # Full (900×700) + Compact (360×170) UI
```

---

## Installation

### 1. Prerequisites

- **Python 3.10 or higher** — [download](https://www.python.org/downloads/)
- **Google Chrome** — required for WhatsApp Web automation
- **Internet connection** — for STT (Google Speech API) and web scraping

### 2. Clone / download the project

```bash
git clone https://github.com/InsaneSoul207/ARCA.git
cd ARCA
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **PyAudio (most common issue):** If `pip install pyaudio` fails on Windows:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```
> Or download the prebuilt wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

> **PyTorch (CPU-only, saves ~2 GB):**
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> ```

### 4. Run

```bash
python main.py
```

On **first run**, the LSTM model is trained automatically from `models/intents.json`. This takes about 60 seconds and only happens once. After that, startup is instant.

---

## Configuration

All settings live in `config.py`. Key ones to know:

```python
# Wake word — what you say to activate Alpha
WAKE_WORD = "alpha"           # change to anything you want

# Microphone sensitivity
ENERGY_THRESHOLD = 200        # lower = picks up quieter speech
PAUSE_THRESHOLD  = 0.7        # seconds of silence that ends a phrase

# TTS speech rate
# (change in code: from core.speaker import set_rate; set_rate(150))

# Default city for weather
# (in tasks/scraper_weather.py)
DEFAULT_CITY = "Delhi"
```

### Email setup (optional)

To enable actual email sending (not just opening the mail client):

```bash
# Windows — set environment variables
set ALPHA_EMAIL=yourname@gmail.com
set ALPHA_EMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

Get a Gmail App Password: Google Account → Security → 2-Step Verification → App Passwords → Create one named "ARCA".

---

## Voice Commands

Say **"Alpha"** first to activate, then any of these:

### System
```
open browser / calculator / notepad / task manager
take a screenshot
check battery / cpu / memory / disk / network
volume up / volume down / mute
lock screen / sleep pc / restart / shutdown
```

### Apps
```
open whatsapp
open word / excel / powerpoint
open discord / telegram / slack / zoom
open vscode / pycharm / android studio
open spotify / vlc / steam
open chrome / firefox / edge
```
*Say the app name naturally — Alpha searches your Start Menu if it's not in the known list.*

### Web & Scraping
```
search for <anything>
what's trending / show google trends
bbc news / times of india / reuters headlines
check the weather / hourly forecast / weather this week
open youtube / github / spotify
get the news
```

### WhatsApp
```
send whatsapp to John hey are you free
whatsapp Mom I am on my way
close whatsapp browser
whatsapp status
```

### Email
```
send email to john@gmail.com about the project
draft an email to Priya
compose email
```
*Fill in recipient, subject, and body in the terminal that opens.*

### Productivity
```
start a timer for 10 minutes
stop the timer
take a note meeting at 3pm
show my notes
clear notes
set a reminder to call mom
open calendar
```

### Info
```
what time is it
what is today's date
tell me a joke
tell me a fact
hello / good morning
goodbye   ← ends the session
help      ← lists all commands
```

---

## Hindi / Multilingual Support

Alpha understands Hindi, Hinglish, and 7 other Indian languages. No extra setup required — it works out of the box.

### How it works

```
You speak Hindi
    ↓
Google STT transcribes with hi-IN language code
    ↓
langdetect identifies the language
    ↓
deep-translator translates to English (Google Translate, free, no API key)
    ↓
LSTM classifier + executor (same as English path)
```

### Examples

| You say | Alpha hears | Executes |
|---|---|---|
| `"अल्फा"` | "alpha" | Activates session |
| `"मौसम कैसा है"` | "how is the weather" | Fetches weather |
| `"स्क्रीनशॉट लो"` | "take a screenshot" | Takes screenshot |
| `"टाइमर शुरू करो पांच मिनट"` | "start timer five minutes" | Starts 5-min timer |
| `"whatsapp karo John ko kal milte hain"` | passed through as-is (Hinglish) | Sends WhatsApp |

### Supported languages

Hindi, Marathi, Gujarati, Bengali, Tamil, Telugu, Kannada, Punjabi

The UI shows translations in real time — you'll see `Hindi: "मौसम कैसा है" → "how is the weather"` in the VOICE INPUT panel.

---

## Compact Mode

Press **Ctrl+M** or click the **COMPACT** button to shrink Alpha into a 360×170 floating pill that sits in the top-right corner of your screen — always on top of other windows.

- Drag it anywhere by clicking and dragging
- Full waveform animation in compact mode too
- Shows last heard command and last result
- Click **⊞ EXPAND** to go back to full mode
- The listener keeps running regardless of which mode you're in

---

## Multi-Task Chaining

Say multiple commands in one breath, connected by `and`, `then`, `also`, `after that`:

```
"Open Chrome and search for Python tutorials"
"Check CPU and check memory and check battery"
"Take a screenshot then set a timer for 5 minutes"
"Open notepad and take a note meeting at 3pm"
```

Each sub-command is classified and executed independently. Results show as a numbered list. An `⚡ multi-task` badge appears in the UI when chaining is detected.

---

## Adding New Commands

### Step 1 — Add training phrases to `models/intents.json`

```json
"my_new_intent": [
  "phrase one",
  "phrase two",
  "another way to say it",
  ...
]
```

Aim for at least 40–50 phrases per intent. Vary the phrasing naturally.

### Step 2 — Add a task function in `tasks/`

```python
# tasks/my_tasks.py
def my_function() -> str:
    # do something
    return "Done."
```

### Step 3 — Route it in `core/executor.py`

```python
from tasks import my_tasks

# inside _route():
if intent == "my_new_intent":
    return my_tasks.my_function()
```

### Step 4 — Retrain

Either restart `main.py` (auto-retrains when `intents.json` is newer than the model), or click **RETRAIN** in the UI.

---

## Troubleshooting

**`TclError: invalid command name "826"`**
You're using an older version of `app_window.py`. Update to the latest — this was a Tkinter internal attribute conflict that has been fixed.

**`PyEval_RestoreThread: GIL released` crash**
You're using an older version of `continuous_listener.py`. Update to the latest — all Tkinter calls now happen on the main thread via a queue poller.

**PyAudio install fails**
```bash
pip install pipwin && pipwin install pyaudio
```

**`recognize_google` fails / no internet**
Google STT requires internet. Alpha cannot transcribe speech offline (the LSTM classifier runs offline, but the mic-to-text step needs Google's servers).

**Model accuracy is poor / wrong intents classified**
Click **RETRAIN** in the UI, or delete `models/intent_model.pkl` and restart. If a specific command keeps misclassifying, add more training phrases for that intent in `intents.json`.

**WhatsApp asks to scan QR every time**
Make sure the `whatsapp_session/` folder is not being deleted between runs. This folder stores the Chrome profile that keeps you logged in.

**Hindi not being detected**
```bash
pip install langdetect deep-translator
```
Both packages are required. Alpha gracefully skips translation if they're missing but will log a warning at startup.

**Volume control fails**
`pycaw` is Windows-only and requires `comtypes`. Run:
```bash
pip install pycaw comtypes
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI | Tkinter (stdlib) |
| Speech-to-text | Google STT via `SpeechRecognition` + `pyaudio` |
| Text-to-speech | `pyttsx3` → Windows SAPI5 (offline) |
| Intent classification | PyTorch LSTM (2-layer, trained on `intents.json`) |
| Language detection | `langdetect` |
| Translation | `deep-translator` → Google Translate (free, no API key) |
| Web scraping | `BeautifulSoup4` + `lxml` + `requests` |
| WhatsApp automation | `selenium` + `webdriver-manager` |
| Email | Python `smtplib` → Gmail SMTP |
| System stats | `psutil` |
| Volume control | `pycaw` + `comtypes` (Windows Core Audio) |
| Screenshots | `Pillow` (ImageGrab) |
| Clipboard | `pyperclip` |

---

## License

MIT — do whatever you want with it.

---

*Built as an AIML project — Year 2, Sem 4.*
