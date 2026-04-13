# ARCA — Intelligent Voice Automation Engine

> Double-clap or say **"ARCA"** to wake it up. Speak your command. Done.

ARCA (Automated Response and Command Architecture) is a fully offline-capable, voice-controlled desktop automation assistant for Windows. It classifies your intent using a trained BiLSTM+Attention neural network, executes real system tasks, and speaks every result back to you — opening apps, drafting AI emails, scraping live data, controlling Spotify, reading your Google Calendar, and more.

---

## Table of Contents

- [Demo Flow](#demo-flow)
- [Features](#features)
- [File Structure](#file-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Google Calendar Setup](#google-calendar-setup)
- [Email Setup](#email-setup)
- [WhatsApp Setup](#whatsapp-setup)
- [Ollama Setup](#ollama-setup)
- [Voice Commands](#voice-commands)
- [Hindi / Multilingual Support](#hindi--multilingual-support)
- [Compact Mode](#compact-mode)
- [Double-Clap Wake](#double-clap-wake)
- [Multi-Task Chaining](#multi-task-chaining)
- [Adding New Commands](#adding-new-commands)
- [Security — What NOT to commit](#security--what-not-to-commit)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)

---

## Demo Flow

```
👏👏  (two claps)
ARCA:  "Online. What do you need?"

You say:   "What are my meetings today?"
ARCA:      Reads your Google Calendar events aloud

You say:   "Write a professional email for sick leave"
ARCA:      AI drafts the full email → shows in terminal → press S to send

You say:   "मौसम कैसा है"  (Hindi: how is the weather)
ARCA:      Detects Hindi → translates → fetches weather → speaks result

You say:   "Play some music"
ARCA:      Launches Spotify

You say:   "Next song"
ARCA:      Skips track (works even if Spotify is minimised)

You say:   "Goodbye"
ARCA:      "Going to standby. Call me when you need me."
```

---

## Features

### Core
| Feature | Details |
|---|---|
| **Double-clap wake** | Two sharp claps → ARCA activates and brings window to front |
| **Voice wake word** | Say `"ARCA"` to activate, `"Goodbye"` to end session |
| **Push-to-activate** | Listens for one phrase at a time — no TTS feedback loop, no earphones needed |
| **Voice output (TTS)** | Speaks every result aloud via Windows SAPI5 — fully offline |
| **FRIDAY personality** | Professional, sharp responses — not robotic |
| **Hindi support** | Auto-detected → translated → executed, no extra setup |
| **Multi-task chaining** | `"Check CPU and check memory"` runs both in sequence |
| **Compact mode** | 360×170 always-on-top floating pill while you work |
| **BiLSTM classifier** | 56 intents, 3,150+ phrases, 93.2% validation accuracy |
| **Confidence gating** | Below 50% confidence → asks you to rephrase instead of guessing wrong |

### Automation
| Category | What it does |
|---|---|
| **System** | Open apps, screenshot, shutdown, restart, lock, sleep, task manager |
| **Hardware** | CPU, RAM, disk, battery, network — all spoken aloud |
| **Volume** | Up, down, mute, unmute |
| **Spotify** | Launch, play/pause, next, previous — global media keys, no window focus needed |
| **WhatsApp** | Send messages by voice via pywhatkit |
| **Email** | AI writes the full email via Ollama → SMTP send |
| **Calendar** | List events, create events, find free slots via Google Calendar API |
| **Web search** | Search and summarise — scrapes web + Ollama digest |
| **News** | Live headlines from BBC, Times of India, Reuters |
| **Weather** | Current, hourly, weekly via wttr.in |
| **Files** | Find any file by name across your entire drive, open it |
| **OCR** | Read text off your screen or clipboard image |
| **Proactive** | Background monitor — alerts for low battery, high RAM, upcoming meetings |

---

## File Structure

```
ARCA/
│
├── main.py                          # Entry point — auto-trains on stale model
├── config.py                        # Settings, colours, paths, CONTACTS dict
├── requirements.txt                 # pip dependencies
├── .gitignore                       # ← credentials.json and token.json MUST be listed here
│
├── core/
│   ├── listener.py                  # Push-to-activate session listener
│   ├── clap_detector.py             # Double-clap wake via PyAudio RMS analysis
│   ├── classifier.py                # Loads BiLSTM+Attention model, predict()
│   ├── executor.py                  # Routes 56 intents → task functions
│   ├── multi_task_parser.py         # Splits "do X and Y" into [X, Y]
│   ├── translator.py                # langdetect + deep-translator
│   ├── speaker.py                   # pyttsx3 SAPI5 — persistent daemon thread
│   └── logger.py                    # Timestamped log
│
├── models/
│   ├── intents.json                 # 56 intents × 50+ phrases = 3,150+ examples
│   ├── train_classifier.py          # BiLSTM+Attention, FocalLoss, augmentation
│   └── intent_model.pkl             # Auto-generated on first run (git-ignored)
│
├── tasks/
│   ├── app_launcher.py              # 60+ known apps + Start Menu fallback
│   ├── system_tasks.py              # battery, CPU, RAM, disk, screenshot, power
│   ├── browser_tasks.py             # search, YouTube, GitHub
│   ├── file_tasks.py                # OS file/folder ops
│   ├── communication_tasks.py       # reminders
│   ├── productivity_tasks.py        # timer, notes, calendar opener
│   ├── info_tasks.py                # time, date, jokes, facts, ARCA greetings
│   ├── friday_personality.py        # FRIDAY-style response wrapping
│   ├── ai_email.py                  # Ollama drafts full email → SMTP send
│   ├── whatsapp_tasks.py            # pywhatkit send
│   ├── spotify_tasks.py             # ctypes VK media keys + PyAutoGUI for search
│   ├── scraper_news.py              # BBC / TOI / Reuters BeautifulSoup scraper
│   ├── scraper_trends.py            # Google Trends RSS
│   ├── scraper_weather.py           # wttr.in JSON (current/hourly/weekly)
│   ├── calendar_tasks.py            # Google Calendar API (OAuth2)
│   ├── search_summarize.py          # Google scrape + Ollama summarisation
│   ├── file_search.py               # os.walk filesystem search, open files
│   ├── ocr_tasks.py                 # pytesseract screen/clipboard OCR
│   └── proactive.py                 # background battery/RAM/CPU/calendar monitor
│
└── ui/
    └── app_window.py                # Full (1100×800) + Compact (360×170) Tkinter UI
```

---

## Installation

### 1. Prerequisites

- **Python 3.11** — [download](https://www.python.org/downloads/)
- **Google Chrome** — for WhatsApp Web automation
- **Internet connection** — for STT (Google Speech API) and web scraping

### 2. Clone the project

```bash
git clone https://github.com/InsaneSoul207/ARCA.git
cd ARCA
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **PyAudio on Windows (most common issue):**
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

> **PyTorch CPU-only (saves ~2 GB):**
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> ```

> **Tesseract OCR (optional — for read_screen / clipboard OCR):**
> Download and install from https://github.com/UB-Mannheim/tesseract/wiki
> Default install path: `C:\Program Files\Tesseract-OCR\`

### 4. Run

```bash
python main.py
```

On **first run**, the BiLSTM model trains automatically from `models/intents.json`. This takes 1–3 minutes and only happens once. After that, startup is instant.

---

## Configuration

All core settings are in `config.py`:

```python
WAKE_WORD        = "arca"      # what you say to activate
ENERGY_THRESHOLD = 200         # lower = more sensitive mic
PAUSE_THRESHOLD  = 0.7         # seconds of silence that ends a phrase
DEFAULT_CITY     = "Delhi"     # for weather commands
```

---

## Google Calendar Setup

This is a one-time process. Once set up, ARCA can read and create calendar events by voice.

### Step 1 — Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project** → **New Project** → name it `ARCA` → click **Create**

### Step 2 — Enable the Google Calendar API

1. In your project, go to **APIs & Services** → **Library**
2. Search for **Google Calendar API** → click it → click **Enable**

### Step 3 — Create OAuth 2.0 credentials

1. Go to **APIs & Services** → **Credentials**
2. If prompted to configure the OAuth consent screen:
   - Click **Configure Consent Screen** → choose **External** → fill in App name (`ARCA`) → **Save and Continue** through all steps
3. Click **+ Create Credentials** → **OAuth client ID**
4. Application type: **Desktop app** → name it anything → click **Create**
5. In the dialog that appears, click **Download JSON**
6. Rename the downloaded file to exactly **`credentials.json`**
7. Place it in the **root of your ARCA project folder**, next to `main.py`

```
ARCA/
├── main.py
├── credentials.json    ← place here (NEVER commit to git)
├── .gitignore          ← must list credentials.json
└── ...
```

### Step 4 — Authenticate (first calendar command only)

1. Run ARCA: `python main.py`
2. Say any calendar command — e.g. **"what are my meetings today"**
3. A browser tab opens automatically asking you to sign in with Google
4. Click **Allow** to grant ARCA access to your calendar
5. The browser tab closes and ARCA reads your events
6. A `token.json` file is created in the project root — this caches your login so you won't be asked again

```
ARCA/
├── main.py
├── credentials.json    ← your app credentials  ⚠️ never commit
├── token.json          ← your session token    ⚠️ never commit
├── .gitignore          ← both files listed here
└── ...
```

### Step 5 — Verify

Say: **"What are my meetings today?"**
ARCA should speak your calendar events. If it says "Google Calendar not configured", make sure `credentials.json` is in the same folder as `main.py`.

### Re-authenticating

If your token expires or you switch Google accounts, delete `token.json` and the browser will open again on the next calendar command:

```bash
del token.json
```

---

## ⚠️ Security — What NOT to commit

**Never push `credentials.json` or `token.json` to GitHub.** These contain your private Google OAuth keys. GitHub's push protection will block the push, and the credentials must be revoked immediately if exposed.

Your `.gitignore` file must contain:

```gitignore
# Google OAuth — NEVER commit these
credentials.json
client_secret_*.json
token.json

# Trained model (large binary, auto-regenerated)
models/intent_model.pkl

# WhatsApp session (login cookies)
whatsapp_session/

# Python / editor
.env
__pycache__/
*.pyc
*.pyo
.vscode/
```

### If you accidentally committed them

```bash
# 1. Remove from git tracking
git rm --cached token.json
git rm --cached credentials.json

# 2. Scrub from ALL past commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch token.json credentials.json client_secret_*.json" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Commit the .gitignore
git add .gitignore
git commit -m "Remove OAuth secrets, add to gitignore"

# 4. Force push
git push origin main --force
```

Then go to [console.cloud.google.com](https://console.cloud.google.com) → **Credentials** → **delete the exposed OAuth client** → create a new one and download a fresh `credentials.json`.

---

## Email Setup

ARCA uses Gmail SMTP to send AI-drafted emails. Requires a Gmail App Password — not your real Gmail password.

### Step 1 — Create a Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com) → **Security**
2. Ensure **2-Step Verification** is turned on
3. Click **App Passwords** (appears at the bottom of the Security page)
4. Select app: **Mail** → device: **Windows Computer** → click **Generate**
5. Copy the 16-character password shown

### Step 2 — Set environment variables

```cmd
setx ALPHA_EMAIL "yourname@gmail.com"
setx ALPHA_EMAIL_PASSWORD "xxxx xxxx xxxx xxxx"
```

Restart any open terminals after running `setx`. These are stored in Windows — never in your code.

### Test it

Say: **"Write a professional email for sick leave"**
ARCA uses Ollama to draft the full email, displays it in the terminal, and prompts: `[S]end  [E]dit  [D]iscard`.

---

## WhatsApp Setup

### Step 1 — Add contacts to `config.py`

```python
CONTACTS = {
    "mom":    "+919876543210",   # country code required
    "mum":    "+919876543210",   # alias — same number
    "dad":    "+919876543211",
    "john":   "+919876543212",
}
```

### Step 2 — First send (QR scan)

On the first WhatsApp command, Chrome opens WhatsApp Web. Scan the QR code with your phone. The session is saved in `whatsapp_session/` so you only scan once.

### Test it

Say: **"Send a WhatsApp to Mom saying I'll be late"**

---

## Ollama Setup

Ollama powers AI email drafting and web search summarisation — fully local, no API key.

```bash
# 1. Download from https://ollama.com and install
# 2. Pull the model
ollama pull llama3
# 3. Ollama runs as a background service automatically
```

ARCA gracefully skips Ollama-dependent features if it's not running, and shows a message in the log.

---

## Voice Commands

Say **"ARCA"** or **double-clap** to activate, then speak naturally:

### System
```
open browser / calculator / notepad / task manager
take a screenshot
check battery / cpu / memory / disk / network
volume up / volume down / mute / unmute
lock screen / sleep pc / restart / shutdown
```

### Apps
```
open whatsapp / discord / telegram / word / excel / vscode
open spotify / vlc / steam / chrome / firefox
```
*Say any app name — ARCA searches your Start Menu if it's not in the known list.*

### Spotify
```
play some music          → launches Spotify
pause spotify            → pauses (works minimised)
next song / skip         → next track (works minimised)
previous song            → previous track (works minimised)
play despacito           → searches Spotify for the song
like this song           → hearts the current track
```

### Calendar
```
what are my meetings today
what is on my calendar this week
add a meeting tomorrow at 3pm
schedule a call with John on Friday at 5pm
when am I free today
delete the project review meeting
```

### Web & Scraping
```
search and summarise quantum computing
research climate change and summarise
bbc news / times of india / reuters headlines
what is trending / show google trends
check the weather / hourly forecast / weather this week
```

### WhatsApp
```
send a whatsapp to Mom saying I will be late
whatsapp John hey are you free tonight
```

### Email
```
write a mail for sick leave
write a professional email to my professor
draft an email asking for a deadline extension
compose a formal mail to the client
```

### Files
```
find my resume pdf
open the project proposal
find all python files in downloads
show recent files
read the screen
read clipboard image
```

### Productivity
```
start a timer for 10 minutes
stop the timer
take a note meeting at 3pm
show my notes / clear notes
set a reminder to call mom
```

### Info
```
what time is it
what is today's date
tell me a joke / tell me a fact
hello / good morning
goodbye   ← ends the session
help      ← lists all commands
```

---

## Hindi / Multilingual Support

ARCA understands Hindi, Hinglish, and 7 other Indian languages. No extra setup.

### How it works

```
You speak Hindi
    ↓
Google STT transcribes with hi-IN locale
    ↓
langdetect identifies the language
(phrases < 5 words skip detection to avoid false positives)
    ↓
deep-translator → Google Translate → English (free, no API key)
    ↓
BiLSTM classifier + executor (same pipeline as English)
```

### Examples

| You say | ARCA executes |
|---|---|
| `"मौसम कैसा है"` | Fetches weather |
| `"स्क्रीनशॉट लो"` | Takes screenshot |
| `"टाइमर शुरू करो पांच मिनट"` | Starts 5-min timer |
| `"whatsapp karo Mom ko"` | Sends WhatsApp (Hinglish — passed through as-is) |

Supported languages: Hindi, Marathi, Gujarati, Bengali, Tamil, Telugu, Kannada, Punjabi

---

## Compact Mode

Press **Ctrl+M** to shrink ARCA into a 360×170 floating pill in the top-right corner — always on top of other windows.

- Drag it anywhere by clicking and dragging
- Shows last heard command and last result
- Waveform animation still active
- Press **⊞ EXPAND** or Ctrl+M again to return to full mode
- Listener and clap detector keep running in both modes

---

## Double-Clap Wake

Clap twice sharply within 1.5 seconds and ARCA wakes up — even if the window is minimised.

- Works from across the room
- No button or keyboard shortcut needed
- Window pops to front automatically
- If a session is already active, ARCA says "Here."

**Adjusting sensitivity** — open `core/clap_detector.py`:

```python
CLAP_THRESHOLD = 3000   # raise to 5000 if random sounds trigger it
                        # lower to 1500 if claps aren't detected
```

---

## Multi-Task Chaining

Say multiple commands in one breath using `and`, `then`, `also`, `after that`:

```
"Check CPU and check memory and check battery"
"Open Chrome and search for Python tutorials"
"Take a screenshot then set a timer for 5 minutes"
```

Each sub-command is classified and executed independently. An `⚡ multi-task` badge appears in the UI.

---

## Adding New Commands

### Step 1 — Add phrases to `models/intents.json`

```json
"my_new_intent": [
  "phrase one",
  "phrase two",
  "another way to say it"
]
```

Aim for 50 phrases per intent using natural speech patterns.

### Step 2 — Add a task function in `tasks/`

```python
# tasks/my_tasks.py
def my_function(raw: str) -> str:
    return "Done."
```

### Step 3 — Route it in `core/executor.py`

```python
from tasks import my_tasks

if intent == "my_new_intent":
    return my_tasks.my_function(raw)
```

### Step 4 — Retrain

Delete `models/intent_model.pkl` and restart, or click **RETRAIN** in the UI.

---

## Troubleshooting

**`AttributeError: 'Alpha2App' object has no attribute '_clap'`**
Replace `app_window.py` with the latest version — `self._clap = ClapDetector()` was missing from `__init__`.

**App closes after ~10 seconds on startup**
Three PyAudio streams were conflicting. Make sure you have the latest `app_window.py` — the clap detector now starts 3 seconds after the listener.

**ARCA hears its own voice and executes random commands**
You are using the old `continuous_listener.py`. Switch to `listener.py` (push-to-activate) — it waits 2.5 seconds after speaking before re-opening the mic.

**Google Calendar says "not configured" or "credentials not found"**
- Confirm `credentials.json` is in the same folder as `main.py`
- Delete `token.json` and re-authenticate
- Check that Google Calendar API is enabled in your Google Cloud project
- Make sure you downloaded the credentials as **OAuth 2.0 Client ID**, not a Service Account key

**Calendar authentication fails or browser doesn't open**
Make sure the OAuth consent screen is set to **External** and your Google account is added as a test user in Google Cloud Console → **OAuth consent screen** → **Test users**.

**Email JSON error / AI writes only "Hello"**
Replace `tasks/ai_email.py` with the latest version. The old version requested JSON from Ollama (caused control character errors). The new version uses `SUBJECT:`/`BODY:` plain text format.

**"write a mail" goes to take_note**
Delete `models/intent_model.pkl` and retrain with the latest `intents.json` — training data was rewritten to fix this conflict.

**PyAudio install fails**
```bash
pip install pipwin && pipwin install pyaudio
```

**WhatsApp says contact not found**
Add the contact to `CONTACTS` in `config.py` with full number including country code (`+91...`).

**Spotify doesn't open**
ARCA searches for `Spotify.exe` in `%APPDATA%\Spotify\` and `%LOCALAPPDATA%\Microsoft\WindowsApps\`. If installed elsewhere, it falls back to Start Menu search via PyAutoGUI (requires `pip install pyautogui`).

**Volume control fails**
```bash
pip install pycaw comtypes
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| GUI | Tkinter (stdlib) |
| Neural Network | PyTorch — BiLSTM + Self-Attention |
| Speech-to-Text | Google STT via `SpeechRecognition` (en-IN + hi-IN) |
| Text-to-Speech | `pyttsx3` → Windows SAPI5 (fully offline) |
| Wake detection | PyAudio — RMS energy clap analysis (`ctypes`) |
| Language detection | `langdetect` |
| Translation | `deep-translator` → Google Translate (free, no API key) |
| AI email + search | Ollama (`llama3`) — runs locally |
| Web scraping | `BeautifulSoup4` + `requests` |
| WhatsApp | `pywhatkit` |
| Email | Python `smtplib` → Gmail SMTP |
| Calendar | `google-api-python-client` + OAuth2 |
| Spotify | `ctypes` VK media keys (global, no focus needed) |
| System stats | `psutil` |
| Volume control | `pycaw` + `comtypes` |
| File search | `pathlib` + `os.walk` (stdlib) |
| OCR | `pytesseract` + `Pillow` |

---

## License

MIT — do whatever you want with it.

---

*ARCA — Built as a DTI project, Bennett University, Year 2 Sem 4.*  
*Team: Eshaan Mishra · Ahmed Bin Asad · Anubhav Punia · Kunsh Kakkar*
