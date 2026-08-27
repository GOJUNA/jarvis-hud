import time
from pathlib import Path
from utils.helpers import load_json, save_json
from utils.logger import log
import config


class Memory:
    """Verwaltet Konversationsverlauf, Praeferenzen und gelernte Muster."""

    def __init__(self):
        self.data = load_json(config.MEMORY_FILE)
        if not isinstance(self.data, dict):
            self.data = {
                "conversation_history": [],
                "user_preferences": {},
                "learned_patterns": [],
            }
        self._ensure_structure()

    def _ensure_structure(self):
        """Stellt sicher, dass allenoetigen Schluessel vorhanden sind."""
        self.data.setdefault("conversation_history", [])
        self.data.setdefault("user_preferences", {})
        self.data.setdefault("learned_patterns", [])

    def add_message(self, role: str, text: str, intent: str = "") -> None:
        """Speichert eine Nachricht im Verlauf."""
        entry = {
            "role": role,
            "text": text,
            "intent": intent,
            "timestamp": time.time(),
        }
        self.data["conversation_history"].append(entry)
        if len(self.data["conversation_history"]) > 100:
            self.data["conversation_history"] = self.data["conversation_history"][-100:]
        self._save()

    def get_recent_messages(self, count: int = 5) -> list[dict]:
        """Gibt die letzten N Nachrichten zurueck."""
        return self.data["conversation_history"][-count:]

    def set_preference(self, key: str, value: str) -> None:
        """Speichert eine Benutzer-Praeferenz."""
        self.data["user_preferences"][key] = value
        self._save()
        log.info(f"Praeferenz gespeichert: {key} = {value}")

    def get_preference(self, key: str, default: str = "") -> str:
        """Gibt eine Benutzer-Praeferenz zurueck."""
        return self.data["user_preferences"].get(key, default)

    def add_learned_pattern(self, trigger: str, response: str) -> None:
        """Speichert ein gelerntes Muster (fuer Proaktivitaet)."""
        pattern = {
            "trigger": trigger,
            "response": response,
            "use_count": 0,
            "last_used": time.time(),
        }
        existing = next(
            (p for p in self.data["learned_patterns"] if p["trigger"] == trigger),
            None,
        )
        if existing:
            existing["use_count"] += 1
            existing["last_used"] = time.time()
        else:
            self.data["learned_patterns"].append(pattern)
        self._save()

    def get_learned_patterns(self) -> list[dict]:
        """Gibt alle gelernten Muster zurueck."""
        return self.data["learned_patterns"]

    def get_username(self) -> str:
        """Gibt den gespeicherten Benutzernamen zurueck."""
        return self.get_preference("username", "")

    def save(self) -> None:
        """Speichert den aktuellen Zustand."""
        self._save()

    def _save(self) -> None:
        save_json(config.MEMORY_FILE, self.data)
