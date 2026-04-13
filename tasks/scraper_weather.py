
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
TIMEOUT = 10

DEFAULT_CITY = "Delhi"


def _wttr_quick(city: str) -> str:
    import urllib.parse
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
        r   = requests.get(url, timeout=5)
        return r.text.strip() if r.status_code == 200 else ""
    except Exception:
        return ""



def _wttr_json(city: str) -> dict | None:

    import urllib.parse, json
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        r   = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"[Weather] wttr JSON failed: {e}", "WARN")
        return None


def _parse_wttr_json(data: dict, mode: str = "current") -> str:
    try:
        cc  = data["current_condition"][0]
        loc = data["nearest_area"][0]
        city_name = loc["areaName"][0]["value"]
        country   = loc["country"][0]["value"]

        temp_c    = cc["temp_C"]
        feels_c   = cc["FeelsLikeC"]
        humidity  = cc["humidity"]
        wind_kmph = cc["windspeedKmph"]
        wind_dir  = cc["winddir16Point"]
        desc      = cc["weatherDesc"][0]["value"]
        uv        = cc.get("uvIndex", "N/A")
        visibility= cc.get("visibility", "N/A")
        precip    = cc.get("precipMM", "0")

        lines = []

        if mode in ("current", "hourly", "weekly"):
            lines += [
                f"── Current Weather: {city_name}, {country} ──",
                f"  Condition  : {desc}",
                f"  Temperature: {temp_c}°C  (feels like {feels_c}°C)",
                f"  Humidity   : {humidity}%",
                f"  Wind       : {wind_kmph} km/h {wind_dir}",
                f"  UV Index   : {uv}",
                f"  Visibility : {visibility} km",
                f"  Precip     : {precip} mm",
            ]

        if mode == "hourly":
            lines.append("")
            lines.append("── Hourly Forecast (next 8 slots) ──")
            weather = data.get("weather", [])
            if weather:
                today_hours = weather[0].get("hourly", [])
                for h in today_hours[:8]:
                    time_str = h["time"].zfill(4)
                    hh = time_str[:2]
                    mm = time_str[2:]
                    hdesc = h["weatherDesc"][0]["value"]
                    htmp  = h["tempC"]
                    hrain = h.get("chanceofrain", "0")
                    lines.append(
                        f"  {hh}:{mm}  {htmp:>3}°C  {hdesc:<25}  Rain: {hrain}%"
                    )

        if mode == "weekly":
            lines.append("")
            lines.append("── 5-Day Forecast ──")
            for day in data.get("weather", [])[:5]:
                date   = day["date"]
                maxc   = day["maxtempC"]
                minc   = day["mintempC"]
                ddesc  = day["hourly"][4]["weatherDesc"][0]["value"]
                rain   = day["hourly"][4].get("chanceofrain", "0")
                lines.append(
                    f"  {date}  High {maxc}°C / Low {minc}°C  "
                    f"{ddesc:<25}  Rain: {rain}%"
                )

        return "\n".join(lines)

    except (KeyError, IndexError) as e:
        log(f"[Weather] Parse error: {e}", "WARN")
        return ""


def _scrape_weather_com(city: str) -> str:

    import urllib.parse

    query = f"weather {city} today hourly"
    url   = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=en"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        lines = [f"── Weather for {city} (via Google) ──"]

        temp = soup.find("span", {"id": "wob_tm"})
        if temp:
            lines.append(f"  Temperature : {temp.text}°C")

        desc = soup.find("span", {"id": "wob_dc"})
        if desc:
            lines.append(f"  Condition   : {desc.text}")

        hum = soup.find("span", {"id": "wob_hm"})
        if hum:
            lines.append(f"  Humidity    : {hum.text}")

        wind = soup.find("span", {"id": "wob_ws"})
        if wind:
            lines.append(f"  Wind        : {wind.text}")

        prec = soup.find("span", {"id": "wob_pp"})
        if prec:
            lines.append(f"  Precip prob : {prec.text}")

        hourly_items = soup.find_all("div", {"class": "wob_df"})
        if hourly_items:
            lines.append("")
            lines.append("  Hourly:")
            for item in hourly_items[:8]:
                try:
                    time_el = item.find("div", {"class": "g3VIld"})
                    temp_el = item.find("span", {"class": "wob_t"})
                    time_t  = time_el.text.strip() if time_el else "?"
                    temp_t  = temp_el.text.strip() if temp_el else "?"
                    lines.append(f"    {time_t:<8} {temp_t}°C")
                except Exception:
                    continue

        if len(lines) > 1:
            log(f"[Weather] Google weather box scraped for {city}")
            return "\n".join(lines)

    except Exception as e:
        log(f"[Weather] Google weather scrape failed: {e}", "WARN")

    return ""


def _extract_city(raw: str) -> str:
    m = re.search(r"(?:weather\s+(?:in|for|at)|in|for)\s+([A-Za-z\s]+?)(?:\s+today|\s+now|\s+this\s+week|\s+hourly|$)",
                  raw, re.IGNORECASE)
    if m:
        city = m.group(1).strip()
        if len(city) > 1:
            return city
    return DEFAULT_CITY


def get_current_weather(raw: str = "") -> str:
    city = _extract_city(raw)
    data = _wttr_json(city)
    if data:
        result = _parse_wttr_json(data, mode="current")
        if result:
            return result
   
    quick = _wttr_quick(city)
    return quick or f"Could not fetch weather for {city}."


def get_hourly_weather(raw: str = "") -> str:
    city = _extract_city(raw)
    data = _wttr_json(city)
    if data:
        result = _parse_wttr_json(data, mode="hourly")
        if result:
            return result

    scraped = _scrape_weather_com(city)
    return scraped or f"Could not fetch hourly forecast for {city}."


def get_weekly_weather(raw: str = "") -> str:

    city = _extract_city(raw)
    data = _wttr_json(city)
    if data:
        result = _parse_wttr_json(data, mode="weekly")
        if result:
            return result
    return f"Could not fetch weekly forecast for {city}."