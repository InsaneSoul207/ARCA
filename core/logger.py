import datetime, os
from config import LOG_PATH

_history = []


def log(msg: str, level: str = "INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] [{level}] {msg}"
    _history.append(entry)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass 
    return entry


def get_history(n=100):
    return list(_history[-n:])