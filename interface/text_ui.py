import sys
import time
import os
from colorama import init, Fore, Style, Back
from utils.logger import log

init(autoreset=True)

BLUE = Fore.CYAN + Style.BRIGHT
GOLD = Fore.YELLOW + Style.BRIGHT
RED = Fore.RED + Style.BRIGHT
GREEN = Fore.GREEN + Style.BRIGHT
DIM = Style.DIM
BOLD = Style.BRIGHT
RESET = Style.RESET_ALL
WHITE = Fore.WHITE + Style.BRIGHT

ARC_REACTOR = f"""
{GOLD}         ___
       /   \\
      | {WHITE}(){GOLD} |
       \\___/
{RESET}"""


class TextUI:
    """Iron Man stilisierte Benutzerschnittstelle fuer JARVIS."""

    def __init__(self):
        self.typing_speed = 0.02
        self.is_typing = True

    def _type_print(self, text: str, color: str = BLUE, delay: float = 0.0) -> None:
        """Simuliert Tipp-Effekt wie bei Iron Man's JARVIS."""
        if not self.is_typing or delay == 0:
            print(f"{color}{text}{RESET}")
            return
        print(f"{color}", end="", flush=True)
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print(f"{RESET}")

    def _clear_line(self) -> None:
        """Loescht die aktuelle Zeile."""
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def display(self, text: str) -> None:
        """Gibt JARVIS Antwort aus mit Styling."""
        lines = text.split("\n")
        print()
        for line in lines:
            if line.strip():
                self._type_print(f"  {BLUE}[J.A.R.V.I.S.]{RESET}  {WHITE}{line}{RESET}", WHITE, self.typing_speed)
            else:
                print()
        print()

    def display_system(self, text: str) -> None:
        """Zeigt System-Meldungen an."""
        self._type_print(f"  {DIM}[SYSTEM]{RESET}  {DIM}{text}{RESET}", DIM)

    def display_warning(self, text: str) -> None:
        """Zeigt Warnungen an."""
        print(f"  {RED}[WARNUNG]{RESET}  {RED}{text}{RESET}")

    def display_success(self, text: str) -> None:
        """Zeigt Erfolgsmeldungen an."""
        print(f"  {GREEN}[OK]{RESET}  {GREEN}{text}{RESET}")

    def get_input(self) -> str:
        """Liest Benutzereingabe mit stylischem Prompt."""
        try:
            prompt = f"\n  {GOLD}>>>{RESET} "
            user_input = input(prompt).strip()
            return user_input
        except (EOFError, KeyboardInterrupt):
            return "tschuess"

    def display_welcome(self) -> None:
        """Zeigt den Iron Man stilisierten Willkommens-Banner."""
        os.system("cls" if os.name == "nt" else "clear")

        arc_reactor = f"""{GOLD}
                           _______________
                          /               \\
                         /    {WHITE}___{GOLD}    \\
                        |    {WHITE}/   \\{GOLD}    |
                        |   {WHITE}|  () |{GOLD}   |
                        |    {WHITE}\\___/{GOLD}    |
                         \\               /
                          \\_____________/{RESET}"""

        banner_lines = [
            "",
            f"{BLUE}",
            f"    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗",
            f"    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝",
            f"    ██║███████║██████╔╝██║   ██║██║███████╗",
            f"   {GOLD}██║{BLUE}██╔══██║██╔══██╗╚██╗ ██╔╝{BLUE}██║╚════██║",
            f"   {GOLD}██║{BLUE}██║  ██║██║  ██║ ╚████╔╝ {GOLD}██║{BLUE}███████║",
            f"   {GOLD}╚═╝{BLUE}╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  {GOLD}╚═╝{BLUE}╚══════╝",
            f"{RESET}",
        ]

        for line in banner_lines:
            print(line)
            time.sleep(0.05)

        print(arc_reactor)
        time.sleep(0.2)

        info_box = f"""
{BLUE}  ╔══════════════════════════════════════════════════════╗
  ║                                                      ║
  ║   {GOLD}Just A Rather Very Intelligent System{BLUE}                ║
  ║   {WHITE}Version 3.0 - Stark Industries Protocol{BLUE}             ║
  ║                                                      ║
  ║   {DIM}Powered by: Arc Reactor MK VII{BLUE}                      ║
  ║   {DIM}Status: {GREEN}ONLINE{BLUE}   |   {DIM}Security: LEVEL 5{BLUE}             ║
  ║                                                      ║
  ╚══════════════════════════════════════════════════════╝{RESET}
"""
        print(info_box)
        time.sleep(0.3)

        commands_info = f"""
{DIM}  Verfuegbare Befehle:{RESET}
  {WHITE}─────────────────────────────────────────────────{RESET}
  {GOLD}Aufgaben:{RESET}    {BLUE}erinnere mich an...{RESET}  |  {BLUE}welche aufgaben?{RESET}  |  {BLUE}aufgabe erledigt{RESET}
  {GOLD}Notizen:{RESET}     {BLUE}notiz: ...{RESET}           |  {BLUE}welche notizen?{RESET}
  {GOLD}Erinnerung:{RESET}  {BLUE}erinnere mich [tag] an...{RESET}  |  {BLUE}welche erinnerungen?{RESET}
  {GOLD}System:{RESET}      {BLUE}wie spaet?{RESET}          |  {BLUE}welches datum?{RESET}
  {GOLD}Extras:{RESET}     {BLUE}wie ist das wetter?{RESET}  |  {BLUE}berechne ...{RESET}  |  {BLUE}timer ...{RESET}
  {GOLD}Steuerung:{RESET}  {BLUE}hilfe{RESET}              |  {BLUE}sprache an/aus{RESET}  |  {BLUE}tschuess{RESET}
  {WHITE}─────────────────────────────────────────────────{RESET}
"""
        print(commands_info)

    def display_goodbye(self) -> None:
        """Iron Man Verabschiedung."""
        print()
        goodbye_lines = [
            f"{BLUE}  ╔══════════════════════════════════════════════════╗{RESET}",
            f"{BLUE}  ║                                                  ║{RESET}",
            f"{BLUE}  ║   {GOLD}J.A.R.V.I.S.{BLUE} fährt herunter...                  ║{RESET}",
            f"{BLUE}  ║                                                  ║{RESET}",
            f"{BLUE}  ║   {WHITE}Arc Reactor: {RED}OFFLINE{BLUE}                          ║{RESET}",
            f"{BLUE}  ║   {WHITE}Alle Systeme: {RED}DEAKTIVIERT{BLUE}                     ║{RESET}",
            f"{BLUE}  ║                                                  ║{RESET}",
            f"{BLUE}  ║   {GOLD}Bis bald, Sir.{BLUE}                                  ║{RESET}",
            f"{BLUE}  ║                                                  ║{RESET}",
            f"{BLUE}  ╚══════════════════════════════════════════════════╝{RESET}",
        ]
        for line in goodbye_lines:
            print(line)
            time.sleep(0.08)
        print()
