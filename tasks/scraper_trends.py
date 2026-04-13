
import re
import requests
from bs4 import BeautifulSoup
from core.logger import log


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 15 


def _google_trends(geo: str = "IN") -> list[str]:

    url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("title")[1:16]  
        trends = []
        for item in items:
            title = item.get_text(strip=True)
            if title:
                trends.append(title)
        log(f"[Trends] Google Trends pulled {len(trends)} items (geo={geo})")
        return trends
    except Exception as e:
        log(f"[Trends] Google Trends failed: {e}", "WARN")
        return []


def _twitter_trends() -> list[str]:

    url = "https://twitter.com/explore/tabs/trending"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")

        trends = []

        for span in soup.find_all("span"):
            text = span.get_text(strip=True)
            if text.startswith("#") and len(text) > 2:
                if text not in trends:
                    trends.append(text)
            if len(trends) >= 15:
                break

        if not trends:
            for div in soup.find_all("div", {"data-testid": "trend"}):
                text = div.get_text(strip=True)
                if text:
                    trends.append(text[:50])
                if len(trends) >= 15:
                    break

        log(f"[Trends] Twitter pulled {len(trends)} items")
        return trends
    except Exception as e:
        log(f"[Trends] Twitter scrape failed: {e}", "WARN")
        return []

def get_trending(source: str = "google", geo: str = "IN") -> str:
    results = {}

    if source in ("google", "both"):
        g = _google_trends(geo)
        if g:
            results["Google Trends"] = g[:10]

    if source in ("twitter", "both"):
        t = _twitter_trends()
        if t:
            results["Twitter/X"] = t[:10]

    # Fallback: both failed, try Google with US geo
    if not results:
        g = _google_trends("US")
        if g:
            results["Google Trends (US)"] = g[:10]

    if not results:
        return ("Could not fetch trending topics right now. "
                "Check your internet connection.")

    lines = []
    for platform, items in results.items():
        lines.append(f"── {platform} ──")
        for i, item in enumerate(items, 1):
            lines.append(f"  {i:2}. {item}")
    return "\n".join(lines)