
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
    "DNT": "1",
}
TIMEOUT = 10

def _scrape_bbc() -> list[tuple[str, str]]:
    url = "https://www.bbc.com/news"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for tag in soup.find_all(attrs={"data-testid": "card-headline"}):
            text = tag.get_text(strip=True)
            if text and len(text) > 15:
                parent = tag.find_parent("a")
                href = parent["href"] if parent and parent.get("href") else ""
                if href and not href.startswith("http"):
                    href = "https://www.bbc.com" + href
                results.append((text, href))
            if len(results) >= 10:
                break

        # Fallback: h3 tags
        if not results:
            for h3 in soup.find_all("h3"):
                text = h3.get_text(strip=True)
                if len(text) > 20:
                    a = h3.find("a") or h3.find_parent("a")
                    href = a["href"] if a and a.get("href") else ""
                    if href and not href.startswith("http"):
                        href = "https://www.bbc.com" + href
                    results.append((text, href))
                if len(results) >= 10:
                    break

        log(f"[News] BBC: {len(results)} headlines")
      
        return results

    except Exception as e:
        log(f"[News] BBC failed: {e}", "WARN")
        return []


def _scrape_toi() -> list[tuple[str, str]]:
    url = "https://timesofindia.indiatimes.com"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        seen = set()

        for tag in soup.find_all(["h2", "h3", "h4"]):
            text = tag.get_text(strip=True)
            if len(text) < 20 or text in seen:
                continue
            seen.add(text)
            a = tag.find("a") or tag.find_parent("a")
            href = a["href"] if a and a.get("href") else ""
            if href and not href.startswith("http"):
                href = "https://timesofindia.indiatimes.com" + href
            results.append((text, href))
            if len(results) >= 10:
                break

        log(f"[News] TOI: {len(results)} headlines")

        return results

    except Exception as e:
        log(f"[News] TOI failed: {e}", "WARN")
        return []


def _scrape_reuters() -> list[tuple[str, str]]:
    url = "https://www.reuters.com"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        seen = set()

        for tag in soup.find_all(attrs={"data-testid": True}):
            testid = tag.get("data-testid", "")
            if "heading" in testid.lower() or "title" in testid.lower():
                text = tag.get_text(strip=True)
                if len(text) > 20 and text not in seen:
                    seen.add(text)
                    a = tag.find("a") or tag.find_parent("a")
                    href = a["href"] if a and a.get("href") else ""
                    if href and not href.startswith("http"):
                        href = "https://www.reuters.com" + href
                    results.append((text, href))
            if len(results) >= 10:
                break

        if not results:
            for h3 in soup.find_all("h3"):
                text = h3.get_text(strip=True)
                if len(text) > 20 and text not in seen:
                    seen.add(text)
                    a = h3.find("a") or h3.find_parent("a")
                    href = a["href"] if a and a.get("href") else ""
                    if href and not href.startswith("http"):
                        href = "https://www.reuters.com" + href
                    results.append((text, href))
                if len(results) >= 10:
                    break

        log(f"[News] Reuters: {len(results)} headlines")
        
        return results

    except Exception as e:
        log(f"[News] Reuters failed: {e}", "WARN")
        return []


_SCRAPERS = {
    "bbc":     (_scrape_bbc,     "BBC News"),
    "toi":     (_scrape_toi,     "Times of India"),
    "reuters": (_scrape_reuters, "Reuters"),
}

_KEYWORD_MAP = {
    "bbc":          "bbc",
    "british":      "bbc",
    "times of india":"toi",
    "toi":          "toi",
    "india":        "toi",
    "reuters":      "reuters",
    "international":"reuters",
    "world":        "reuters",
}


def _detect_source(raw: str) -> str:
    text = raw.lower()
    for kw, src in _KEYWORD_MAP.items():
        if kw in text:
            return src
    return "bbc"   # default



def get_news_headlines(raw: str = "") -> str:

    source_key = _detect_source(raw)
    scraper_fn, source_name = _SCRAPERS[source_key]

    headlines = scraper_fn()

    # Try fallbacks if primary fails
    if not headlines:
        for key, (fn, name) in _SCRAPERS.items():
            if key != source_key:
                headlines = fn()
                if headlines:
                    source_name = name + " (fallback)"
                    break

    if not headlines:
        return "Could not fetch news headlines right now. Check your internet connection."

    lines = [f"── {source_name}  —  Top Headlines ──"]
    for i, (title, url) in enumerate(headlines, 1):
        lines.append(f"  {i:2}. {title}")
        if url:
            lines.append(f"       {url[:70]}")
    return "\n".join(lines)