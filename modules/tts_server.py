"""Server-seitiges TTS mit Edge Neural Voices (kostenlos, hohe Qualitaet)."""
import asyncio
import hashlib
import os
from pathlib import Path
from utils.logger import log

TMS_DIR = Path("data/tts_cache")
TMS_DIR.mkdir(parents=True, exist_ok=True)

# Feste maennliche Stimme - wird nie wechseln
VOICE = "de-DE-ConradNeural"  # Maennlich, tief, JARVIS-like
FALLBACK_VOICE = "de-DE-KatjaNeural"  # Fallback falls Conrad nicht verfuegbar
RATE = "+0%"
PITCH = "-2Hz"

async def _synthesize_edge(text: str, voice: str = VOICE) -> bytes:
    """Nutzt edge-tts fuer hochwertige Synthese."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=RATE, pitch=PITCH)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        return audio_bytes
    except Exception as e:
        log.error(f"Edge TTS Fehler: {e}")
        raise

def synthesize(text: str, voice: str = VOICE, use_cache: bool = True) -> bytes:
    """Synchrone Wrapper - gibt MP3 Bytes zurueck."""
    if not text or not text.strip():
        return b""
    # Cache via hash
    cache_key = hashlib.md5(f"{voice}:{text}".encode()).hexdigest()
    cache_file = TMS_DIR / f"{cache_key}.mp3"
    if use_cache and cache_file.exists():
        return cache_file.read_bytes()

    # Versuche edge-tts
    try:
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # Falls bereits ein Loop laeuft (z.B. in SocketIO), neuen Thread nutzen
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                audio = pool.submit(asyncio.run, _synthesize_edge(text, voice)).result(timeout=15)
        else:
            audio = loop.run_until_complete(_synthesize_edge(text, voice))

        if audio and len(audio) > 100:
            if use_cache:
                cache_file.write_bytes(audio)
            return audio
    except Exception as e:
        log.warning(f"Edge TTS fehlgeschlagen, Fallback pyttsx3: {e}")

    # Fallback: pyttsx3 lokal
    try:
        import pyttsx3
        import tempfile
        engine = pyttsx3.init()
        # Suche maennliche Stimme
        voices = engine.getProperty("voices")
        for v in voices:
            if any(n in v.name for n in ["David", "Hans", "Conrad", "Stefan"]):
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 180)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            tmp_path = tf.name
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        data = Path(tmp_path).read_bytes() if Path(tmp_path).exists() else b""
        try:
            os.unlink(tmp_path)
        except:
            pass
        if data:
            return data
    except Exception as e:
        log.error(f"pyttsx3 Fallback fehlgeschlagen: {e}")

    return b""

def clear_cache():
    """Loescht alte Cache-Dateien (>100 Dateien)."""
    files = sorted(TMS_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
    if len(files) > 100:
        for f in files[:-100]:
            try:
                f.unlink()
            except:
                pass
