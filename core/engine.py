import random
import os
import config
from core.nlp import NLPEngine, ParsedCommand
from core.intent import Intent
from core.memory import Memory
from modules.tasks import TaskManager
from modules.time_date import TimeDateModule
from modules.notes import NotesManager
from modules.weather import WeatherModule
from modules.calculator import CalculatorModule
from modules.timer import TimerModule
from modules.reminders import ReminderManager
from modules.web_search import WebSearch
from modules.cameras import CameraManager
from utils.logger import log

# Optional import for presentations
try:
    from modules.presentation import PresentationManager
    HAS_PRESENTATION = True
except ImportError:
    PresentationManager = None
    HAS_PRESENTATION = False


class JarvisEngine:
    """Haupt-Engine von JARVIS - orchestriert alle Module."""

    def __init__(self):
        log.info("JARVIS Engine wird initialisiert...")
        self.nlp = NLPEngine()
        self.memory = Memory()
        self.tasks = TaskManager()
        self.time_date = TimeDateModule()
        self.notes = NotesManager()
        self.weather = WeatherModule()
        self.calculator = CalculatorModule()
        self.timer = TimerModule()
        self.reminders = ReminderManager()
        self.web_search = WebSearch()
        self.cameras = CameraManager()
        self.presentations = PresentationManager() if HAS_PRESENTATION else None
        self.running = True
        self.voice_enabled = config.VOICE_ENABLED
        log.info("JARVIS Engine bereit.")

    def process(self, user_input: str) -> str:
        """Verarbeitet eine Benutzereingabe und gibt eine Antwort zurueck."""
        if not user_input.strip():
            return ""

        parsed = self.nlp.parse(user_input)
        self.memory.add_message("user", user_input, parsed.intent.name)
        log.info(f"Intent: {parsed.intent.name} (Confidence: {parsed.confidence:.2f}) | Entities: {parsed.entities}")

        response = self._route(parsed)
        self.memory.add_message("jarvis", response, parsed.intent.name)
        return response

    def _route(self, parsed: ParsedCommand) -> str:
        """Leitet den Befehl an das richtige Modul weiter."""
        handlers = {
            Intent.GREETING: self._handle_greeting,
            Intent.FAREWELL: self._handle_farewell,
            Intent.TIME: lambda p: self.time_date.get_time(),
            Intent.DATE: lambda p: self.time_date.get_date(),
            Intent.DATETIME: lambda p: self.time_date.get_datetime(),
            Intent.TASK_ADD: self._handle_task_add,
            Intent.TASK_LIST: lambda p: self.tasks.list_tasks(),
            Intent.TASK_DELETE: self._handle_task_delete,
            Intent.TASK_COMPLETE: self._handle_task_complete,
            Intent.NOTE_ADD: self._handle_note_add,
            Intent.NOTE_LIST: lambda p: self.notes.list_notes(),
            Intent.NOTE_DELETE: self._handle_note_delete,
            Intent.WEATHER: lambda p: self.weather.get_weather(),
            Intent.CALCULATE: self._handle_calculate,
            Intent.TIMER_SET: self._handle_timer_set,
            Intent.TIMER_CANCEL: self._handle_timer_cancel,
            Intent.REMINDER_ADD: self._handle_reminder_add,
            Intent.REMINDER_LIST: lambda p: self.reminders.list_reminders(),
            Intent.REMINDER_DELETE: self._handle_reminder_delete,
            Intent.HELP: lambda p: self._handle_help(),
            Intent.SETTINGS: self._handle_settings,
            Intent.WEB_SEARCH: self._handle_web_search,
            Intent.CAMERA_SHOW: self._handle_camera_show,
            Intent.CAMERA_LIST: self._handle_camera_list,
            Intent.CAMERA_ADD: self._handle_camera_add,
            Intent.RESTAURANT: self._handle_restaurant,
            Intent.EARN_MONEY: self._handle_earn_money,
            Intent.RESEARCH: self._handle_research,
            Intent.PRESENTATION_CREATE: self._handle_presentation_create,
            Intent.CHAT: self._handle_chat,
            Intent.UNKNOWN: self._handle_unknown,
        }

        handler = handlers.get(parsed.intent, self._handle_unknown)
        try:
            return handler(parsed)
        except Exception as e:
            log.error(f"Fehler bei der Verarbeitung: {e}")
            return "Es ist ein Fehler aufgetreten. Bitte versuche es noch einmal."

    def _handle_greeting(self, parsed: ParsedCommand) -> str:
        username = self.memory.get_username()
        if username:
            return f"Hallo {username}! Wie kann ich dir helfen?"
        return random.choice(NLPEngine.GREETING_RESPONSES)

    def _handle_farewell(self, parsed: ParsedCommand) -> str:
        self.running = False
        return random.choice(config.FAREWELLS)

    def _handle_chat(self, parsed: ParsedCommand) -> str:
        response = self.nlp.get_chat_response(parsed.raw_text)
        if response:
            return response
        return "Erzaehl mir mehr!"

    def _handle_restaurant(self, parsed: ParsedCommand) -> str:
        location = parsed.entities.get("location", "")
        if not location:
            return "In welcher Stadt oder Region soll ich nach Restaurants suchen?"
        return self.web_search.search_restaurants(location)

    def _handle_earn_money(self, parsed: ParsedCommand) -> str:
        topic = parsed.entities.get("topic", "")
        if not topic:
            topic = "online"
        return self.web_search.search_earning(topic)

    def _handle_research(self, parsed: ParsedCommand) -> str:
        query = parsed.entities.get("search_query", "")
        if not query:
            return "Was soll ich recherchieren?"
        return self.web_search.research(query)

    def _handle_web_search(self, parsed: ParsedCommand) -> str:
        query = parsed.entities.get("search_query", "")
        if not query:
            return "Was soll ich suchen?"
        return self.web_search.search(query)

    def _handle_camera_show(self, parsed: ParsedCommand) -> str:
        query = parsed.entities.get("camera_query", "")
        if not query:
            cams = self.cameras.get_all_cameras()
            if cams:
                return f"Verfuegbare Kameras: {', '.join(c['name'] for c in cams[:5])}. Welche moechtest du sehen?"
            return "Keine Kameras verfuegbar."
        results = self.cameras.search_cameras(query)
        if results:
            return f"Gefunden: {results[0]['name']} in {results[0]['city']}. Kamera wird geladen..."
        return f"Keine Kamera fuer '{query}' gefunden. Verfuegbare Staedte: Zurich, London, Paris, New York, Tokyo, Dubai, Rom, Berlin."

    def _handle_camera_list(self, parsed: ParsedCommand) -> str:
        cams = self.cameras.get_all_cameras()
        if not cams:
            return "Keine Kameras verfuegbar."
        lines = [f"  - {c['name']} ({c['city']}, {c['country']})" for c in cams]
        return f"Verfuegbare Kameras:\n" + "\n".join(lines)

    def _handle_camera_add(self, parsed: ParsedCommand) -> str:
        text = parsed.raw_text
        import re
        url_match = re.search(r"(https?://[^\s]+)", text)
        if url_match:
            result = self.cameras.add_youtube_stream(url_match.group(1))
            if "error" in result:
                return f"Fehler: {result['error']}"
            return f"Kamera '{result['name']}' hinzugefuegt!"
        return "Bitte gib eine YouTube-URL an, die du als Kamera hinzufuegen moechtest."

    def _handle_presentation_create(self, parsed: ParsedCommand) -> str:
        if not HAS_PRESENTATION or self.presentations is None:
            return ("Praesentation-Funktion nicht verfuegbar. "
                    "Bitte installiere python-pptx: pip install python-pptx")
        topic = parsed.entities.get("topic", "")
        if not topic:
            return "Zu welchem Thema soll ich die Praesentation erstellen?"
        slides = parsed.entities.get("slides", 8)
        if slides < 3:
            slides = 8
        if slides > 15:
            slides = 15
        try:
            filepath = self.presentations.create_presentation(topic, slides, "jarvis")
            filename = os.path.basename(filepath)
            return (
                f"Praesentation erstellt! ({slides} Folien)\n"
                f"Thema: {topic}\n"
                f"Datei: {filename}\n"
                f"Sie ist bereit zum Download im Web-HUD."
            )
        except Exception as e:
            log.error(f"Praesentation fehlgeschlagen: {e}")
            return f"Fehler beim Erstellen: {e}"

    def _handle_task_add(self, parsed: ParsedCommand) -> str:
        task_text = parsed.entities.get("task_text", "")
        date_text = parsed.entities.get("date_text", "")
        if not task_text:
            return "Was soll ich dir als Aufgabe merken? Bitte beschreibe die Aufgabe."
        success = self.tasks.add_task(task_text, date_text)
        if success:
            date_part = f" fuer {date_text}" if date_text else ""
            return f"Okay! Aufgabe '{task_text}' gespeichert{date_part}."
        return "Es gab ein Problem beim Speichern der Aufgabe."

    def _handle_task_delete(self, parsed: ParsedCommand) -> str:
        task_id = parsed.entities.get("number")
        if task_id:
            success = self.tasks.delete_task(task_id)
            if success:
                return f"Aufgabe #{task_id} wurde geloescht."
            return f"Aufgabe #{task_id} konnte nicht gefunden werden."
        tasks = self.tasks.get_all_tasks()
        if not tasks:
            return "Du hast keine offenen Aufgaben."
        task_list = "\n".join(f"  #{t['id']}: {t['title']}" for t in tasks)
        return f"Welche Aufgabe moechtest du loeschen?\n{task_list}"

    def _handle_task_complete(self, parsed: ParsedCommand) -> str:
        task_id = parsed.entities.get("number")
        if task_id:
            success = self.tasks.complete_task(task_id)
            if success:
                return f"Aufgabe #{task_id} als erledigt markiert! Gut gemacht!"
            return f"Aufgabe #{task_id} konnte nicht gefunden werden."
        return "Welche Aufgabe soll ich als erledigt markieren? Bitte gib die Aufgaben-Nummer an."

    def _handle_note_add(self, parsed: ParsedCommand) -> str:
        note_text = parsed.entities.get("note_text", "")
        if not note_text:
            return "Was soll ich als Notiz speichern?"
        success = self.notes.add_note(note_text)
        if success:
            return f"Notiz gespeichert: '{note_text}'"
        return "Es gab ein Problem beim Speichern der Notiz."

    def _handle_note_delete(self, parsed: ParsedCommand) -> str:
        note_id = parsed.entities.get("number")
        if note_id:
            success = self.notes.delete_note(note_id)
            if success:
                return f"Notiz #{note_id} wurde geloescht."
            return f"Notiz #{note_id} konnte nicht gefunden werden."
        notes = self.notes.get_all_notes()
        if not notes:
            return "Du hast keine Notizen."
        note_list = "\n".join(f"  #{n['id']}: {n['text']}" for n in notes)
        return f"Welche Notiz moechtest du loeschen?\n{note_list}"

    def _handle_calculate(self, parsed: ParsedCommand) -> str:
        expression = parsed.entities.get("expression", "")
        if not expression:
            text = parsed.raw_text.lower()
            calc_match = __import__("re").search(r"was\s+ist\s+(.+?)(?:\?|$)", text)
            if calc_match:
                expression = calc_match.group(1)
        if not expression:
            return "Was soll ich berechnen? Bitte gib einen Ausdruck ein."
        return self.calculator.calculate(expression)

    def _handle_timer_set(self, parsed: ParsedCommand) -> str:
        duration_text = parsed.entities.get("duration_text", "")
        if not duration_text:
            return "Fuer wie lange soll der Timer laufen? (z.B. '5 Minuten', '1 Stunde')"
        return self.timer.set_timer(duration_text)

    def _handle_timer_cancel(self, parsed: ParsedCommand) -> str:
        return self.timer.cancel_timer()

    def _handle_reminder_add(self, parsed: ParsedCommand) -> str:
        task_text = parsed.entities.get("task_text", "")
        date_text = parsed.entities.get("date_text", "")
        if not task_text:
            full_text = parsed.raw_text
            an_match = __import__("re").search(r"(?:an|daran)\s+(.+)", full_text, __import__("re").IGNORECASE)
            if an_match:
                task_text = an_match.group(1).strip()
        if not task_text:
            return "Woran soll ich dich erinnern?"
        success = self.reminders.add_reminder(task_text, date_text)
        if success:
            date_part = f" am {date_text}" if date_text else ""
            return f"Okay! Ich erinnere dich an '{task_text}'{date_part}."
        return "Es gab ein Problem beim Speichern der Erinnerung."

    def _handle_reminder_delete(self, parsed: ParsedCommand) -> str:
        reminder_id = parsed.entities.get("number")
        if reminder_id:
            success = self.reminders.delete_reminder(reminder_id)
            if success:
                return f"Erinnerung #{reminder_id} wurde geloescht."
            return f"Erinnerung #{reminder_id} konnte nicht gefunden werden."
        reminders = self.reminders.get_all_reminders()
        if not reminders:
            return "Du hast keine Erinnerungen."
        reminder_list = "\n".join(f"  #{r['id']}: {r['text']}" for r in reminders)
        return f"Welche Erinnerung moechtest du loeschen?\n{reminder_list}"

    def _handle_settings(self, parsed: ParsedCommand) -> str:
        username = parsed.entities.get("username", "")
        if username:
            self.memory.set_preference("username", username)
            return f"Schon gespeichert! Ich nenne dich ab jetzt {username}."
        current_name = self.memory.get_username()
        if current_name:
            return f"Dein Name ist {current_name}. Wenn du den Namen aendern moechtest, sag mir deinen neuen Namen."
        return "Du hast mir noch keinen Namen genannt. Wie soll ich dich nennen?"

    def _handle_help(self) -> str:
        return (
            "J.A.R.V.I.S. - Befehlsuebersicht\n\n"
            "  Aufgaben:\n"
            "    'Erinnere mich an [Aufgabe]' - Aufgabe hinzufuegen\n"
            "    'Welche Aufgaben habe ich?' - Aufgaben auflisten\n\n"
            "  Notizen:\n"
            "    'Notiz: [Text]' - Notiz speichern\n\n"
            "  Erinnerungen:\n"
            "    'Erinnere mich [Datum] an [Text]' - Erinnerung setzen\n\n"
            "  Websuche & Recherche:\n"
            "    'Suche nach [Thema]' - Internet durchsuchen\n"
            "    'Was ist [Begriff]?' - Erklaerung suchen\n"
            "    'Recherchiere [Thema]' - Tiefergehende Recherche\n\n"
            "  Restaurants:\n"
            "    'Wo kann man in [Stadt] gut essen?' - Restaurant-Tipps\n"
            "    'Restaurant Empfehlung [Stadt]' - Restaurants suchen\n\n"
            "  Geld verdienen:\n"
            "    'Wie kann ich 500 CHF verdienen?' - Einnahme-Moeglichkeiten\n"
            "    'Geld verdienen [Thema]' - Jobs & Nebenverdienst\n\n"
            "  Kameras:\n"
            "    'Zeig Kamera [Stadt]' - Webcam anzeigen\n"
            "    'Welche Kameras?' - Alle Kameras auflisten\n\n"
            "  Sonstiges:\n"
            "    'Wie spät ist es?' - Uhrzeit\n"
            "    'Wie ist das Wetter?' - Wetter\n"
            "    'Berechne [Ausdruck]' - Taschenrechner\n"
            "    'Timer [Dauer]' - Timer stellen\n"
            "    'Hilfe' - Diese Hilfe\n"
        )

    def _handle_unknown(self, parsed: ParsedCommand) -> str:
        text = parsed.raw_text.strip()
        low = text.lower()

        # Versuche hilfreiche Antworten statt "nicht verstanden"
        # Kurze Chats
        if len(low.split()) <= 3:
            if any(w in low for w in ["ok", "ja", "nein", "cool", "nice", "danke", "haha", "lol"]):
                return "Alles klar! Sag Bescheid wenn du was brauchst."
            if "?" in text:
                # Frage -> versuche Websuche
                try:
                    return self.web_search.search(text)
                except:
                    pass

        # Laengere freie Eingaben -> als Websuche/Recherche behandeln
        if len(text.split()) >= 3 and not low.startswith(("hilfe", "help")):
            # Wirkt wie eine Frage oder ein Thema?
            question_words = ["was", "wer", "wie", "warum", "wann", "wo", "welch", "kannst", "erklär", "erzaehl", "wieso", "weshalb"]
            if any(low.startswith(w) or f" {w} " in f" {low} " for w in question_words) or "?" in text:
                try:
                    result = self.web_search.search(text)
                    if result and "Keine Ergebnisse" not in result:
                        return result
                except:
                    pass

        recent = self.memory.get_recent_messages(3)
        context_hint = ""
        if len(recent) >= 2:
            prev_intent = recent[-2].get("intent", "")
            if prev_intent == "TASK_ADD":
                context_hint = " Meintest du eine neue Aufgabe hinzuzufuegen?"
            elif prev_intent == "NOTE_ADD":
                context_hint = " Meintest du eine Notiz hinzuzufuegen?"

        # Freundlicher, weniger "kacke"
        return (
            f"Hmm, das habe ich nicht ganz verstanden. Meintest du das anders?{context_hint}\n"
            f"Du kannst frei mit mir sprechen - z.B. 'Wie spät ist es?', 'Suche nach Quantencomputer', 'Erstelle eine Notiz: Einkaufen'.\n"
            f"'{text[:60]}' klingt spannend - erzaehl mir mehr oder tippe 'Hilfe'."
        )

    def check_reminders(self) -> list[str]:
        """Prueft auf faellige Erinnerungen (fuer Hintergrund-Check)."""
        return self.reminders.check_due_reminders()

    def shutdown(self) -> None:
        """Faehrt JARVIS herunter."""
        self.timer.cancel_timer()
        self.memory.save()
        log.info("JARVIS wurde heruntergefahren.")
