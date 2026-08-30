"""Semantische Intent-Erkennung mit Embeddings (lokal, gratis).
Faellt sanft auf Keyword-Matching zurueck falls Modell nicht verfuegbar.
"""
import re
from typing import Optional
from core.intent import Intent
from utils.logger import log

# Beispiel-Saetze pro Intent fuer semantisches Matching
INTENT_EXAMPLES = {
    Intent.GREETING: [
        "hallo", "hey guten morgen", "hi wie gehts", "moin moin",
        "servus gruezi", "guten tag jarvis", "hallo bist du da",
    ],
    Intent.FAREWELL: [
        "tschüss bis bald", "auf wiedersehen", "bye bye", "machs gut",
        "bis spaeter", "beende das programm", "fahr herunter",
    ],
    Intent.TIME: [
        "wie spät ist es", "sag mir die uhrzeit", "welche zeit haben wir",
        "wie viel uhr ist es", "aktuelle uhrzeit bitte",
    ],
    Intent.DATE: [
        "welches datum haben wir heute", "welcher tag ist heute", "datum bitte",
        "was ist heute fuer ein tag",
    ],
    Intent.DATETIME: [
        "datum und uhrzeit bitte", "zeit und datum",
    ],
    Intent.TASK_ADD: [
        "erinnere mich daran einkaufen zu gehen", "ich muss morgen zum arzt",
        "merk dir dass ich noch miete zahlen muss", "neue aufgabe hausaufgaben",
        "vergiss nicht den muell rauszubringen",
    ],
    Intent.TASK_LIST: [
        "was muss ich heute noch tun", "zeige meine aufgaben", "was steht an",
        "welche todos habe ich", "liste meine aufgaben auf",
    ],
    Intent.TASK_DELETE: [
        "lösche die aufgabe nummer zwei", "entferne aufgabe drei",
    ],
    Intent.TASK_COMPLETE: [
        "aufgabe eins ist erledigt", "markiere aufgabe zwei als fertig",
    ],
    Intent.NOTE_ADD: [
        "schreib eine notiz einkaufsliste milch brot", "notiere idee fuer projekt",
        "merk dir notiz wichtigen termin",
    ],
    Intent.NOTE_LIST: ["zeige meine notizen", "welche notizen habe ich"],
    Intent.NOTE_DELETE: ["lösche notiz nummer eins"],
    Intent.WEATHER: [
        "wie wird das wetter morgen", "regnet es heute", "temperatur draussen",
        "wettervorhersage berlin",
    ],
    Intent.CALCULATE: [
        "berechne fuenf plus drei", "was ist zwanzig mal vier", "rechne 10 geteilt durch 2",
        "kannst du rechnen", "wie viel ist 100 minus 30",
    ],
    Intent.TIMER_SET: [
        "stell einen timer auf fuenf minuten", "wecker in zehn minuten",
        "timer fuer eine stunde",
    ],
    Intent.TIMER_CANCEL: ["stoppe den timer", "timer abbrechen"],
    Intent.REMINDER_ADD: ["erinnere mich morgen an arzttermin"],
    Intent.REMINDER_LIST: ["welche erinnerungen habe ich"],
    Intent.REMINDER_DELETE: ["lösche erinnerung eins"],
    Intent.HELP: [
        "was kannst du alles", "hilfe bitte", "welche befehle gibt es",
        "wie funktioniert das system",
    ],
    Intent.SETTINGS: [
        "mein name ist danilo", "ich heisse peter", "nenn mich chef",
    ],
    Intent.WEB_SEARCH: [
        "suche nach quantencomputer", "was ist fotosynthese", "wer ist einstein",
        "erkläre mir schwarze löcher", "wie funktioniert blockchain",
    ],
    Intent.CAMERA_SHOW: [
        "zeige mir die kamera matterhorn", "webcam zugspitze bitte", "live bild new york",
    ],
    Intent.CAMERA_LIST: ["welche kameras gibt es", "zeige alle webcams"],
    Intent.CAMERA_ADD: ["füge neue kamera hinzu"],
    Intent.RESTAURANT: [
        "wo kann man in zürich gut essen", "restaurant empfehlung berlin",
        "ich habe hunger wo gehen wir essen", "beste pizzeria in der nähe",
    ],
    Intent.EARN_MONEY: [
        "wie kann ich geld verdienen", "nebenjob gesucht", "500 franken verdienen",
        "geld verdienen tipps",
    ],
    Intent.RESEARCH: [
        "recherchiere künstliche intelligenz ausführlich", "analysiere das thema klimawandel",
        "mache eine zusammenfassung über",
    ],
    Intent.PRESENTATION_CREATE: [
        "erstelle eine präsentation über python", "mache powerpoint zu ki",
        "folien über webentwicklung bitte",
    ],
    Intent.CHAT: [
        "wie geht es dir heute", "erzähl mir einen witz", "danke dir",
        "was machst du gerade", "bist du da", "du bist toll",
        "wie ist das leben", "was denkst du über", "kannst du mir helfen",
        "hey", "ok", "ja", "nein", "cool", "super",
    ],
}

# Fuer schnelles Fallback: TF-IDF ohne Modell
_tfidf_vectors = None
_intent_labels = None
_tfidf_model = None
_semantic_model = None
_semantic_embeddings = None

def _init_tfidf():
    global _tfidf_vectors, _intent_labels, _tfidf_model
    if _tfidf_vectors is not None:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        texts = []
        labels = []
        for intent, examples in INTENT_EXAMPLES.items():
            for ex in examples:
                texts.append(ex.lower())
                labels.append(intent)
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer="char_wb", sublinear_tf=True)
        vectors = vectorizer.fit_transform(texts)
        _tfidf_vectors = vectors
        _intent_labels = labels
        _tfidf_model = vectorizer
        log.info(f"TF-IDF Intent-Modell geladen ({len(texts)} Beispiele)")
    except Exception as e:
        log.warning(f"TF-IDF nicht verfuegbar: {e}")

def _init_semantic():
    global _semantic_model, _semantic_embeddings
    if _semantic_model is not None:
        return _semantic_model is not False
    try:
        from sentence_transformers import SentenceTransformer
        # Kleines mehrsprachiges Modell, 120MB, versteht Deutsch perfekt
        _semantic_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        # Pre-compute intent centroids
        import numpy as np
        centroids = {}
        for intent, examples in INTENT_EXAMPLES.items():
            embs = _semantic_model.encode(examples, normalize_embeddings=True)
            centroids[intent] = np.mean(embs, axis=0)
        _semantic_embeddings = centroids
        log.info("Semantic Intent-Modell geladen (MiniLM-L12)")
        return True
    except Exception as e:
        log.info(f"Semantic Modell nicht verfuegbar (nutze TF-IDF): {e}")
        _semantic_model = False
        return False

def classify(text: str) -> tuple[Optional[Intent], float]:
    """
    Gibt (Intent, Confidence) zurueck.
    Versucht: 1. Semantic Embeddings, 2. TF-IDF, 3. None
    """
    cleaned = text.lower().strip()
    if not cleaned:
        return None, 0.0

    # 1. Versuche Semantic
    if _init_semantic():
        try:
            import numpy as np
            q_emb = _semantic_model.encode([cleaned], normalize_embeddings=True)[0]
            best_intent = None
            best_score = -1
            for intent, centroid in _semantic_embeddings.items():
                score = float(np.dot(q_emb, centroid))
                if score > best_score:
                    best_score = score
                    best_intent = intent
            # Schwelle: 0.35 ist gut fuer MiniLM, darunter ist Rauschen
            if best_score >= 0.32:
                return best_intent, min(best_score, 1.0)
        except Exception as e:
            log.debug(f"Semantic classify Fehler: {e}")

    # 2. TF-IDF Fallback
    _init_tfidf()
    if _tfidf_model is not None:
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            q_vec = _tfidf_model.transform([cleaned])
            sims = cosine_similarity(q_vec, _tfidf_vectors)[0]
            # Max pro Intent
            intent_scores = {}
            for label, score in zip(_intent_labels, sims):
                if label not in intent_scores or score > intent_scores[label]:
                    intent_scores[label] = score
            best_intent = max(intent_scores, key=intent_scores.get)
            best_score = intent_scores[best_intent]
            if best_score >= 0.36:  # gegen Random-Strings
                return best_intent, min(float(best_score) * 1.5, 1.0)
        except Exception as e:
            log.debug(f"TF-IDF classify Fehler: {e}")

    return None, 0.0
