import os, sys, platform, subprocess
import psutil
from core.logger import log
from core.speaker import speak


def open_browser():
    import webbrowser
    webbrowser.open("https://www.google.com")
    return "Opening your default browser."

def open_calculator():
    if platform.system() == "Windows":
        os.startfile("calc.exe")
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Calculator"])
    else:
        subprocess.Popen(["gnome-calculator"])
    return "Calculator opened."

def open_notepad():
    if platform.system() == "Windows":
        os.startfile("notepad.exe")
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "TextEdit"])
    else:
        subprocess.Popen(["gedit"])
    return "Text editor opened."

import os
import datetime
from PIL import ImageGrab

def take_screenshot():
    try:
        timestamp = datetime.datetime.now().strftime('%H%M%S')
        filename = f"alpha_shot_{timestamp}.png"
        
        desktop = os.path.join(os.path.expanduser("~"),"OneDrive","Desktop")
        path = os.path.join(desktop, filename)
        img = ImageGrab.grab()
        img.save(path)
        return f"Screenshot saved to Desktop as {filename}"
    
    except Exception as e:
        return f"Screenshot failed: {e}"

def shutdown_computer():
    log("Shutdown command issued", "WARN")
    if platform.system() == "Windows":
        os.system("shutdown /s /t 10")
    else:
        os.system("shutdown -h +1")
    return "Shutting down in 10 seconds. Cancel with 'shutdown -a' or abort command."

def restart_computer():
    log("Restart command issued", "WARN")
    if platform.system() == "Windows":
        os.system("shutdown /r /t 10")
    else:
        os.system("shutdown -r +1")
    return "Restarting in 10 seconds."

def lock_screen():
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.user32.LockWorkStation()
    elif platform.system() == "Darwin":
        os.system("pmset displaysleepnow")
    else:
        os.system("gnome-screensaver-command --lock")
    return "Screen locked."

def check_battery():
    bat = psutil.sensors_battery()
    if bat is None:
        return "No battery detected (desktop system)."
    status = "Charging" if bat.power_plugged else "Discharging"
    return f"Battery: {bat.percent:.0f}% — {status}."

def check_cpu():
    usage = psutil.cpu_percent(interval=1)
    cores = psutil.cpu_count()
    return f"CPU Usage: {usage}% across {cores} cores."

def check_memory():
    mem = psutil.virtual_memory()
    used_gb = mem.used / 1e9
    total_gb = mem.total / 1e9
    return f"RAM: {used_gb:.1f} GB used of {total_gb:.1f} GB ({mem.percent}%)."

def volume_up():
    if platform.system() == "Windows":
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            vol = min(volume.GetMasterVolumeLevelScalar() + 0.1, 1.0)
            volume.SetMasterVolumeLevelScalar(vol, None)
            return f"Volume up → {int(vol*100)}%"
        except Exception:
            return "[Mock] Volume increased."
    else:
        return "[Mock] Volume up (system command required)."

def volume_down():
    if platform.system() == "Windows":
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            vol = max(volume.GetMasterVolumeLevelScalar() - 0.1, 0.0)
            volume.SetMasterVolumeLevelScalar(vol, None)
            return f"Volume down → {int(vol*100)}%"
        except Exception:
            return "[Mock] Volume decreased."
    else:
        return "[Mock] Volume down (system command required)."

def mute():
    if platform.system() == "Windows":
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            vol = min(volume.GetMasterVolumeLevelScalar()*0, 1.0)
            volume.SetMasterVolumeLevelScalar(vol, None)
            return f"Volume muted → {int(vol*100)}%"
        except Exception:
            return "[Mock] Volume muted."
    else:
        return "[Mock] Volume muted (system command required)."

def sleep_pc():
    if platform.system() == "Windows":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif platform.system() == "Darwin":
        os.system("pmset sleepnow")
    return "Putting the PC to sleep."

def open_task_manager():
    if platform.system() == "Windows":
        subprocess.Popen(["taskmgr.exe"])
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Activity Monitor"])
    
    return "Opening Task Manager."

def check_disk():
    disk = psutil.disk_usage('/')
    return f"Disk: {disk.percent}% used ({disk.free // (2**30)} GB free of {disk.total // (2**30)} GB)."

def check_network():
    addrs = psutil.net_if_addrs()
    return f"Network active on {len(addrs)} interfaces. Connection: {'Online' if psutil.net_connections() else 'Offline'}."