import re
from dataclasses import dataclass, field
from core.intent import Intent

# Semantisches Modell optional
try:
    from core.semantic import classify as semantic_classify
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False
    semantic_classify = None


@dataclass
class ParsedCommand:
    """Ergebnis der NLP-Analyse."""
    intent: Intent = Intent.UNKNOWN
    entities: dict = field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 0.0


class NLPEngine:
    """Erweiterte NLP-Engine fuer natuerliche deutsche Sprache."""

    KEYWORDS = {
        Intent.GREETING: [
            "hallo", "hi", "hey", "moin", "servus", "gruess",
            "guten morgen", "guten tag", "guten abend",
            "willkommen", "schon dich zu sehen",
        ],
        Intent.FAREWELL: [
            "tschüss", "tschuess", "tschau", "bye", "ade", "bis bald",
            "gute nacht", "mach's gut", "pass auf dich auf", "bis später",
            "bis zum nächsten mal", "cu", "ciao", "shutdown", "beende",
            "ende", "fahre herunter", "shut down",
        ],
        Intent.TIME: [
            "wie spät", "wie spaet", "uhrzeit", "wie viel uhr",
            "aktuelle zeit", "zeit", "spät ist es", "spaet ist es",
            "wie spät ist es denn", "sag mir die uhrzeit",
            "welche uhrzeit", "wie spaet", "wie spaet denn",
            "um wie viel uhr", "sag die zeit",
        ],
        Intent.DATE: [
            "welches datum", "welcher tag", "welcher tag ist heute",
            "datum", "welches datum haben wir", "welcher tag ist heute",
            "sag mir das datum", "heute ist", "welches datum ist heute",
            "wie ist das datum",
        ],
        Intent.DATETIME: [
            "datum und zeit", "zeit und datum", "tag und zeit",
            "datum und uhrzeit", "wie spät und welches datum",
        ],
        Intent.TASK_ADD: [
            "erinnere mich an", "erinnere mich daran", "merk dir",
            "merk mir", "aufgabe hinzufügen", "aufgabe erstellen",
            "aufgabe speichern", "speichere eine aufgabe",
            "speicher eine aufgabe", "ich muss noch", "ich soll noch",
            "nicht vergessen", "todo", "to-do", "notiere als aufgabe",
            "aufgabe:", "als aufgabe", "als erinnerung",
            "ich vergesse sonst", "bitte merken",
        ],
        Intent.TASK_LIST: [
            "welche aufgaben", "welche aufgabe", "aufgaben anzeigen",
            "aufgaben liste", "aufgaben zeigen", "aufgaben auflisten",
            "zeig mir die aufgaben", "zeig mir aufgaben",
            "was muss ich heute tun", "was soll ich tun",
            "was habe ich vor", "offene aufgaben",
            "aufgaben heute", "aufgaben diese woche",
            "was steht an", "was steht heute an",
            "gib mir meine aufgaben", "liste meine aufgaben",
        ],
        Intent.TASK_DELETE: [
            "aufgabe löschen", "aufgabe loeschen", "aufgabe entfernen",
            "lösche aufgabe", "loesche aufgabe", "entferne aufgabe",
            "aufgabe weg", "nimm die aufgabe raus",
        ],
        Intent.TASK_COMPLETE: [
            "aufgabe erledigt", "aufgabe abgeschlossen",
            "erledige aufgabe", "erledige die aufgabe",
            "markiere als erledigt", "aufgabe ist fertig",
            "hab ich erledigt", "ist erledigt",
        ],
        Intent.NOTE_ADD: [
            "notiz", "notiz hinzufügen", "notiz machen",
            "schreib eine notiz", "hinterlass eine notiz",
            "notiere", "merke dir", "notiz:", "als notiz",
        ],
        Intent.NOTE_LIST: [
            "notizen anzeigen", "notizen liste", "notizen zeigen",
            "welche notizen", "zeig mir notizen", "notizen auflisten",
            "gib mir meine notizen", "was habe ich notiert",
        ],
        Intent.NOTE_DELETE: [
            "notiz löschen", "notiz loeschen", "notiz entfernen",
            "lösche notiz", "loesche notiz", "entferne notiz",
            "nimm die notiz", "notiz weg", "lösche mal die notiz",
            "loesche mal die notiz", "notiz raus",
        ],
        Intent.WEATHER: [
            "wie ist das wetter", "wettervorhersage",
            "wie ist das wetter heute",
            "regnet es", "wie wird das wetter",
            "wie kalt", "wie warm",
        ],
        Intent.CALCULATE: [
            "berechne", "rechne", "wie viel ist",
            "rechner", "taschenrechner", "rechne aus",
            "kannst du rechnen", "hilf mir rechnen",
        ],
        Intent.TIMER_SET: [
            "timer", "wecker", "stell einen timer", "stell einen wecker",
            "alarm", "erinnere mich in", "timer für",
            "setze einen timer", "ich brauche einen timer",
        ],
        Intent.TIMER_CANCEL: [
            "timer abbrechen", "timer stoppen", "timer löschen",
            "wecker abbrechen", "wecker stoppen", "wecker löschen",
            "stoppe den timer", "stoppe den wecker",
        ],
        Intent.REMINDER_ADD: [
            "erinnerung", "erinnere mich", "remind",
            "merke dir für", "erinnerung für",
        ],
        Intent.REMINDER_LIST: [
            "erinnerungen anzeigen", "erinnerungen liste",
            "welche erinnerungen", "zeig mir erinnerungen",
            "erinnerungen auflisten", "was erinnere ich",
        ],
        Intent.REMINDER_DELETE: [
            "erinnerung löschen", "erinnerung loeschen",
            "lösche erinnerung", "loesche erinnerung",
            "entferne erinnerung",
        ],
        Intent.HELP: [
            "hilfe", "help", "was kannst du", "was konntest du",
            "was kannst du alles", "befehle", "kommandos",
            "funktionen", "anleitung", "zeig mir was du kannst",
            "wie funktioniert das", "was geht", "wie bediene ich dich",
            "hilf mir", "kannst du mir helfen",
        ],
        Intent.SETTINGS: [
            "einstellungen", "settings", "konfiguration",
            "mein name ist", "ich heiße", "ich heisse",
            "nenn mich", "ruf mich", "name ist", "name heißt",
            "ich bin", "du kannst mich",
        ],
        Intent.WEB_SEARCH: [
            "suche", "such nach", "suche nach", "google", "googgle",
            "finde heraus", "finde raus",
            "was ist", "wer ist", "was sind", "was bedeutet",
            "erkläre", "erklaere", "was heisst",
            "was bedeutet das",
            "erzähle mir über", "erzaehle mir ueber",
            "informationen über", "info über", "info ueber",
            "wikipedia", "nachrichten", "news", "aktuelles",
            "was gibt es neues", "was gibt es",
            "wie funktioniert", "wie macht man",
            "was halten sie von", "meinung zu",
            "vergleiche", "unterschied zwischen",
        ],
        Intent.CAMERA_SHOW: [
            "kamera", "kameras", "webcam", "webcams", "show cam",
            "zeig kamera", "zeig mir die kamera", "camera",
            "live kamera", "live cam", "video", "stream",
            "zeig mir", "zeige mir", "schau dir an",
        ],
        Intent.CAMERA_LIST: [
            "welche kameras", "welche webcams", "kameras anzeigen",
            "kamera liste", "alle kameras", "verfügbare kameras",
            "welche streams", "welche cams",
        ],
        Intent.CAMERA_ADD: [
            "kamera hinzufügen", "kamera hinzufuegen",
            "cam hinzufügen", "cam hinzufuegen",
            "neue kamera", "neue cam", "eigene kamera",
            "eigene cam", "eigener stream",
        ],
        Intent.RESTAURANT: [
            "restaurant", "restaurants", "gastro", "gasthaus",
            "wo kann man essen", "wo kann man gut essen",
            "empfehlung restaurant", "restaurant empfehlung",
            "essen gehen", "wo gehen wir essen",
            "wo kann ich essen", "wo kann ich gut essen",
            "bistrot", "cafe", "café", "imbiss",
            "pizzeria", "sushi", "thai", "indisch",
            "gute küche", "gute kueche", "lecker essen",
            "hungry", "hunger", "ich habe hunger",
        ],
        Intent.EARN_MONEY: [
            "geld verdienen", "geld verdienen wie",
            "verdienst", "nebenverdienst", "nebenjob",
            "einnahmen", "einkommen", "money",
            "job finden", "job suchen", "arbeit suchen",
            "freelance", "freelancing", "selbständig", "selbststaendig",
            "business", "geschaeft", "gewinn",
            "500 chf", "1000 chf", "geld brauche",
            "wie kann ich geld", "verdienen",
            "side hustle", "hustle", "cash",
        ],
        Intent.RESEARCH: [
            "recherchiere", "recherche", "forsche",
            "analysiere", "analyse", "untersuche",
            "berichte uber", "berichte ueber",
            "was weisst du uber", "was weisst du ueber",
            "erzähle mir ausfuehrlich", "erzaehle mir ausfuehrlich",
            "detailierte information", "genauere information",
            "zusammenfassung", "fakten",
        ],
        Intent.PRESENTATION_CREATE: [
            "präsentation erstellen", "praesentation erstellen",
            "powerpoint erstellen", "ppt erstellen",
            "folien erstellen", "folien machen",
            "präsentation machen", "praesentation machen",
            "mach eine präsentation", "mach eine praesentation",
            "erstelle eine präsentation", "erstelle eine praesentation",
            "erstellen sie eine präsentation", "präsentation über",
            "praesentation ueber", "powerpoint über", "powerpoint ueber",
            "prasentation erstellen", "prasentation machen",
            "mach eine prasentation", "erstelle eine prasentation",
            "prasentation uber", "powerpoint uber",
            "praesentation uber", "präsentation uber",
            "ppt uber", "folien uber", "folien ueber",
        ],
        Intent.CHAT: [
            "wie gehts", "wie geht es", "wie geht's",
            "was machst du", "was machst du gerade",
            "wie bist du", "wie fuehlst du",
            "danke", "vielen dank", "super", "toll",
            "gut gemacht", "perfekt", "klasse",
            "ja", "nein", "ok", "okay",
            "erzähl mir", "erzaehl mir",
            "witz", "witz erzählen", "mach einen witz",
            "was hältst du", "meinung",
            "bist du da", "bist du noch da",
        ],
    }

    GREETING_RESPONSES = [
        "Hallo! Wie kann ich dir helfen?",
        "Hey! Was kann ich fuer dich tun?",
        "Gruess dich! Wobei kann ich unterstuetzen?",
    ]

    CHAT_RESPONSES = {
        "wie geht": "Mir geht's super! Ich bin immer bereit dir zu helfen. Und dir?",
        "was machst du": "Ich warte auf deine Befehle und halte alles bereit!",
        "wie bist du": "Ausgezeichnet! Alle Systeme laufen nominal.",
        "danke": "Bitte gerne! Das ist mein Job.",
        "super": "Danke! Freut mich zu hoeren!",
        "gut gemacht": "Danke! Ich gebe mir immer muehe.",
        "perfekt": "Vielen Dank! Das bedeutet mir viel.",
        "klasse": "Super! Ich mach weiter so!",
        "ja": "Verstanden!",
        "nein": "Okay, kein Problem.",
        "ok": "Bereit wenn du mich brauchst!",
        "okay": "Alles klar!",
        "bist du da": "Ja, ich bin hier! Alle Systeme aktiv.",
        "witz": None,
    }

    def parse(self, text: str) -> ParsedCommand:
        """Analysiert einen Text und erkennt Intent + Entitaeten.
        Reihenfolge: 1. Semantik (Embeddings/TF-IDF), 2. Keyword-Scoring, 3. Fuzzy.
        """
        cleaned = text.lower().strip()
        parsed = ParsedCommand(raw_text=text)

        # 1. Semantik zuerst (versteht freie Sprache)
        if HAS_SEMANTIC:
            sem_intent, sem_conf = semantic_classify(text)
            if sem_intent is not None and sem_conf >= 0.32:
                parsed.intent = sem_intent
                parsed.confidence = sem_conf
                parsed.entities = self._extract_entities(cleaned, parsed.intent)
                return parsed

        # 2. Klassisches Keyword-Scoring
        scores = {}
        for intent, keywords in self.KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in cleaned:
                    score += len(keyword) / max(len(cleaned), 1)
            if score > 0:
                scores[intent] = score

        if scores:
            best_intent = max(scores, key=scores.get)
            best_score = scores[best_intent]
            if best_score >= 0.08:
                parsed.intent = best_intent
                parsed.confidence = min(best_score, 1.0)
                # Semantik als Tie-Breaker bei knappen Scores
                if HAS_SEMANTIC and best_score < 0.25:
                    sem_intent, sem_conf = semantic_classify(text)
                    if sem_intent is not None and sem_conf > best_score + 0.1:
                        parsed.intent = sem_intent
                        parsed.confidence = sem_conf
            else:
                # Schwacher Score -> versuche Semantik nochmal mit niedrigerer Schwelle
                if HAS_SEMANTIC:
                    sem_intent, sem_conf = semantic_classify(text)
                    if sem_intent is not None and sem_conf >= 0.28:
                        parsed.intent = sem_intent
                        parsed.confidence = sem_conf
                    else:
                        parsed.intent = self._guess_intent_fuzzy(cleaned)
                        parsed.confidence = best_score if parsed.intent != Intent.UNKNOWN else 0.0
                else:
                    parsed.intent = self._guess_intent_fuzzy(cleaned)
                    parsed.confidence = best_score if parsed.intent != Intent.UNKNOWN else 0.0
        else:
            if HAS_SEMANTIC:
                sem_intent, sem_conf = semantic_classify(text)
                if sem_intent is not None and sem_conf >= 0.28:
                    parsed.intent = sem_intent
                    parsed.confidence = sem_conf
                else:
                    parsed.intent = self._guess_intent_fuzzy(cleaned)
                    parsed.confidence = 0.0
            else:
                parsed.intent = self._guess_intent_fuzzy(cleaned)
                parsed.confidence = 0.0

        parsed.entities = self._extract_entities(cleaned, parsed.intent)
        return parsed

    def _guess_intent_fuzzy(self, text: str) -> Intent:
        """Fuzzy-Matching fuer nicht-exakte Treffer."""
        words = text.split()
        for intent, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                kw_words = keyword.split()
                matches = sum(1 for w in kw_words if any(fw.startswith(w[:3]) for fw in words if len(w) >= 3))
                if matches >= len(kw_words) * 0.6:
                    return intent

        if re.search(r"\d+\s*(?:plus|minus|mal|geteilt|hoch|\+|\-|\*|/)", text):
            return Intent.CALCULATE
        if re.search(r"\d+\s*(?:minute|stunde|sekunde|min|std|sec)", text):
            return Intent.TIMER_SET

        return Intent.UNKNOWN

    def get_chat_response(self, text: str) -> str | None:
        """Gibt eine passende Chat-Antwort zurueck oder None."""
        cleaned = text.lower().strip()

        if any(w in cleaned for w in ["witz", "witzig", "lach"]):
            import random
            wits = [
                "Warum trinkt ein Programmierer immer Tee? Weil in Java ist alles muell!",
                "Was sagt ein IT-ler wenn er in den Spiegel schaut? Hello World!",
                "Warum ist Programmieren wie Frostschutz? Beide brauchen eine gute Abdeckung!",
                "Was ist der Unterschied zwischen einem Bug und einem Feature? Ein Feature ist ein Bug mit Marketing!",
            ]
            return random.choice(wits)

        for pattern, response in self.CHAT_RESPONSES.items():
            if pattern in cleaned and response:
                return response

        return None

    def _extract_entities(self, text: str, intent: Intent) -> dict:
        """Extrahiert Entitaeten basierend auf dem erkannten Intent."""
        entities = {}

        date_match = re.search(
            r"(heute|morgen|uebermorgen|gestern|vorgestern|"
            r"n(?:ächsten?|aechsten?)\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)|"
            r"montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|"
            r"\d{1,2}\.\d{1,2}\.?\d{0,4}|\d{4}-\d{2}-\d{2})",
            text, re.IGNORECASE
        )
        if date_match:
            entities["date_text"] = date_match.group()

        time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", text)
        if time_match:
            entities["time"] = time_match.group()

        number_match = re.search(r"(\d+)", text)
        if number_match:
            entities["number"] = int(number_match.group())

        if intent in (Intent.TASK_ADD, Intent.TASK_DELETE, Intent.TASK_COMPLETE):
            task_text = self._extract_task_text(text, intent)
            if task_text:
                entities["task_text"] = task_text

        if intent == Intent.CALCULATE:
            calc_match = re.search(
                r"[\d\s]*(?:hoch|mal|plus|minus|geteilt)[\d\s]*|[\d\+\-\*\/\%\.\(\)\s]+",
                text, re.IGNORECASE
            )
            if calc_match:
                entities["expression"] = calc_match.group().strip()

        if intent == Intent.TIMER_SET:
            duration_match = re.search(r"(\d+)\s*(minute|min|stunde|std|sekunde|sec)", text, re.IGNORECASE)
            if duration_match:
                entities["duration_text"] = duration_match.group()

        if intent in (Intent.NOTE_ADD, Intent.NOTE_DELETE):
            note_match = re.search(r'(?:notiz|hinterlass)\s*[:\s]+(.+)', text, re.IGNORECASE)
            if not note_match:
                note_match = re.search(r'(?:notiere|merke dir|hinterlass)\s+(.+)', text, re.IGNORECASE)
            if note_match:
                entities["note_text"] = note_match.group(1).strip()

        if intent == Intent.SETTINGS:
            name_match = re.search(
                r"(?:name\s+(?:ist|heisst)|ich\s+(?:heisse|hieß)|mein\s+name\s+ist|nenn\s+mich|ruf\s+mich)\s*(.+)",
                text, re.IGNORECASE
            )
            if name_match:
                entities["username"] = name_match.group(1).strip()

        if intent == Intent.WEB_SEARCH:
            search_query = self._extract_search_query(text)
            if search_query:
                entities["search_query"] = search_query

        if intent == Intent.CAMERA_SHOW:
            cam_query = self._extract_camera_query(text)
            if cam_query:
                entities["camera_query"] = cam_query

        if intent == Intent.RESTAURANT:
            location = self._extract_location(text)
            if location:
                entities["location"] = location

        if intent == Intent.EARN_MONEY:
            topic = self._extract_earn_topic(text)
            if topic:
                entities["topic"] = topic

        if intent == Intent.RESEARCH:
            research_query = self._extract_search_query(text)
            if research_query:
                entities["search_query"] = research_query

        if intent == Intent.PRESENTATION_CREATE:
            topic = self._extract_presentation_topic(text)
            if topic:
                entities["topic"] = topic
            # Extract slide count if mentioned
            slides_match = re.search(r"(\d+)\s*(?:folien|seiten|slides?)", text, re.IGNORECASE)
            if slides_match:
                entities["slides"] = int(slides_match.group(1))

        return entities

    def _extract_search_query(self, text: str) -> str:
        """Extrahiert den Suchbegriff aus einem Websuche-Befehl."""
        remove_patterns = [
            r"^(?:suche\s+(?:nach\s+)?)",
            r"^(?:such\s+(?:nach\s+)?)",
            r"^(?:google\s+(?:nach\s+)?)",
            r"^(?:recherchiere\s+(?:nach\s+)?)",
            r"^(?:finde\s+(?:heraus|raus)\s+(?:was\s+)?)",
            r"^(?:was\s+ist\s+)",
            r"^(?:wer\s+ist\s+)",
            r"^(?:was\s+sind\s+)",
            r"^(?:was\s+bedeutet\s+)",
            r"^(?:erkl[aä]re\s+(?:mir\s+)?(?:die|das|den|die)\s+)",
            r"^(?:erz[aä]hle\s+mir\s+(?:über|ueber)\s+)",
            r"^(?:informationen\s+(?:über|ueber)\s+)",
            r"^(?:info\s+(?:über|ueber)\s+)",
            r"^(?:nachrichten\s+(?:über|ueber|zum|zur)\s+)",
            r"^(?:news\s+(?:zum|zur|über|ueber)\s+)",
            r"^(?:wie\s+funktioniert\s+)",
            r"^(?:wie\s+macht\s+man\s+)",
            r"^(?:unterschied\s+between\s+)",
            r"^(?:vergleiche\s+)",
            r"\?+$",
        ]
        result = text.strip()
        for pattern in remove_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
        result = re.sub(r"\s+", " ", result)
        return result if len(result) >= 2 else text.strip()

    def _extract_camera_query(self, text: str) -> str:
        """Extrahiert den Kamera-Suchbegriff."""
        remove_patterns = [
            r"^(?:zeig\s+(?:mir\s+)?(?:die\s+|den\s+|das\s+)?)",
            r"^(?:zeige\s+(?:mir\s+)?(?:die\s+|den\s+|das\s+)?)",
            r"^(?:schau\s+dir\s+)",
            r"^(?:live\s+)",
            r"^(?:camera\s+)",
            r"^(?:cam\s+)",
            r"^(?:webcam\s+)",
            r"^(?:kamera\s+)",
            r"^(?:stream\s+)",
            r"^(?:video\s+)",
        ]
        result = text.strip()
        for pattern in remove_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
        result = re.sub(r"\s+", " ", result)
        return result if len(result) >= 2 else text.strip()

    def _extract_location(self, text: str) -> str:
        """Extrahiert einen Ortsnamen aus einem Restaurant-Befehl."""
        stop_words = {"gut", "beste", "toll", "super", "lecker", "wo", "kann", "man",
                       "essen", "gehen", "empfehlung", "restaurant", "in", "bei", "nahe"}
        patterns = [
            r"(?:in|bei|nahe)\s+([A-ZÄÖÜ][a-zäöüß]+\.?(?:\s+[A-ZÄÖÜ][a-zäöüß]+\.?)*)",
            r"essen\s+(?:in|bei|nahe)\s+([A-ZÄÖÜ][a-zäöüß]+\.?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                words = location.split()
                filtered = [w for w in words if w.lower() not in stop_words]
                if filtered:
                    return " ".join(filtered)

        # Fallback: Letztes grossgeschriebenes Wort
        words = text.split()
        for w in reversed(words):
            clean = w.strip("?,.!")
            if clean and clean[0].isupper() and clean.lower() not in stop_words and len(clean) >= 2:
                return clean

        # Letzter Versuch: letztes Wort
        if words:
            return words[-1].strip("?,.!")
        return ""

    def _extract_earn_topic(self, text: str) -> str:
        """Extrahiert das Thema aus einem Geld-verdienen-Befehl."""
        # Spezielle Patterns fuer Betrag + Waehrung
        amount_match = re.search(r"(\d+)\s*(?:chf|eur|usd|franken|euro|dollar)", text, re.IGNORECASE)
        if amount_match:
            return amount_match.group(0).strip()

        # Rest des Textes nach Keyword
        cleaned = text.lower()
        for prefix in ["wie kann ich", "wie kann man", "wo kann ich", "wo kann man",
                        "geld verdienen", "verdienen", "nebenverdienst", "job"]:
            if prefix in cleaned:
                after = cleaned.split(prefix, 1)[-1].strip()
                if after:
                    # Stop words entfernen
                    for sw in ["damit", "davon", "durch", "mit", "online", "von zu hause"]:
                        after = after.replace(sw, "").strip()
                    if after:
                        return after

        # Fallback
        cleaned = re.sub(r"(?:wie|kann|ich|geld|verdienen|wo|damit|davon|durch)\s*", "", cleaned)
        return cleaned.strip() if cleaned.strip() else "online"

    def _extract_presentation_topic(self, text: str) -> str:
        """Extrahiert das Thema aus einem Präsentations-Befehl."""
        patterns = [
            r"(?:pr[aä]sentation|powerpoint|ppt|folien)\s+(?:über|ueber|uber|zu)\s+(.+)",
            r"(?:erstell|mach|mach mir)\s+(?:eine\s+)?(?:pr[aä]sentation|powerpoint|ppt|folien)\s+(?:über|ueber|uber|zu)\s+(.+)",
            r"(?:pr[aä]sentation|powerpoint|ppt|folien)\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                topic = re.sub(r"^(?:über|ueber|uber|zu|für)\s+", "", topic, flags=re.IGNORECASE)
                return topic.strip(" ?.!")
        # Fallback: letztes Wort nach Keyword
        cleaned = text.lower()
        for kw in ["präsentation", "praesentation", "prasentation", "powerpoint", "ppt", "folien"]:
            if kw in cleaned:
                after = cleaned.split(kw, 1)[-1].strip()
                after = re.sub(r"^(?:über|ueber|uber|zu|für)\s+", "", after)
                if after:
                    return after.strip(" ?.!")
        return text.strip(" ?.!")

    def _extract_task_text(self, text: str, intent: Intent) -> str:
        """Extrahiert den Aufgabentext aus einem Befehl."""
        remove_patterns = [
            r"^(?:erinnere\s+(?:mich\s+)?(?:an|daran)\s*)",
            r"^(?:merk\s+(?:mir|dir)\s+)",
            r"^(?:speichere?\s+(?:mir\s+)?(?:eine?\s+)?(?:aufgabe|erinnerung|todo)\s*:?\s*)",
            r"^(?:de[nm]?\s+aufgabe\s*:?\s*)",
            r"^(?:zur\s+aufgabe\s*)",
            r"^(?:aufgabe\s+(?:hinzufuegen|hinzufügen|erstellen|merk|speichern?)\s*:?\s*)",
            r"(?:nicht\s+vergessen\s*)",
            r"^(?:todo\s*:?\s*)",
            r"^(?:erledige?\s+)",
            r"^(?:ich\s+soll\s+)",
            r"^(?:als\s+(?:aufgabe|erinnerung)\s*)",
            r"^(?:bitte\s+merken\s*)",
            r"(?:morgen|heute|uebermorgen|montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)",
        ]

        result = text.strip()
        for pattern in remove_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()

        result = re.sub(r"^(?:die\s+|den\s+|das\s+)", "", result).strip()
        result = re.sub(r"\s+", " ", result)

        if len(result) < 2:
            return text.strip()
        return result
