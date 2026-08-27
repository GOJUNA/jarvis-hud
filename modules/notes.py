import time
from utils.helpers import load_json, save_json, generate_id
from utils.logger import log
import config


class NotesManager:
    """Verwaltet Notizen mit persistenter JSON-Speicherung."""

    def __init__(self):
        self.file = config.NOTES_FILE
        self.notes = load_json(self.file)
        if not isinstance(self.notes, list):
            self.notes = []

    def add_note(self, text: str) -> bool:
        """Fuegt eine neue Notiz hinzu."""
        try:
            note = {
                "id": generate_id(self.notes),
                "text": text.strip(),
                "created_at": time.time(),
            }
            self.notes.append(note)
            self._save()
            log.info(f"Notiz hinzugefuegt: {text}")
            return True
        except Exception as e:
            log.error(f"Fehler beim Hinzufuegen der Notiz: {e}")
            return False

    def list_notes(self) -> str:
        """Listet alle Notizen auf."""
        if not self.notes:
            return "Du hast keine Notizen."
        lines = ["Deine Notizen:"]
        for note in self.notes:
            lines.append(f"  #{note['id']}: {note['text']}")
        return "\n".join(lines)

    def delete_note(self, note_id: int) -> bool:
        """Loescht eine Notiz nach ID."""
        for i, note in enumerate(self.notes):
            if note["id"] == note_id:
                removed = self.notes.pop(i)
                self._save()
                log.info(f"Notiz geloescht: {removed['text']}")
                return True
        return False

    def get_all_notes(self) -> list[dict]:
        """Gibt alle Notizen zurueck."""
        return self.notes

    def _save(self) -> None:
        save_json(self.file, self.notes)
