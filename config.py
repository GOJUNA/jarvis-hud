import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

TASKS_FILE = DATA_DIR / "tasks.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"
NOTES_FILE = DATA_DIR / "notes.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
MEMORY_FILE = DATA_DIR / "memory.json"

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "28bf91eee7a2f358959e2171da0a6ccb")
WEATHER_CITY = os.environ.get("WEATHER_CITY", "Amriswil")

VOICE_ENABLED = True
VOICE_RATE = 180
VOICE_INDEX = 0

REMINDER_CHECK_INTERVAL = 60

LOGGING_ENABLED = True
LOG_FILE = DATA_DIR / "jarvis.log"

GREETINGS = [
    "Hallo! Wie kann ich dir helfen?",
    "Hey! Was kann ich fuer dich tun?",
    "Willkommen zurueck! Wobei kann ich behilflich sein?",
    "Guten Tag! Ich bin bereit.",
]

FAREWELLS = [
    "Bis bald! Pass auf dich auf.",
    "Tschuess! Ich bin hier, wenn du mich brauchst.",
    "Bis zum naechsten Mal!",
]
 