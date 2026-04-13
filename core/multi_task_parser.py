import re
from core.logger import log

_SPLITTERS = re.compile(
    r'\b(?:and then|then|and also|also|after that|next|plus|,'
    r'|and open|and launch|and start|and check|and take|and set'
    r'|and search|and get|and show|and tell|and draft|and create)\b',
    re.IGNORECASE
)

_MIN_WORDS = 2


def split_commands(text: str) -> list[str]:
    text = text.strip().rstrip(".")

    parts = _SPLITTERS.split(text)

    commands = []
    for p in parts:
        p = p.strip(" ,.")
        if p and len(p.split()) >= _MIN_WORDS:
            commands.append(p)

    if not commands:
        return [text]

    if len(commands) > 1:
        log(f"[MultiTask] Split into {len(commands)} commands: {commands}")

    return commands


def is_multi_task(text: str) -> bool:
    return bool(_SPLITTERS.search(text)) and len(split_commands(text)) > 1
