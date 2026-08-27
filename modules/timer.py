import re
import time
import threading
from utils.logger import log


class TimerModule:
    """Verwaltet Timer und Wecker im Hintergrund."""

    def __init__(self):
        self.active_timer: threading.Timer | None = None
        self.timer_end_time: float = 0.0

    def set_timer(self, duration_text: str) -> str:
        """Startet einen Timer mit der angegebenen Dauer."""
        self.cancel_timer()
        seconds = self._parse_duration(duration_text)
        if seconds <= 0:
            return "Die Timer-Dauer konnte nicht erkannt werden. Versuche z.B. '5 Minuten' oder '1 Stunde'."

        self.timer_end_time = time.time() + seconds
        self.active_timer = threading.Timer(seconds, self._timer_callback)
        self.active_timer.daemon = True
        self.active_timer.start()

        minutes = seconds // 60
        remaining_secs = seconds % 60
        if minutes > 0:
            time_str = f"{minutes} Minuten"
            if remaining_secs > 0:
                time_str += f" und {remaining_secs} Sekunden"
        else:
            time_str = f"{remaining_secs} Sekunden"

        log.info(f"Timer gestellt: {time_str}")
        return f"Timer gestellt fuer {time_str}. Ich melde mich!"

    def cancel_timer(self) -> str:
        """Bricht den aktiven Timer ab."""
        if self.active_timer and self.active_timer.is_alive():
            self.active_timer.cancel()
            self.active_timer = None
            self.timer_end_time = 0.0
            log.info("Timer abgebrochen.")
            return "Timer wurde abgebrochen."
        return "Kein aktiver Timer vorhanden."

    def get_remaining_time(self) -> str:
        """Gibt die verbleibende Zeit des aktiven Timers zurueck."""
        if not self.active_timer or not self.active_timer.is_alive():
            return "Kein aktiver Timer."
        remaining = max(0, self.timer_end_time - time.time())
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        return f"Noch {minutes} Minuten und {seconds} Sekunden."

    def _timer_callback(self):
        """Wird aufgerufen, wenn der Timer abgelaufen ist."""
        log.info("Timer abgelaufen!")
        self.active_timer = None
        self.timer_end_time = 0.0

    def _parse_duration(self, text: str) -> int:
        """Parst eine Dauer-Texteingabe in Sekunden."""
        text = text.lower().strip()
        total_seconds = 0

        hour_match = re.search(r"(\d+)\s*(stunde|std|hour|hr)", text)
        if hour_match:
            total_seconds += int(hour_match.group(1)) * 3600

        min_match = re.search(r"(\d+)\s*(minute|min|m)", text)
        if min_match:
            total_seconds += int(min_match.group(1)) * 60

        sec_match = re.search(r"(\d+)\s*(sekunde|sec|s)", text)
        if sec_match:
            total_seconds += int(sec_match.group(1))

        if total_seconds == 0:
            num_match = re.search(r"(\d+)", text)
            if num_match:
                total_seconds = int(num_match.group(1)) * 60

        return total_seconds

    def _timer_callback(self):
        """Benachrichtigung beim Timer-Ablauf."""
        print("\n" + "=" * 50)
        print("  TIMER ABGELAUFEN!")
        print("  Dein Timer ist fertig.")
        print("=" * 50 + "\n")
        log.info("Timer abgelaufen - Benachrichtigung ausgegeben.")
        self.active_timer = None
