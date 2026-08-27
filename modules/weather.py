import requests
from utils.logger import log
import config


class WeatherModule:
    """Holt Wetterdaten von der OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city: str = "") -> str:
        """Gibt die aktuelle Wettervorhersage zurueck."""
        api_key = config.WEATHER_API_KEY
        if not api_key:
            return (
                "Fuer die Wetterabfrage benoetige ich einen API-Key.\n"
                "Setze die Umgebungsvariable WEATHER_API_KEY auf deinen OpenWeatherMap-Key.\n"
                "Kostenlos registrieren: https://openweathermap.org/api"
            )

        city = city or config.WEATHER_CITY
        try:
            params = {
                "q": city,
                "appid": api_key,
                "units": "metric",
                "lang": "de",
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            description = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return (
                f"Wetter in {city}:\n"
                f"  Temperatur: {temp:.1f} C (gefuehlt {feels_like:.1f} C)\n"
                f"  Beschreibung: {description}\n"
                f"  Luftfeuchtigkeit: {humidity}%\n"
                f"  Wind: {wind_speed} m/s"
            )
        except requests.exceptions.Timeout:
            return "Die Wetter-API antwortet nicht bitte versuche es spaeter erneut."
        except requests.exceptions.ConnectionError:
            return "Keine Internetverbindung. Ich kann das Wetter leider nicht abrufen."
        except KeyError:
            return f"Fuer die Stadt '{city}' konnte kein Wetter gefunden werden."
        except Exception as e:
            log.error(f"Wetter-API Fehler: {e}")
            return "Beim Abrufen des Wetters ist ein Fehler aufgetreten."
