import time
from pathlib import Path
from utils.helpers import load_json, save_json, generate_id, parse_german_date, format_german_date
from utils.logger import log
import config


class TaskManager:
    """Verwaltet Aufgaben mit persistenter JSON-Speicherung."""

    def __init__(self):
        self.file = config.TASKS_FILE
        self.tasks = load_json(self.file)
        if not isinstance(self.tasks, list):
            self.tasks = []

    def add_task(self, title: str, date_text: str = "", priority: str = "normal") -> bool:
        """Fuegt eine neue Aufgabe hinzu."""
        try:
            task = {
                "id": generate_id(self.tasks),
                "title": title.strip(),
                "date_text": date_text,
                "date_parsed": "",
                "priority": priority,
                "completed": False,
                "created_at": time.time(),
            }
            if date_text:
                parsed_date = parse_german_date(date_text)
                if parsed_date:
                    task["date_parsed"] = parsed_date.isoformat()

            self.tasks.append(task)
            self._save()
            log.info(f"Aufgabe hinzugefuegt: {title}")
            return True
        except Exception as e:
            log.error(f"Fehler beim Hinzufuegen der Aufgabe: {e}")
            return False

    def list_tasks(self, show_completed: bool = False) -> str:
        """Listet alle offenen (oder alle) Aufgaben auf."""
        filtered = self.tasks if show_completed else [t for t in self.tasks if not t["completed"]]
        if not filtered:
            return "Du hast keine offenen Aufgaben. Gut gemacht!"

        lines = ["Deine Aufgaben:"]
        for task in filtered:
            status = "[x]" if task["completed"] else "[ ]"
            date_info = f" ({task['date_text']})" if task["date_text"] else ""
            lines.append(f"  #{task['id']} {status} {task['title']}{date_info}")
        return "\n".join(lines)

    def delete_task(self, task_id: int) -> bool:
        """Loescht eine Aufgabe nach ID."""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                removed = self.tasks.pop(i)
                self._save()
                log.info(f"Aufgabe geloescht: {removed['title']}")
                return True
        return False

    def complete_task(self, task_id: int) -> bool:
        """Markiert eine Aufgabe als erledigt."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = True
                task["completed_at"] = time.time()
                self._save()
                log.info(f"Aufgabe erledigt: {task['title']}")
                return True
        return False

    def get_all_tasks(self) -> list[dict]:
        """Gibt alle Aufgaben zurueck."""
        return [t for t in self.tasks if not t["completed"]]

    def _save(self) -> None:
        save_json(self.file, self.tasks)
