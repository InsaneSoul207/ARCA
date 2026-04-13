import os, re, glob, time, subprocess
from pathlib import Path
from core.logger import log
from config import BASE_DIR
_cache: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 60

HOME = Path.home()
PRIORITY_DIRS = [
    HOME / "Desktop",
    HOME / "Documents",
    HOME / "Downloads",
    HOME / "OneDrive",
    HOME / "OneDrive" / "Desktop",
    HOME / "OneDrive" / "Documents",
    HOME / "Pictures",
    HOME / "Videos",
    HOME / "Music",
    Path(os.getenv("USERPROFILE", str(HOME))),
]
PRIORITY_DIRS = [d for d in PRIORITY_DIRS if d.exists()]

EXT_GROUPS = {
    "pdf":      [".pdf"],
    "word":     [".docx", ".doc"],
    "excel":    [".xlsx", ".xls", ".csv"],
    "powerpoint": [".pptx", ".ppt"],
    "image":    [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "video":    [".mp4", ".mov", ".avi", ".mkv"],
    "audio":    [".mp3", ".wav", ".flac", ".aac"],
    "python":   [".py"],
    "text":     [".txt", ".md", ".log"],
    "zip":      [".zip", ".rar", ".7z"],
    "code":     [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c"],
}



def _parse_query(raw: str) -> tuple[str, list[str] | None]:
    """
    Extract (search_term, extensions) from voice command.
    Returns (term, None) if no extension filter detected.
    """
    text = raw.lower()

    extensions = None
    for group, exts in EXT_GROUPS.items():
        if group in text:
            extensions = exts
            break
    ext_match = re.search(r"\.(py|txt|pdf|docx|xlsx|csv|jpg|png|mp4|mp3|zip)\b", text)
    if ext_match:
        extensions = ["." + ext_match.group(1)]

    term = text
    for phrase in ["find the", "find my", "find all", "find",
                   "search for", "search", "locate", "look for",
                   "open my", "open the", "open",
                   "pdf", "word", "excel", "python", "text", "image",
                   "files", "file", "document", "folder"]:
        term = re.sub(r"\b" + re.escape(phrase) + r"\b", " ", term, flags=re.IGNORECASE)
    term = re.sub(r"\s+", " ", term).strip(" .,?")

    term = re.sub(r"\b(from the|from my|in the|in my|on the|on my|of the|of my)\b.*$",
                  "", term, flags=re.IGNORECASE).strip()
    term = re.sub(r"^(the|a|an|my|this|that|these|those)\s+", "", term, flags=re.IGNORECASE)

    return term, extensions



def _search_in_dirs(term: str, dirs: list[Path],
                    extensions: list[str] | None = None,
                    max_results: int = 20,
                    max_depth: int = 5) -> list[Path]:
    results  = []
    term_low = term.lower()

    for base_dir in dirs:
        if not base_dir.exists():
            continue
        try:
            for root, subdirs, files in os.walk(str(base_dir)):
                depth = len(Path(root).parts) - len(base_dir.parts)
                if depth >= max_depth:
                    subdirs.clear()
                    continue

                subdirs[:] = [d for d in subdirs
                               if not d.startswith(".") and
                               d not in ("__pycache__", "node_modules",
                                         "$RECYCLE.BIN", "System Volume Information")]

                for fname in files:
                    fname_low = fname.lower()
                    stem      = Path(fname).stem.lower()
                    ext       = Path(fname).suffix.lower()

                    if extensions and ext not in extensions:
                        continue

                    if term_low in fname_low or term_low in stem:
                        results.append(Path(root) / fname)
                        if len(results) >= max_results:
                            return results
        except PermissionError:
            continue

    return results


def _sort_by_recency(paths: list[Path]) -> list[Path]:
    def mtime(p):
        try:
            return p.stat().st_mtime
        except Exception:
            return 0
    return sorted(paths, key=mtime, reverse=True)



def search_files(raw: str) -> str:
    term, extensions = _parse_query(raw)

    if not term and not extensions:
        return "What file are you looking for? Try: 'find my resume pdf'"

    cache_key = f"{term}|{extensions}"
    if cache_key in _cache:
        ts, cached = _cache[cache_key]
        if time.time() - ts < _CACHE_TTL:
            results = cached
        else:
            results = None
    else:
        results = None

    if results is None:
        log(f"[FileSearch] Searching for: '{term}' ext={extensions}")
        results = _search_in_dirs(term, PRIORITY_DIRS, extensions,
                                   max_results=15, max_depth=5)

        if len(results) < 3:
            extra_dirs = [Path("C:\\")]
            deep = _search_in_dirs(term, extra_dirs, extensions,
                                    max_results=15 - len(results), max_depth=8)
            results.extend(deep)

        results = _sort_by_recency(list(dict.fromkeys(results)))  
        _cache[cache_key] = (time.time(), results)

    if not results:
        msg = f"No files found matching '{term}'"
        if extensions:
            msg += f" (type: {'/'.join(extensions)})"
        return msg

    lines = [f"── Found {len(results)} file{'s' if len(results)>1 else ''} ──"]
    for i, path in enumerate(results[:10], 1):
        try:
            size  = path.stat().st_size
            size_s = f"{size//1024}KB" if size < 1_000_000 else f"{size//1_048_576}MB"
            mtime = time.strftime("%d %b %Y", time.localtime(path.stat().st_mtime))
        except Exception:
            size_s = "?"; mtime = "?"
        lines.append(f"  [{i}] {path.name:<40} {size_s:<8} {mtime}")
        lines.append(f"       {str(path)}")

    if len(results) > 10:
        lines.append(f"  ... and {len(results)-10} more")
    return "\n".join(lines)


def open_file(raw: str) -> str:
    term, extensions = _parse_query(raw)

    if not term and not extensions:
        return "Which file should I open? Try: 'open my resume pdf'"

    results = _search_in_dirs(term, PRIORITY_DIRS, extensions, max_results=5)
    if not results:
        results = _search_in_dirs(term, [Path("C:\\")], extensions,
                                   max_results=5, max_depth=6)

    if not results:
        import subprocess as _sp
        for base in PRIORITY_DIRS:
            if not base.exists(): continue
            for item in base.iterdir():
                if item.is_dir() and term.lower() in item.name.lower():
                    _sp.Popen(f'explorer "{item}"')
                    return f"Opened folder: {item.name}"
        return f"Could not find a file or folder matching '{term}'."

    results = _sort_by_recency(results)
    target  = results[0]

    try:
        if target.is_dir():
            import subprocess as _sp
            _sp.Popen(f'explorer "{target}"')
            log(f"[FileSearch] Opened folder: {target}")
            return f"Opened folder: {target.name}"
        else:
            os.startfile(str(target))
            log(f"[FileSearch] Opened: {target}")
            return f"Opened: {target.name}\n  Path: {target.parent}"
    except Exception as e:
        log(f"[FileSearch] Open error: {e}", "ERROR")
        return f"Found '{target.name}' but could not open it: {e}"


def open_folder(raw: str) -> str:
    text = raw.lower()

    folder_map = {
        "desktop":   HOME / "Desktop",
        "documents": HOME / "Documents",
        "downloads": HOME / "Downloads",
        "pictures":  HOME / "Pictures",
        "videos":    HOME / "Videos",
        "music":     HOME / "Music",
        "onedrive":  HOME / "OneDrive",
        "home":      HOME,
        "project":   BASE_DIR,
        "alpha":     BASE_DIR,
    }

    for key, path in folder_map.items():
        if key in text:
            if path.exists():
                subprocess.Popen(f'explorer "{path}"')
                return f"Opened folder: {path.name}"
            return f"Folder not found: {path}"

    # Try to find a folder by name
    term = re.sub(r"\b(open|folder|directory|go to|show me)\b", " ", text).strip()
    if term:
        for base in PRIORITY_DIRS:
            for item in base.iterdir() if base.exists() else []:
                if item.is_dir() and term.lower() in item.name.lower():
                    subprocess.Popen(f'explorer "{item}"')
                    return f"Opened folder: {item}"
    return f"Could not find folder matching '{raw}'"


def find_recent_files(ext: str = "", n: int = 10) -> str:
    extensions = EXT_GROUPS.get(ext.lower(), None)
    results    = _search_in_dirs("", PRIORITY_DIRS, extensions,
                                  max_results=50, max_depth=4)
    results    = _sort_by_recency(results)[:n]

    if not results:
        return "No recent files found."

    lines = [f"── {n} Most Recent Files ──"]
    for path in results:
        try:
            mtime = time.strftime("%d %b %Y %H:%M",
                                   time.localtime(path.stat().st_mtime))
        except Exception:
            mtime = "?"
        lines.append(f"  {mtime}  {path.name}")
        lines.append(f"           {path.parent}")
    return "\n".join(lines)