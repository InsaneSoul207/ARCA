import os, time, subprocess, re, ctypes
from pathlib import Path
from core.logger import log
import time


_KEYEVENTF_KEYDOWN = 0x0000
_KEYEVENTF_KEYUP   = 0x0002

VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP       = 0xB2
VK_VOLUME_UP        = 0xAF
VK_VOLUME_DOWN      = 0xAE
VK_VOLUME_MUTE      = 0xAD


def _press_media_key(vk_code: int) -> bool:
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, _KEYEVENTF_KEYDOWN, 0)
        time.sleep(0.05)
        user32.keybd_event(vk_code, 0, _KEYEVENTF_KEYUP,   0)
        log(f"[Spotify] Media key sent: 0x{vk_code:02X}")
        return True
    except Exception as e:
        log(f"[Spotify] Media key failed: {e}", "ERROR")
        return False


_SPOTIFY_PATHS = [
    Path(os.getenv("APPDATA",      "")) / "Spotify"  / "Spotify.exe",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "Spotify.exe",
]


def _find_spotify() -> Path | None:
    for p in _SPOTIFY_PATHS:
        if p.exists():
            return p
    import shutil
    found = shutil.which("spotify")
    return Path(found) if found else None


def _is_spotify_running() -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/fi", "imagename eq Spotify.exe"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "Spotify.exe" in r.stdout
    except Exception:
        return False


def open_spotify() -> str:
    if _is_spotify_running():
        return "Spotify is already running."

    path = _find_spotify()
    if path:
        try:
            subprocess.Popen([str(path)], creationflags=subprocess.DETACHED_PROCESS)
            log(f"[Spotify] Launched: {path}")
            return "Spotify launched."
        except Exception as e:
            time.sleep(2)
            log(f"[Spotify] Direct launch failed: {e}", "WARN")
    try:
        import pyautogui
        pyautogui.press("win");         time.sleep(0.6)
        pyautogui.write("Spotify", interval=0.05); time.sleep(0.8)
        pyautogui.press("enter");       time.sleep(3)
        return "Spotify launched via Start Menu."
    except ImportError:
        pass
    except Exception as e:
        log(f"[Spotify] Start Menu launch failed: {e}", "WARN")
    try:
        os.startfile("spotify:")
        time.sleep(2)
        return "Spotify opened."
    except Exception as e:
        return f"Could not open Spotify: {e}"


def play_pause() -> str:
    if not _is_spotify_running():
        result = open_spotify()
        time.sleep(2)

    if _press_media_key(VK_MEDIA_PLAY_PAUSE):
        return "Play/pause toggled."
    return "Media key failed. Is Spotify installed?"


def next_track() -> str:
    if not _is_spotify_running():
        return "Spotify is not running. Say 'open spotify' first."
    if _press_media_key(VK_MEDIA_NEXT_TRACK):
        return "Next track."
    return "Could not skip track."


def previous_track() -> str:
    if not _is_spotify_running():
        return "Spotify is not running."
    if _press_media_key(VK_MEDIA_PREV_TRACK):
        return "Previous track."
    return "Could not go back."


def stop_playback() -> str:
    if _press_media_key(VK_MEDIA_STOP):
        return "Spotify stopped."
    return "Could not stop playback."


def like_current_song() -> str:
    if not _is_spotify_running():
        return "Spotify is not running."
    try:
        import pyautogui
        try:
            import pygetwindow as gw
            wins = gw.getWindowsWithTitle("Spotify")
            if wins:
                wins[0].activate()
                time.sleep(0.3)
        except Exception:
            pass
        pyautogui.hotkey("alt", "shift", "b")
        return "Song liked."
    except ImportError:
        return "pyautogui not installed — run: pip install pyautogui"
    except Exception as e:
        return f"Could not like song: {e}"


def search_and_play(query: str) -> str:

    if not _is_spotify_running():
        open_spotify()
        time.sleep(3)

    try:
        import pyautogui

        # Bring Spotify to focus
        try:
            import pygetwindow as gw
            wins = gw.getWindowsWithTitle("Spotify")
            if wins:
                wins[0].activate()
                time.sleep(0.4)
        except Exception:
            pass

        pyautogui.hotkey("ctrl", "l")           # focus search bar
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "a")           # select all
        pyautogui.write(query, interval=0.04)
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.press("tab")
        time.sleep(1)
        pyautogui.press("tab")
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.press("enter")    
        time.sleep(1)
        pyautogui.hotkey('win', 'down')            
        return f"Playing {query}"
    except ImportError:
        return f"Spotify opened. Search manually for: {query}"
    except Exception as e:
        return f"Spotify search failed: {e}"


def spotify_status() -> str:
    path    = _find_spotify()
    running = _is_spotify_running()
    lines = [
        f"Spotify installed: {'Yes — ' + str(path) if path else 'Not found in known paths'}",
        f"Spotify running:   {'Yes' if running else 'No'}",
        f"Media keys:        ctypes (stdlib) — always available",
    ]
    try:
        import pyautogui
        lines.append("PyAutoGUI:         Available (used for search + like)")
    except ImportError:
        lines.append("PyAutoGUI:         Not installed (optional — pip install pyautogui)")
    return "\n".join(lines)


if __name__ == "__main__":
    search_and_play("chak de india")