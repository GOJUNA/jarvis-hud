import re
import requests
from utils.logger import log


class CameraManager:
    """Verwaltet oeffentliche Webcams mit direkten Bild-Feeds und YouTube-Livestreams."""

    CAMERAS = [
        # === FOTO-WEBCAM.EU (Direkte JPEG-Bilder) ===
        {
            "id": "matterhorn",
            "name": "Matterhorn",
            "city": "Zermatt",
            "country": "Schweiz",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/zermatt/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/zermatt/current/400.jpg",
        },
        {
            "id": "zugspitze",
            "name": "Zugspitze",
            "city": "Garmisch-Partenkirchen",
            "country": "Deutschland",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/zugspitze/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/zugspitze/current/400.jpg",
        },
        {
            "id": "innsbruck",
            "name": "Innsbruck Nordkette",
            "city": "Innsbruck",
            "country": "Oesterreich",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/innsbruck/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/innsbruck/current/400.jpg",
        },
        {
            "id": "salzburg",
            "name": "Salzburg Altstadt",
            "city": "Salzburg",
            "country": "Oesterreich",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/salzburg/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/salzburg/current/400.jpg",
        },
        {
            "id": "st-anton",
            "name": "St. Anton am Arlberg",
            "city": "St. Anton",
            "country": "Oesterreich",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/st-anton-galzig/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/st-anton-galzig/current/400.jpg",
        },
        {
            "id": "lienz",
            "name": "Lienz Zettersfeld",
            "city": "Lienz",
            "country": "Oesterreich",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/lienz-zettersfeld/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/lienz-zettersfeld/current/400.jpg",
        },
        {
            "id": "oberstdorf",
            "name": "Oberstdorf Fellhorn",
            "city": "Oberstdorf",
            "country": "Deutschland",
            "type": "image",
            "url": "https://www.foto-webcam.eu/webcam/oberstdorf/current/1200.jpg",
            "thumbnail": "https://www.foto-webcam.eu/webcam/oberstdorf/current/400.jpg",
        },
        # === YOUTUBE LIVESTREAMS (Echte aktive Streams) ===
        {
            "id": "new-york",
            "name": "New York - Brooklyn Bridge",
            "city": "New York",
            "country": "USA",
            "type": "youtube",
            "url": "https://www.youtube.com/embed/1kvGNR_A3DY?autoplay=1&mute=1",
            "thumbnail": "https://img.youtube.com/vi/1kvGNR_A3DY/maxresdefault.jpg",
        },
        {
            "id": "tokyo",
            "name": "Tokyo - Odaiba 4K",
            "city": "Tokyo",
            "country": "Japan",
            "type": "youtube",
            "url": "https://www.youtube.com/embed/PEIUQVdt9XQ?autoplay=1&mute=1",
            "thumbnail": "https://img.youtube.com/vi/PEIUQVdt9XQ/maxresdefault.jpg",
        },
        {
            "id": "paris",
            "name": "Paris - Eiffelturm",
            "city": "Paris",
            "country": "Frankreich",
            "type": "youtube",
            "url": "https://www.youtube.com/embed/OzYp4NRZlwQ?autoplay=1&mute=1",
            "thumbnail": "https://img.youtube.com/vi/OzYp4NRZlwQ/maxresdefault.jpg",
        },
        {
            "id": "world-tour",
            "name": "World Webcam Tour",
            "city": "Weltweit",
            "country": "",
            "type": "youtube",
            "url": "https://www.youtube.com/embed/xeQJBMx2abw?autoplay=1&mute=1",
            "thumbnail": "https://img.youtube.com/vi/xeQJBMx2abw/maxresdefault.jpg",
        },
        # === USGS VULKAN-KAMERAS (Hawaii) ===
        {
            "id": "kilauea",
            "name": "Kilauea Vulkankamera",
            "city": "Hawaii",
            "country": "USA",
            "type": "image",
            "url": "https://volcanoes.usgs.gov/cams/K2cam/images/M.jpg",
            "thumbnail": "https://volcanoes.usgs.gov/cams/K2cam/images/M.jpg",
        },
        {
            "id": "halemaumau",
            "name": "Halemaumau Krater",
            "city": "Hawaii",
            "country": "USA",
            "type": "image",
            "url": "https://volcanoes.usgs.gov/cams/V2cam/images/M.jpg",
            "thumbnail": "https://volcanoes.usgs.gov/cams/V2cam/images/M.jpg",
        },
    ]

    def __init__(self):
        self.cameras = self.CAMERAS.copy()

    def get_all_cameras(self) -> list[dict]:
        return self.cameras

    def get_camera(self, camera_id: str) -> dict | None:
        for cam in self.cameras:
            if cam["id"] == camera_id:
                return cam
        return None

    def search_cameras(self, query: str) -> list[dict]:
        query = query.lower().strip()
        results = []
        for cam in self.cameras:
            searchable = f"{cam['name']} {cam['city']} {cam['country']}".lower()
            if query in searchable:
                results.append(cam)
                continue
            for w in query.split():
                if len(w) >= 3:
                    w_norm = w.replace("oe", "ö").replace("ae", "ä").replace("ue", "ü")
                    if w in searchable or w_norm in searchable:
                        results.append(cam)
                        break
        return results

    def get_camera_image_bytes(self, camera_id: str) -> bytes | None:
        """Laedt das aktuelle Bild einer Webcam als Bytes."""
        cam = self.get_camera(camera_id)
        if not cam or cam["type"] != "image":
            return None
        try:
            resp = requests.get(cam["url"], timeout=10)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            log.error(f"Kamera-Bild-Fehler ({camera_id}): {e}")
            return None

    def add_youtube_stream(self, youtube_url: str, name: str = "") -> dict:
        video_id_match = re.search(
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)",
            youtube_url,
        )
        if not video_id_match:
            return {"error": "Ungueltige YouTube-URL"}
        video_id = video_id_match.group(1)
        new_cam = {
            "id": f"custom_{video_id}",
            "name": name or f"YouTube {video_id}",
            "city": "Benutzerdefiniert",
            "country": "",
            "type": "youtube",
            "url": f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        }
        self.cameras.append(new_cam)
        return new_cam
