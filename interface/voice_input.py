import io
import wave
import numpy as np

try:
    import sounddevice as sd
    SD_AVAILABLE = True
except (ImportError, OSError):
    sd = None
    SD_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False

from utils.logger import log


class VoiceInput:
    """Spracheingabe ueber sounddevice + speech_recognition."""

    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self):
        self.available = False
        if not SR_AVAILABLE:
            log.warning("SpeechRecognition nicht installiert. Spracheingabe deaktiviert.")
            return
        if not SD_AVAILABLE:
            log.warning("sounddevice nicht verfuegbar. Spracheingabe deaktiviert.")
            return
        self.recognizer = sr.Recognizer()
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Prueft ob ein Mikrofon verfuegbar ist."""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]
            if not input_devices:
                log.warning("Kein Eingabegeraet gefunden.")
                return False
            log.info(f"Mikrofon gefunden: {input_devices[0]['name']}")
            return True
        except Exception as e:
            log.warning(f"Kein Mikrofon verfuegbar: {e}")
            return False

    def listen(self, timeout: int = 10) -> str | None:
        """Nimmt Audio ueber sounddevice auf und erkennt Sprache."""
        if not self.available:
            return None
        try:
            print("  [Höre zu...]")
            duration = timeout
            audio_data = sd.rec(
                int(duration * self.SAMPLE_RATE),
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="int16",
            )
            sd.wait()

            audio_np = np.squeeze(audio_data)
            if np.max(np.abs(audio_np)) < 500:
                return None

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(audio_np.tobytes())
            wav_buffer.seek(0)

            with sr.AudioFile(wav_buffer) as source:
                audio = sr.Recognizer().record(source)

            text = self.recognizer.recognize_google(audio, language="de-DE")
            log.info(f"Spracheingabe erkannt: {text}")
            return text

        except sr.UnknownValueError:
            log.warning("Sprache konnte nicht erkannt werden.")
            return None
        except sr.RequestError as e:
            log.error(f"Spracherkennungs-API Fehler: {e}")
            return None
        except Exception as e:
            log.error(f"Unerwarteter Fehler bei Spracheingabe: {e}")
            return None
