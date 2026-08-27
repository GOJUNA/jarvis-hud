try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False

from utils.logger import log
import config


class VoiceOutput:
    """Gibt Text als Sprache ueber Lautsprecher aus."""

    def __init__(self):
        self.engine = None
        if not TTS_AVAILABLE:
            log.warning("pyttsx3 nicht installiert. Sprachausgabe deaktiviert.")
            self.available = False
            return
        self.available = self._init_engine()

    def _init_engine(self) -> bool:
        """Initialisiert die Text-to-Sprache-Engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", config.VOICE_RATE)
            voices = self.engine.getProperty("voices")
            if voices and len(voices) > config.VOICE_INDEX:
                self.engine.setProperty("voice", voices[config.VOICE_INDEX].id)
            log.info("Text-to-Sprache-Engine initialisiert.")
            return True
        except Exception as e:
            log.warning(f"Text-to-Sprache nicht verfuegbar: {e}")
            return False

    def speak(self, text: str) -> None:
        """Spricht den uebergebenen Text aus."""
        if not self.available or not self.engine:
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            log.error(f"Fehler bei der Sprachausgabe: {e}")

    def set_rate(self, rate: int) -> None:
        """Aendert die Sprechgeschwindigkeit."""
        if self.engine:
            self.engine.setProperty("rate", rate)

    def stop(self) -> None:
        """Stoppt die aktuelle Sprachausgabe."""
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
