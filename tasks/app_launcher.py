import os, subprocess, glob, shutil
from core.logger import log

# ── Known app table ────────────────────────────────────────────────────────────
KNOWN_APPS: dict[str, str | list] = {
    "whatsapp":        r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe",
    "telegram":        r"%APPDATA%\Telegram Desktop\Telegram.exe",
    "discord":         r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe",
    "slack":           r"%LOCALAPPDATA%\slack\slack.exe",
    "teams":           r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe",
    "zoom":            r"%APPDATA%\Zoom\bin\Zoom.exe",
    "signal":          r"%LOCALAPPDATA%\Programs\signal-desktop\Signal.exe",
    "skype":           r"%APPDATA%\Microsoft\Teams\current\Teams.exe",

    "word":            r"%PROGRAMFILES%\Microsoft Office\root\Office16\WINWORD.EXE",
    "microsoft word":  r"%PROGRAMFILES%\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":           r"%PROGRAMFILES%\Microsoft Office\root\Office16\EXCEL.EXE",
    "microsoft excel": r"%PROGRAMFILES%\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":      r"%PROGRAMFILES%\Microsoft Office\root\Office16\POWERPNT.EXE",
    "onenote":         r"%PROGRAMFILES%\Microsoft Office\root\Office16\ONENOTE.EXE",
    "outlook":         r"%PROGRAMFILES%\Microsoft Office\root\Office16\OUTLOOK.EXE",
    "access":          r"%PROGRAMFILES%\Microsoft Office\root\Office16\MSACCESS.EXE",

    "visual studio code": r"%LOCALAPPDATA%\\Programs\\Microsoft VS Code\Code.exe",
    "vscode":             r"%LOCALAPPDATA%\\Programs\\Microsoft VS Code\Code.exe",
    "vs code":            r"%LOCALAPPDATA%\\Programs\\Microsoft VS Code\Code.exe",
    "visual studio":      r"%PROGRAMFILES%\\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
    "pycharm":            r"%LOCALAPPDATA%\\Programs\\PyCharm Community\bin\pycharm64.exe",
    "android studio":     r"%LOCALAPPDATA%\\Programs\\Android Studio\bin\studio64.exe",
    "git bash":           r"%PROGRAMFILES%\\Git\git-bash.exe",
    "cmd":                "cmd.exe",
    "command prompt":     "cmd.exe",
    "powershell":         "powershell.exe",
    "terminal":           "wt.exe",          # Windows Terminal
    "windows terminal":   "wt.exe",
    "postman":            r"%LOCALAPPDATA%\\Postman\Postman.exe",
    "docker":             r"%PROGRAMFILES%\\Docker\Docker\Docker Desktop.exe",

    "chrome":             r"%PROGRAMFILES%\\Google\Chrome\Application\chrome.exe",
    "google chrome":      r"%PROGRAMFILES%\\Google\Chrome\Application\chrome.exe",
    "firefox":            r"%PROGRAMFILES%\\Mozilla Firefox\firefox.exe",
    "mozilla firefox":    r"%PROGRAMFILES%\\Mozilla Firefox\firefox.exe",
    "edge":               r"%PROGRAMFILES(X86)%\\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge":     r"%PROGRAMFILES(X86)%\\Microsoft\Edge\Application\msedge.exe",
    "brave":              r"%LOCALAPPDATA%\\BraveSoftware\Brave-Browser\Application\brave.exe",
    "opera":              r"%APPDATA%\\Opera Software\Opera Stable\opera.exe",

    # Media
    "spotify":            r"%APPDATA%\Spotify\Spotify.exe",
    "vlc":                r"%PROGRAMFILES%\\VideoLAN\VLC\vlc.exe",
    "media player":       r"%PROGRAMFILES%\\Windows Media Player\wmplayer.exe",
    "windows media player": r"%PROGRAMFILES%\\Windows Media Player\wmplayer.exe",
    "itunes":             r"%PROGRAMFILES%\\iTunes\iTunes.exe",
    "audacity":           r"%PROGRAMFILES%\\Audacity\Audacity.exe",

    # System / Utilities
    "file explorer":      "explorer.exe",
    "explorer":           "explorer.exe",
    "paint":              "mspaint.exe",
    "ms paint":           "mspaint.exe",
    "snipping tool":      "snippingtool.exe",
    "magnifier":          "magnify.exe",
    "control panel":      "control.exe",
    "settings":           "ms-settings:",        # URI scheme
    "windows settings":   "ms-settings:",
    "device manager":     "devmgmt.msc",
    "registry editor":    "regedit.exe",
    "task scheduler":     "taskschd.msc",
    "event viewer":       "eventvwr.msc",
    "disk management":    "diskmgmt.msc",

    # Gaming / Other
    "steam":              r"%PROGRAMFILES(X86)%\Steam\steam.exe",
    "epic games":         r"%LOCALAPPDATA%\\EpicGamesLauncher\\Portal\Binaries\Win64\\EpicGamesLauncher.exe",
    "obs":                r"%PROGRAMFILES%\\obs-studio\bin\\64bit\obs64.exe",
    "obs studio":         r"%PROGRAMFILES%\\obs-studio\bin\\64bit\obs64.exe",
    "blender":            r"%PROGRAMFILES%\\Blender Foundation\Blender 4.0\blender.exe",
    "adobe photoshop":    r"%PROGRAMFILES%\\Adobe\Adobe Photoshop 2024\Photoshop.exe",
    "photoshop":          r"%PROGRAMFILES%\\Adobe\Adobe Photoshop 2024\Photoshop.exe",
    "premiere":           r"%PROGRAMFILES%\\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe",
    "after effects":      r"%PROGRAMFILES%\\Adobe\Adobe After Effects 2024\Support Files\AfterFX.exe",
}


def _expand(path: str) -> str:
    return os.path.expandvars(path)


def _try_known(name: str) -> str | None:
    key = name.lower().strip()
    if key not in KNOWN_APPS:
        return None

    raw = KNOWN_APPS[key]
    parts  = raw.split(" --", 1)
    exe    = _expand(parts[0])
    args   = ("--" + parts[1]) if len(parts) > 1 else ""

    if os.path.exists(exe):
        return exe + (" " + args if args else "")

    alt = exe.replace("Program Files\\", "Program Files (x86)\\")
    if os.path.exists(alt):
        return alt + (" " + args if args else "")

    parent = os.path.dirname(exe)
    bname  = os.path.basename(exe)
    matches = glob.glob(os.path.join(
        os.path.dirname(parent), "**", bname), recursive=True)
    if matches:
        return matches[0]

    return None


def _try_start_menu(name: str) -> str | None:
    search_dirs = [
        os.path.join(os.getenv("APPDATA", ""),
                     r"Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]
    name_lower = name.lower()
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(".lnk") and name_lower in f.lower():
                    return os.path.join(root, f)
    return None


def _try_where(name: str) -> str | None:
    try:
        result = subprocess.run(
            ["where", name], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def _try_uri(name: str) -> bool:
    uri_map = {
        "settings":         "ms-settings:",
        "windows settings": "ms-settings:",
        "store":            "ms-windows-store:",
        "microsoft store":  "ms-windows-store:",
        "xbox":             "xbox:",
    }
    uri = uri_map.get(name.lower())
    if uri:
        os.startfile(uri)
        return True
    if ":" in name and not name.startswith("C:"):
        try:
            os.startfile(name)
            return True
        except Exception:
            pass
    return False


def launch_app(app_name: str) -> str:
    name = app_name.strip().lower()
    log(f"Launching app: '{name}'")

    if _try_uri(name):
        return f"Opened '{app_name}'."

    path = _try_known(name)
    if path:
        parts = path.split(" ", 1)
        try:
            if len(parts) > 1:
                subprocess.Popen(parts)
            else:
                subprocess.Popen([path])
            return f"Launched '{app_name}'."
        except Exception as e:
            log(f"Known-path launch failed: {e}", "WARN")

    lnk = _try_start_menu(name)
    if lnk:
        try:
            os.startfile(lnk)
            return f"Launched '{app_name}' from Start Menu."
        except Exception as e:
            log(f"Start Menu launch failed: {e}", "WARN")

    try:
        subprocess.Popen(
            ["explorer", f"shell:AppsFolder"],
            creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass

    exe = _try_where(name) or _try_where(name.replace(" ", ""))
    if exe:
        try:
            subprocess.Popen([exe])
            return f"Launched '{app_name}' from PATH."
        except Exception as e:
            log(f"PATH launch failed: {e}", "WARN")

    # 6. Last resort — pass to shell (sometimes works for .msc, URI, etc.)
    try:
        subprocess.Popen(name, shell=True)
        return f"Sent '{app_name}' to shell — check if it opened."
    except Exception as e:
        return (f"Could not find '{app_name}'. "
                f"Make sure it is installed, or say the exact app name.")
