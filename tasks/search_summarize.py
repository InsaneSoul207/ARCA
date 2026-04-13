
import re
import requests
from bs4 import BeautifulSoup
from core.logger import log

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
}
TIMEOUT       = 8
OLLAMA_URL    = "http://localhost:11434/api/generate"
OLLAMA_MODEL  = "llama3"
MAX_CHARS     = 3000

def _google_search_urls(query: str, n: int = 5) -> list[tuple[str, str]]:
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={n+5}"
    
    try:
        session = requests.Session()
        r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if r.status_code != 200:
            log(f"[Search] Google returned status {r.status_code}. You might be rate-limited.", "WARN")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        results = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if href.startswith("/url?q="):
                real_url = href.split("/url?q=")[1].split("&")[0]
                real_url = urllib.parse.unquote(real_url)
            elif href.startswith("http"):
                real_url = href
            else:
                continue

            if "google.com" in real_url or "accounts.google.com" in real_url:
                continue

            title_tag = a.find("h3")
            title = title_tag.get_text() if title_tag else a.get_text()
            title = title.strip()[:80]

            if real_url not in [r[0] for r in results] and title:
                results.append((real_url, title))

            if len(results) >= n:
                break

        log(f"[Search] Found {len(results)} URLs for: {query}")
        return results

    except Exception as e:
        log(f"[Search] Scraping failed: {e}", "WARN")
        return []
    
from duckduckgo_search import DDGS
from ddgs import DDGS
def _ddg_search_urls(query: str, n: int = 5) -> list[tuple[str, str]]:
    results = []
    skip = {"youtube.com", "twitter.com", "x.com", "facebook.com", 
            "instagram.com", "tiktok.com", "reddit.com"}
    
    try:
        with DDGS() as ddgs:
            ddg_gen = ddgs.text(query, region='wt-wt', safesearch='moderate', timelimit='y')
            
            for r in ddg_gen:
                href = r.get('href')
                title = r.get('title', 'No Title')
                
                domain = href.split("//")[-1].split("/")[0]
                if not any(s in domain for s in skip):
                    results.append((href, title))
                
                if len(results) >= n:
                    break
        
        log(f"[DDG Search] Found {len(results)} URLs for: {query}")
        return results

    except Exception as e:
        log(f"[DDG Search] Failed: {e}", "WARN")
        return []

def _fetch_page_text(url: str) -> str:
    try:
        r    = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "noscript", "svg", "img"]):
            tag.decompose()

        main = (soup.find("article") or soup.find("main")
                or soup.find("div", {"id": "content"})
                or soup.find("div", {"class": re.compile(r"content|article|post|body", re.I)})
                or soup.body)

        if main:
            text = main.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        text = re.sub(r"\s{2,}", " ", text).strip()
        return text[:MAX_CHARS]

    except Exception as e:
        log(f"[Search] Page fetch failed ({url[:50]}): {e}", "WARN")
        return ""



def _ollama_summarize(query: str, context: str) -> str:
    prompt = f"""You are a helpful assistant. The user searched for: "{query}"

Here is content scraped from the top web results:
---
{context}
---

Write a concise, clear summary (3-5 sentences) answering the query. 
Speak directly, use plain language. Do not mention that you scraped websites.
Answer as if you know this information."""

    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 300,
        }
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=30)
        r.raise_for_status()
        response = r.json().get("response", "").strip()
        log(f"[Ollama] Summary generated ({len(response)} chars)")
        return response
    except requests.ConnectionError:
        return ""   # Ollama not running — caller handles fallback
    except Exception as e:
        log(f"[Ollama] Error: {e}", "WARN")
        return ""



def _snippet_fallback(query: str, pages: list[tuple[str, str, str]]) -> str:
    """Return first 2-3 sentences from each scraped page."""
    lines = [f"── Search results for: {query} ──",
             "  (Ollama not running — showing raw snippets)\n"]
    for i, (url, title, text) in enumerate(pages[:3], 1):
        if text:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            snippet   = " ".join(sentences[:3])
            lines.append(f"  [{i}] {title[:60]}")
            lines.append(f"      {snippet[:200]}")
            lines.append(f"      {url[:70]}\n")
    return "\n".join(lines) if len(lines) > 2 else f"No results found for: {query}"


def _extract_query(raw: str) -> str:
    patterns = [
        # Added "search the web for" and "look up" more cleanly
        r"(?:search the web for|search for|look up)\s+(.+)",
        r"(?:search and summarize|summarize search results for|research and summarize)\s+(.+)",
        r"(?:give me a summary of|summarize)\s+(.+)",
        r"(?:research|search|for|web|search for|look up)\s+(.+?)\s+and\s+summarize",
    ]
    for p in patterns:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return raw.strip()


def search_and_summarize(raw: str) -> str:
    query = _extract_query(raw)
    if not query:
        return "What would you like me to search and summarize?"

    log(f"[Search+Summarize] Query: {query}")
    urls = _ddg_search_urls(query, n=5)
    if not urls:
        return f"Could not find search results for: {query}"

    pages = []
    for url, title in urls[:4]:
        text = _fetch_page_text(url)
        if text and len(text) > 100:
            pages.append((url, title, text))
        if len(pages) >= 3:
            break

    if not pages:
        return f"Found URLs but could not extract content for: {query}"

    context_parts = []
    for url, title, text in pages:
        context_parts.append(f"Source: {title}\n{text[:1500]}")
    combined_context = "\n\n".join(context_parts)

    summary = _ollama_summarize(query, combined_context)

    if summary:
        sources = "\n".join(f"  • {t[:60]}  ({u[:50]})"
                            for u, t, _ in pages[:3])
        return f"{summary}\n\nSources:\n{sources}"
    else:
        return _snippet_fallback(query, pages)


def ollama_status() -> str:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        if models:
            return f"Ollama: running  |  Models: {', '.join(models)}"
        return "Ollama: running but no models pulled. Run: ollama pull llama3"
    except Exception:
        return (
            "Ollama: not running.\n"
            "  1. Download from https://ollama.com\n"
            "  2. Run: ollama pull llama3\n"
            "  3. Keep Ollama running in the background"
        )