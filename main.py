import sys
import time
import threading
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.engine import JarvisEngine
from interface.text_ui import TextUI, BLUE, GOLD, GREEN, RED, WHITE, DIM, RESET
from interface.voice_input import VoiceInput
from interface.voice_output import VoiceOutput
from utils.logger import log
import config


def boot_sequence(ui: TextUI):
    """Cinematic Iron Man Boot-Sequenz."""
    os.system("cls" if os.name == "nt" else "clear")

    print(f"\n{DIM}  Stark Industries - Secure Terminal v3.0{RESET}")
    time.sleep(0.3)
    print(f"{DIM}  Verbindung wird hergestellt...{RESET}")
    time.sleep(0.5)

    boot_steps = [
        (0.3, f"  {DIM}[INIT]{RESET} Kernsysteme laden..."),
        (0.2, f"  {DIM}[INIT]{RESET} Arc Reactor MK VII starten..."),
        (0.4, f"  {GREEN}[  OK]{RESET} Energieversorgung: {GREEN}STABIL{RESET}"),
        (0.2, f"  {DIM}[INIT]{RESET} NLP-Engine initialisieren..."),
        (0.3, f"  {GREEN}[  OK]{RESET} Sprachverarbeitung: {GREEN}BEREIT{RESET}"),
        (0.2, f"  {DIM}[INIT]{RESET} Aufgaben-Datenbank verbinden..."),
        (0.3, f"  {GREEN}[  OK]{RESET} Persistenz: {GREEN}AKTIV{RESET}"),
        (0.2, f"  {DIM}[INIT]{RESET} Erinnerungs-Modul starten..."),
        (0.2, f"  {GREEN}[  OK]{RESET} Hintergrundprozesse: {GREEN}LAUFEND{RESET}"),
        (0.2, f"  {DIM}[INIT]{RESET} Sicherheitsprotokolle pruefen..."),
        (0.3, f"  {GREEN}[  OK]{RESET} Sicherheit: {GREEN}LEVEL 5{RESET}"),
        (0.1, ""),
        (0.3, f"  {GOLD}>>> Alle Systeme nominal. JARVIS bereit. <<<"),
    ]

    for delay, msg in boot_steps:
        time.sleep(delay)
        if msg:
            print(msg)

    time.sleep(0.5)
    ui.display_welcome()


def reminder_background_check(engine: JarvisEngine, ui: TextUI, interval: int = 60):
    """Prueft im Hintergrund auf faellige Erinnerungen."""
    while engine.running:
        try:
            notifications = engine.check_reminders()
            for note in notifications:
                print(f"\n  {GOLD}[ERINNERUNG]{RESET}  {GOLD}{note}{RESET}")
                log.info(f"Erinnerung ausgeloest: {note}")
        except Exception as e:
            log.error(f"Fehler bei Erinnerungspruefung: {e}")
        time.sleep(interval)


def main():
    """Hauptfunktion von JARVIS."""
    ui = TextUI()
    boot_sequence(ui)

    engine = JarvisEngine()
    voice_in = VoiceInput()
    voice_out = VoiceOutput()

    use_voice = config.VOICE_ENABLED
    if voice_in.available:
        ui.display_system("Sprachsteuerung verfuegbar. Tippe 'sprache an' zum Aktivieren.")
    else:
        ui.display_system("Sprachsteuerung nicht verfuegbar (kein Mikrofon).")

    reminder_thread = threading.Thread(
        target=reminder_background_check,
        args=(engine, ui, config.REMINDER_CHECK_INTERVAL),
        daemon=True,
    )
    reminder_thread.start()

    while engine.running:
        try:
            if use_voice and voice_in.available:
                user_input = voice_in.listen()
                if user_input:
                    print(f"\n  {GOLD}[SPRACHE]{RESET}  {user_input}")
                else:
                    continue
            else:
                user_input = ui.get_input()

            if not user_input:
                continue

            if user_input.lower() in ("sprache an", "sprache aktivieren", "voice on"):
                if voice_in.available:
                    use_voice = True
                    voice_out.speak("Sprachsteuerung aktiviert.")
                    ui.display_success("Sprachsteuerung aktiviert.")
                else:
                    ui.display_warning("Sprachsteuerung ist nicht verfuegbar.")
                continue

            if user_input.lower() in ("sprache aus", "sprache deaktivieren", "voice off"):
                use_voice = False
                ui.display_success("Sprachsteuerung deaktiviert.")
                continue

            response = engine.process(user_input)

            if response:
                ui.display(response)
                if use_voice:
                    voice_out.speak(response)

        except KeyboardInterrupt:
            user_input = "tschuess"
        except Exception as e:
            log.error(f"Unerwarteter Fehler: {e}")
            ui.display_warning(f"Fehler: {e}")

    ui.display_goodbye()
    voice_out.stop()
    engine.shutdown()


if __name__ == "__main__":
    main()
