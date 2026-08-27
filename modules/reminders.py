import time
from utils.helpers import load_json, save_json, generate_id, parse_german_date, format_german_date
from utils.logger import log
from datetime import datetime
import config


class ReminderManager:
    """Verwaltet Erinnerungen mit Zeitplanung und persistenter Speicherung."""

    def __init__(self):
        self.file = config.REMINDERS_FILE
        self.reminders = load_json(self.file)
        if not isinstance(self.reminders, list):
            self.reminders = []

    def add_reminder(self, text: str, date_text: str = "") -> bool:
        """Fuegt eine neue Erinnerung hinzu."""
        try:
            reminder = {
                "id": generate_id(self.reminders),
                "text": text.strip(),
                "date_text": date_text,
                "date_parsed": "",
                "completed": False,
                "notified": False,
                "created_at": time.time(),
            }
            if date_text:
                parsed_date = parse_german_date(date_text)
                if parsed_date:
                    reminder["date_parsed"] = parsed_date.isoformat()

            self.reminders.append(reminder)
            self._save()
            log.info(f"Erinnerung hinzugefuegt: {text}")
            return True
        except Exception as e:
            log.error(f"Fehler beim Hinzufuegen der Erinnerung: {e}")
            return False

    def list_reminders(self) -> str:
        """Listet alle aktiven Erinnerungen auf."""
        active = [r for r in self.reminders if not r.get("completed")]
        if not active:
            return "Du hast keine offenen Erinnerungen."
        lines = ["Deine Erinnerungen:"]
        for r in active:
            date_info = f" am {r['date_text']}" if r["date_text"] else ""
            lines.append(f"  #{r['id']}: {r['text']}{date_info}")
        return "\n".join(lines)

    def delete_reminder(self, reminder_id: int) -> bool:
        """Loescht eine Erinnerung nach ID."""
        for i, reminder in enumerate(self.reminders):
            if reminder.get("id") == reminder_id:
                removed = self.reminders.pop(i)
                self._save()
                log.info(f"Erinnerung geloescht: {removed['text']}")
                return True
        return False

    def check_due_reminders(self) -> list[str]:
        """Prueft auf faellige Erinnerungen und gibt Benachrichtigungen zurueck."""
        now = datetime.now()
        notifications = []

        for reminder in self.reminders:
            if reminder.get("completed") or reminder.get("notified"):
                continue

            date_str = reminder.get("date_parsed", "")
            if not date_str:
                continue

            try:
                reminder_date = datetime.fromisoformat(date_str)
                if now.date() >= reminder_date.date():
                    notifications.append(
                        f"Erinnerung: {reminder['text']}"
                        + (f" ({reminder['date_text']})" if reminder["date_text"] else "")
                    )
                    reminder["notified"] = True
            except ValueError:
                continue

        if notifications:
            self._save()
        return notifications

    def get_all_reminders(self) -> list[dict]:
        """Gibt alle Erinnerungen zurueck."""
        return self.reminders

    def _save(self) -> None:
        save_json(self.file, self.reminders)
