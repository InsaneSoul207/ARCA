import webbrowser, urllib.parse, requests
from core.logger import log
import time
import pyautogui


def search_web(query=""):
    if not query:
        query = "ARCA AI"
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f'Searching Google for: "{query}"'

def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube."

def open_github():
    webbrowser.open("https://www.github.com")
    return "Opening GitHub."

def open_spotify():
    pyautogui.press('win')
    time.sleep(1)
    pyautogui.write('Spotify')
    time.sleep(2)
    pyautogui.press('enter')
    return "Opening Spotify."

def check_weather(city=""):
    try:
        city = city or "Delhi"
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
        r = requests.get(url, timeout=4)
        return r.text.strip() if r.status_code == 200 else f"Could not fetch weather for {city}."
    except Exception as e:
        return f"Weather check failed: {e}"

def get_news():
    webbrowser.open("https://news.google.com")
    return "Opening Google News for the latest headlines."