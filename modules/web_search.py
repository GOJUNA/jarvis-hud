import requests
import re
from urllib.parse import quote_plus
from utils.logger import log


class WebSearch:
    """Internet-Recherche: DuckDuckGo, Wikipedia, Nachrichten, gezielte Suche."""

    HEADERS = {"User-Agent": "JARVIS/3.0 (Local Assistant; +https://localhost)"}

    def search(self, query: str) -> str:
        """Haupt-Suchfunktion."""
        query = query.strip()
        if not query:
            return "Was soll ich suchen?"

        results = []

        wiki = self._search_wikipedia(query)
        if wiki:
            results.append(wiki)

        ddg = self._search_duckduckgo(query)
        if ddg:
            results.append(ddg)

        if results:
            return "\n\n".join(results)

        return self._search_html_fallback(query)

    def search_restaurants(self, location: str) -> str:
        """Sucht Restaurants in einer bestimmten Stadt."""
        queries = [
            f"beste Restaurants {location}",
            f"Restaurant Empfehlung {location} Essen gehen",
            f"wo kann man gut essen in {location}",
        ]
        all_results = []
        for q in queries:
            r = self._search_duckduckgo(q)
            if r:
                all_results.append(r)
            wiki = self._search_wikipedia(f"Restaurantkulinarik {location}")
            if wiki:
                all_results.append(wiki)

        if all_results:
            header = f"Restaurant-Empfehlungen fuer {location}:\n\n"
            return header + "\n---\n".join(all_results[:4])

        return self._search_html_fallback(f"beste Restaurants {location}")

    def search_earning(self, topic: str) -> str:
        """Sucht Moeglichkeiten zum Geld verdienen."""
        queries = [
            f"Geld verdienen {topic}",
            f"job moeglichkeiten {topic}",
            f"nebenverdienst {topic}",
        ]
        all_results = []
        for q in queries:
            r = self._search_duckduckgo(q)
            if r:
                all_results.append(r)

        if all_results:
            header = f"Einnahme-Moeglichkeiten ({topic}):\n\n"
            return header + "\n---\n".join(all_results[:4])

        return self._search_html_fallback(f"Geld verdienen {topic}")

    def research(self, query: str) -> str:
        """Fuehrt eine tiefergehende Recherche durch."""
        results = []

        wiki = self._search_wikipedia(query)
        if wiki:
            results.append(wiki)

        ddg = self._search_duckduckgo(query)
        if ddg:
            results.append(ddg)

        news = self._search_duckduckgo(f"{query} Nachrichten aktuell")
        if news:
            results.append("[Aktuelle Nachrichten]\n" + news)

        if results:
            return "\n\n".join(results)

        return self._search_html_fallback(query)

    def get_page_content(self, url: str) -> str:
        """Holt den Text-Inhalt einer Webseite."""
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=10)
            resp.raise_for_status()
            text = resp.text
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:3000] if len(text) > 3000 else text
        except Exception as e:
            log.error(f"Fehler beim Laden der Seite {url}: {e}")
            return f"Konnte die Seite nicht laden: {e}"

    def _search_wikipedia(self, query: str) -> str:
        """Sucht auf Wikipedia (deutsch)."""
        try:
            resp = requests.get(
                "https://de.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 2,
                    "format": "json",
                },
                headers=self.HEADERS,
                timeout=5,
            )
            data = resp.json()
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                return ""

            parts = []
            for sr in search_results[:2]:
                title = sr["title"]
                resp2 = requests.get(
                    f"https://de.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}",
                    headers=self.HEADERS,
                    timeout=5,
                )
                if resp2.status_code == 200:
                    info = resp2.json()
                    extract = info.get("extract", "")
                    if extract:
                        parts.append(f"[Wikipedia - {title}] {extract[:500]}")

            return "\n".join(parts) if parts else ""
        except Exception as e:
            log.debug(f"Wikipedia-Suche fehlgeschlagen: {e}")
            return ""

    def _search_duckduckgo(self, query: str) -> str:
        """DuckDuckGo Instant Answer API."""
        try:
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                headers=self.HEADERS,
                timeout=5,
            )
            data = resp.json()

            parts = []

            abstract = data.get("AbstractText", "")
            if abstract:
                url = data.get("AbstractURL", "")
                source = data.get("AbstractSource", "")
                parts.append(f"[{source}] {abstract[:600]}")
                if url:
                    parts.append(f"Quelle: {url}")

            answer = data.get("Answer", "")
            if answer:
                parts.append(f"[Direktantwort] {answer}")

            related = data.get("RelatedTopics", [])
            if related and not parts:
                for topic in related[:5]:
                    if isinstance(topic, dict) and "Text" in topic:
                        parts.append(f"- {topic['Text'][:200]}")

            return "\n".join(parts) if parts else ""
        except Exception as e:
            log.debug(f"DuckDuckGo-Suche fehlgeschlagen: {e}")
            return ""

    def _search_html_fallback(self, query: str) -> str:
        """Fallback: DuckDuckGo HTML-Scraping."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            resp = requests.get(url, headers=self.HEADERS, timeout=8)
            text = resp.text
            results = re.findall(
                r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</span>',
                text,
                re.DOTALL,
            )
            if results:
                lines = []
                for link, title, snippet in results[:5]:
                    title = re.sub(r"<[^>]+>", "", title).strip()
                    snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                    lines.append(f"- {title}\n  {snippet}\n  {link}")
                return "[Websuche]\n" + "\n".join(lines)
        except Exception as e:
            log.debug(f"HTML-Fallback fehlgeschlagen: {e}")
        return f"Keine Ergebnisse fuer '{query}' gefunden."
