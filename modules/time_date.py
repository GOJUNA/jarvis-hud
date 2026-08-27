from datetime import datetime
from utils.helpers import format_german_date


class TimeDateModule:
    """Bietet Zeit- und Datumsabfragen auf Deutsch."""

    def get_time(self) -> str:
        now = datetime.now()
        return f"Es ist {now.strftime('%H:%M')} Uhr."

    def get_date(self) -> str:
        now = datetime.now()
        return f"Heute ist {format_german_date(now)}."

    def get_datetime(self) -> str:
        now = datetime.now()
        return f"Jetzt ist es {now.strftime('%H:%M')} Uhr am {format_german_date(now)}."

    def get_greeting_by_time(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Guten Morgen!"
        elif 12 <= hour < 18:
            return "Guten Tag!"
        elif 18 <= hour < 22:
            return "Guten Abend!"
        else:
            return "Gute Nacht!"
