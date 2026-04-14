import threading, time, subprocess, datetime
from core.logger import log

INTERVAL_BATTERY  = 120    
INTERVAL_RAM      = 60     
INTERVAL_CPU      = 30    
INTERVAL_CALENDAR = 60    
INTERVAL_REMINDER = 30     

BATTERY_WARN      = 20  
BATTERY_CRITICAL  = 10     
RAM_WARN          = 90    
CPU_WARN          = 90     
DISK_WARN         = 5     
CALENDAR_AHEAD    = 10     


class ProactiveMonitor:
    def __init__(self, speak_cb=None, log_cb=None):
        self._speak = speak_cb or (lambda t: None)
        self._log   = log_cb   or (lambda t, c="": log(t))
        self._running = False
        self._threads = []

        self._alerted: dict[str, float] = {}
        self._alert_cooldown = 300          

    def start(self):
        self._running = True
        monitors = [
            ("battery",  self._monitor_battery,  INTERVAL_BATTERY),
            ("ram",      self._monitor_ram,       INTERVAL_RAM),
            ("cpu",      self._monitor_cpu,       INTERVAL_CPU),
            ("disk",     self._monitor_disk,      INTERVAL_BATTERY),
            ("calendar", self._monitor_calendar,  INTERVAL_CALENDAR),
        ]
        for name, fn, interval in monitors:
            t = threading.Thread(
                target=self._run_loop,
                args=(fn, interval, name),
                daemon=True,
                name=f"ProactiveMonitor_{name}"
            )
            self._threads.append(t)
            t.start()
        log("[Proactive] Background monitoring started.")

    def stop(self):
        self._running = False
        log("[Proactive] Monitoring stopped.")

    def _run_loop(self, fn, interval, name):
        time.sleep(5)   # brief startup delay
        while self._running:
            try:
                fn()
            except Exception as e:
                log(f"[Proactive/{name}] Error: {e}", "WARN")
            for _ in range(interval * 2):   # sleep in small chunks for fast stop
                if not self._running:
                    return
                time.sleep(0.5)

    def _can_alert(self, key: str) -> bool:
        now = time.time()
        last = self._alerted.get(key, 0)
        if now - last > self._alert_cooldown:
            self._alerted[key] = now
            return True
        return False

    def _alert(self, key: str, message: str, speak: str = "",
               color: str = "#FFB800", toast: bool = True):
        if not self._can_alert(key):
            return
        self._log(f"[⚡ Alert] {message}", color)
        if speak:
            self._speak(speak)
        if toast:
            self._toast(message)
        log(f"[Proactive] ALERT: {message}")

    def _toast(self, message: str):
        safe_msg = message.replace('"', "'")
        ps = (
            f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
            f'ContentType = WindowsRuntime] > $null; '
            f'$t = [Windows.UI.Notifications.ToastTemplateType]::ToastText01; '
            f'$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($t); '
            f'$xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode("{safe_msg}")); '
            f'$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); '
            f'[Windows.UI.Notifications.ToastNotificationManager]::'
            f'CreateToastNotifier("ARCA").Show($toast)'
        )
        try:
            subprocess.Popen(
                ["powershell", "-Command", ps],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass

    def _monitor_battery(self):
        import psutil
        bat = psutil.sensors_battery()
        if bat is None or bat.power_plugged:
            return

        pct = bat.percent
        if pct <= BATTERY_CRITICAL:
            self._alert(
                "battery_critical",
                f"⚡ CRITICAL: Battery at {pct:.0f}% — plug in now!",
                speak=f"Critical battery alert. Battery is at {pct:.0f} percent. Please plug in immediately.",
                color="#FF3B5C"
            )
        elif pct <= BATTERY_WARN:
            self._alert(
                "battery_warn",
                f"🔋 Battery low: {pct:.0f}% remaining",
                speak=f"Battery warning. {pct:.0f} percent remaining. Consider plugging in.",
                color="#FFB800"
            )

    def _monitor_ram(self):
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent >= RAM_WARN:
            used = mem.used / 1e9
            self._alert(
                "ram_high",
                f"⚠ RAM usage high: {mem.percent:.0f}% ({used:.1f} GB used)",
                speak=f"RAM usage is at {mem.percent:.0f} percent. You may want to close some applications.",
                color="#FFB800"
            )

    def _monitor_cpu(self):
        import psutil
        usage = psutil.cpu_percent(interval=2)
        if usage >= CPU_WARN:
            time.sleep(10)
            usage2 = psutil.cpu_percent(interval=2)
            if usage2 >= CPU_WARN:   # sustained high CPU
                self._alert(
                    "cpu_high",
                    f"⚠ CPU usage sustained at {usage2:.0f}%",
                    speak=f"CPU usage is sustained at {usage2:.0f} percent.",
                    color="#FFB800"
                )

    def _monitor_disk(self):
        import psutil
        try:
            disk  = psutil.disk_usage("C:\\")
            free_pct = 100 - disk.percent
            if free_pct < DISK_WARN:
                free_gb = disk.free / 1e9
                self._alert(
                    "disk_critical",
                    f"💾 C:\\ almost full: only {free_gb:.1f} GB free ({free_pct:.0f}%)",
                    speak=f"Disk space warning. Only {free_gb:.1f} gigabytes free on your C drive.",
                    color="#FF3B5C"
                )
        except Exception:
            pass

    def _monitor_calendar(self):
        try:
            from tasks.calendar_tasks import _get_service
            import datetime as dt_mod
            import os
            from config import TOKEN_PATH

            # Skip if not authenticated
            if not os.path.exists(TOKEN_PATH):
                return

            svc  = _get_service()
            now  = dt_mod.datetime.utcnow()
            soon = now + dt_mod.timedelta(minutes=CALENDAR_AHEAD)

            result = svc.events().list(
                calendarId="primary",
                timeMin=now.isoformat() + "Z",
                timeMax=soon.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
                maxResults=5
            ).execute()

            events = result.get("items", [])
            for event in events:
                event_id  = event["id"]
                title     = event.get("summary", "Unnamed event")
                start_str = event["start"].get("dateTime", "")
                if not start_str:
                    continue

                start_dt = dt_mod.datetime.fromisoformat(start_str.replace("Z",""))
                mins_away = int((start_dt - dt_mod.datetime.now()).total_seconds() / 60)

                if 0 < mins_away <= CALENDAR_AHEAD:
                    self._alert(
                        f"calendar_{event_id}",
                        f"📅 Upcoming: '{title}' starts in {mins_away} minutes",
                        speak=f"Reminder. You have {title} starting in {mins_away} minutes.",
                        color="#00C9FF"
                    )

        except Exception:
            pass   
_monitor: ProactiveMonitor | None = None


def get_monitor() -> ProactiveMonitor | None:
    return _monitor


def start_monitoring(speak_cb=None, log_cb=None) -> str:
    global _monitor
    if _monitor and _monitor._running:
        return "Proactive monitoring is already running."
    _monitor = ProactiveMonitor(speak_cb=speak_cb, log_cb=log_cb)
    _monitor.start()
    return "Proactive monitoring started — I will alert you about battery, RAM, calendar and disk space."


def stop_monitoring() -> str:
    global _monitor
    if _monitor:
        _monitor.stop()
        _monitor = None
    return "Proactive monitoring stopped."


def monitoring_status() -> str:
    global _monitor
    if _monitor and _monitor._running:
        thresholds = [
            f"Battery warn: {BATTERY_WARN}% / critical: {BATTERY_CRITICAL}%",
            f"RAM warn: {RAM_WARN}%",
            f"CPU warn: {CPU_WARN}%",
            f"Disk free warn: {DISK_WARN}%",
            f"Calendar alert: {CALENDAR_AHEAD} min ahead",
        ]
        return "Proactive monitoring: ACTIVE\n" + "\n".join(f"  · {t}" for t in thresholds)
    return "Proactive monitoring: stopped. Say 'start monitoring' to activate."