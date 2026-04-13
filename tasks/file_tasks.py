import os, datetime, shutil
from core.logger import log

def create_file():
    path = os.path.join(os.path.expanduser("~"), "Desktop",
                        f"alpha_note_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(path, "w") as f:
        f.write(f"Created by Alpha 2.0 at {datetime.datetime.now()}\n")
    return f"File created on Desktop: {os.path.basename(path)}"

def list_files():
    folder = os.path.expanduser("~")
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))][:10]
    if not files:
        return "No files found in home directory."
    return "Files in home:\n" + "\n".join(f"  • {f}" for f in files)

def open_downloads():
    path = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(path):
        if os.name == "nt":
            os.startfile(path)
        elif os.uname().sysname == "Darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}'")

        return "Opened Downloads folder."
    return "Downloads folder not found."

def open_documents():
    path = os.path.join(os.path.expanduser("~"), "Documents")
    if os.path.exists(path):
        if os.name == "nt":
            os.startfile(path)
        else:
            os.system(f"xdg-open '{path}' 2>/dev/null || open '{path}'")
        return "Opened Documents folder."
    return "Documents folder not found."

def delete_file():
    return "[Mock] Specify a filename to delete. (Safety: no auto-delete without confirmation)"

def open_desktop():
    path = os.path.join(os.path.expanduser("~"), "Desktop")
    os.startfile(path) if os.name == "nt" else subprocess.Popen(["xdg-open", path])
    return "Opened Desktop."

def empty_recycle_bin():
    if os.name == "nt":
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
        return "Recycle Bin emptied."
    return "Feature only supported on Windows."