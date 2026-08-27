import json
from pathlib import Path
from datetime import datetime, timedelta
from difflib import get_close_matches


def load_json(path: Path) -> list | dict:
    """Laedt eine JSON-Datei oder gibt eine leere Struktur zurueck."""
    if not path.exists():
        return [] if path.suffix == ".json" and "tasks" in path.name or "notes" in path.name else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return [] if "tasks" in path.name or "notes" in path.name else {}


def save_json(path: Path, data: list | dict) -> None:
    """Speichert Daten in eine JSON-Datei."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_german_date(text: str) -> datetime | None:
    """Parst deutsche Zeitangaben wie 'morgen', 'uebermorgen', 'naechsten montag'."""
    now = datetime.now()
    text = text.lower().strip()

    relative_days = {
        "heute": 0,
        "morgen": 1,
        "uebermorgen": 2,
        "gestern": -1,
        "vorgestern": -2,
    }
    if text in relative_days:
        return now + timedelta(days=relative_days[text])

    weekdays = {
        "montag": 0, "dienstag": 1, "mittwoch": 2,
        "donnerstag": 3, "freitag": 4, "samstag": 5, "sonntag": 6,
    }
    for day_name, day_num in weekdays.items():
        if day_name in text:
            days_ahead = (day_num - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            if "naechst" in text or "nachst" in text or "komme" in text:
                pass
            return now + timedelta(days=days_ahead)

    try:
        for fmt in ("%d.%m.%Y", "%d.%m.", "%Y-%m-%d", "%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    except Exception:
        pass

    return None


def fuzzy_match(query: str, choices: list[str], threshold: float = 0.6) -> str | None:
    """Findet den besten Fuzzy-Match fuer Tippfehler-Korrektur."""
    matches = get_close_matches(query.lower(), [c.lower() for c in choices], n=1, cutoff=threshold)
    if matches:
        for choice in choices:
            if choice.lower() == matches[0]:
                return choice
    return None


def generate_id(items: list[dict], key: str = "id") -> int:
    """Generiert eine eindeutige ID basierend auf vorhandenen Eintraegen."""
    if not items:
        return 1
    return max(item.get(key, 0) for item in items) + 1


def format_german_date(dt: datetime) -> str:
    """Formatiert ein Datum auf Deutsch."""
    weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return f"{weekdays[dt.weekday()]} {dt.strftime('%d.%m.%Y')}"
