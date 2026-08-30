import sys
import os
import time
import threading
import psutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from core.engine import JarvisEngine
from utils.logger import log

app = Flask(__name__)
app.config["SECRET_KEY"] = "stark-industries-jarvis-3.0"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

jarvis = JarvisEngine()


def get_system_stats():
    """Sammelt System-Telemetrie-Daten."""
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()

    stats = {
        "cpu": round(cpu, 1),
        "ram_used": round(memory.used / (1024**3), 1),
        "ram_total": round(memory.total / (1024**3), 1),
        "ram_percent": round(memory.percent, 1),
        "disk_used": round(disk.used / (1024**3), 1),
        "disk_total": round(disk.total / (1024**3), 1),
        "disk_percent": round(disk.percent, 1),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }

    if battery:
        stats["battery_percent"] = battery.percent
        stats["battery_plugged"] = battery.power_plugged
    else:
        stats["battery_percent"] = None
        stats["battery_plugged"] = None

    return stats


def system_stats_thread():
    """Sendet alle 2 Sekunden Systemdaten an alle Clients."""
    while True:
        try:
            stats = get_system_stats()
            socketio.emit("system_stats", stats)
        except Exception as e:
            log.error(f"System-Stats Fehler: {e}")
        time.sleep(2)


@app.route("/")
def index():
    """Hauptseite des HUD."""
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    """REST API fuer Systemdaten."""
    return jsonify(get_system_stats())


@app.route("/api/tasks")
def api_tasks():
    """REST API fuer Aufgaben und Erinnerungen."""
    data = {
        "tasks": jarvis.tasks.get_all_tasks(),
        "reminders": jarvis.reminders.get_all_reminders(),
    }
    return jsonify(data)


@app.route("/api/notes")
def api_notes():
    """REST API fuer Notizen."""
    return jsonify({"notes": jarvis.notes.get_all_notes()})


@app.route("/api/cameras")
def api_cameras():
    """REST API fuer Kameras."""
    return jsonify({"cameras": jarvis.cameras.get_all_cameras()})


@app.route("/api/cameras/search")
def api_cameras_search():
    """Sucht Kameras."""
    query = request.args.get("q", "")
    results = jarvis.cameras.search_cameras(query)
    return jsonify({"cameras": results})


@app.route("/api/search")
def api_search():
    """Websuche."""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Kein Suchbegriff angegeben."})
    result = jarvis.web_search.search(query)
    return jsonify({"result": result})


@app.route("/api/camera_image/<camera_id>")
def api_camera_image(camera_id):
    """Holt ein Thumbnail einer Kamera."""
    url = jarvis.cameras.get_camera_image(camera_id)
    if url:
        return jsonify({"thumbnail": url})
    return jsonify({"error": "Kamera nicht gefunden."}), 404


@app.route("/api/presentations")
def api_presentations():
    """Listet erstellte Praesentationen."""
    import os
    pres_dir = "data/presentations"
    if not os.path.exists(pres_dir):
        return jsonify({"presentations": []})
    files = []
    for f in sorted(os.listdir(pres_dir), reverse=True):
        if f.endswith(".pptx"):
            path = os.path.join(pres_dir, f)
            stat = os.stat(path)
            files.append({
                "filename": f,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y %H:%M"),
            })
    return jsonify({"presentations": files})


@app.route("/api/presentations/download/<filename>")
def api_presentation_download(filename):
    """Laedt eine Praesentation herunter."""
    import os
    from flask import send_file
    pres_dir = "data/presentations"
    path = os.path.join(pres_dir, filename)
    if not os.path.exists(path) or not filename.endswith(".pptx"):
        return jsonify({"error": "Datei nicht gefunden."}), 404
    return send_file(path, as_attachment=True, download_name=filename)


@app.route("/api/tts")
def api_tts():
    """Server-seitiges TTS - gibt MP3 zurueck (Edge Neural, feste maennliche Stimme)."""
    text = request.args.get("text", "").strip()
    if not text:
        return jsonify({"error": "Kein Text"}), 400
    if len(text) > 2000:
        text = text[:2000]
    try:
        from modules.tts_server import synthesize
        audio = synthesize(text)
        if not audio or len(audio) < 100:
            return jsonify({"error": "TTS fehlgeschlagen"}), 500
        from flask import Response
        return Response(audio, mimetype="audio/mpeg", headers={
            "Content-Length": str(len(audio)),
            "Cache-Control": "public, max-age=3600",
        })
    except Exception as e:
        log.error(f"TTS API Fehler: {e}")
        return jsonify({"error": str(e)}), 500


@socketio.on("connect")
def handle_connect():
    """Client verbunden."""
    log.info("HUD Client verbunden.")
    emit("connected", {
        "status": "online",
        "message": "J.A.R.V.I.S. HUD Verbindung hergestellt.",
        "system": get_system_stats(),
    })


@socketio.on("disconnect")
def handle_disconnect():
    """Client getrennt."""
    log.info("HUD Client getrennt.")


@socketio.on("user_message")
def handle_message(data):
    """Verarbeitet Benutzernachricht vom HUD."""
    user_text = data.get("message", "").strip()
    if not user_text:
        return

    log.info(f"HUD Nachricht: {user_text}")
    emit("user_message", {
        "text": user_text,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }, broadcast=True)

    # Parse first to detect camera intent
    from core.intent import Intent
    parsed = jarvis.nlp.parse(user_text)

    response = jarvis.process(user_text)

    emit("jarvis_response", {
        "text": response,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "is_farewell": not jarvis.running,
    }, broadcast=True)

    # If camera intent, also emit camera feed
    if parsed.intent == Intent.CAMERA_SHOW:
        cam_query = parsed.entities.get("camera_query", "")
        if cam_query:
            results = jarvis.cameras.search_cameras(cam_query)
            if results:
                cam = results[0]
                emit("camera_feed", {
                    "id": cam["id"],
                    "name": cam["name"],
                    "city": cam["city"],
                    "country": cam["country"],
                    "url": cam["url"],
                    "thumbnail": cam["thumbnail"],
                }, broadcast=True)
            else:
                emit("camera_error", {"message": f"Keine Kamera fuer '{cam_query}' gefunden."}, broadcast=True)


@socketio.on("camera_show")
def handle_camera_show(data):
    """Zeigt eine Kamera im HUD."""
    camera_id = data.get("camera_id", "")
    cam = jarvis.cameras.get_camera(camera_id)
    if cam:
        emit("camera_feed", {
            "id": cam["id"],
            "name": cam["name"],
            "city": cam["city"],
            "url": cam["url"],
            "thumbnail": cam["thumbnail"],
        }, broadcast=True)
    else:
        emit("camera_error", {"message": f"Kamera '{camera_id}' nicht gefunden."}, broadcast=True)


@socketio.on("camera_search")
def handle_camera_search(data):
    """Sucht Kameras."""
    query = data.get("query", "")
    results = jarvis.cameras.search_cameras(query)
    emit("camera_results", {"cameras": results}, broadcast=True)


def start_background_threads():
    """Startet Hintergrund-Threads."""
    stats_thread = threading.Thread(target=system_stats_thread, daemon=True)
    stats_thread.start()

    def reminder_check():
        while True:
            try:
                notifications = jarvis.check_reminders()
                for note in notifications:
                    socketio.emit("reminder", {
                        "text": note,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    })
            except Exception as e:
                log.error(f"Erinnerungs-Check Fehler: {e}")
            time.sleep(60)

    reminder_thread = threading.Thread(target=reminder_check, daemon=True)
    reminder_thread.start()


if __name__ == "__main__":
    start_background_threads()
    print()
    print("  ============================================")
    print("                                           ")
    print("   J.A.R.V.I.S. HUD Server gestartet!      ")
    print("                                           ")
    print("   Oeffne: http://localhost:5000            ")
    print("                                           ")
    print("  ============================================")
    print()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
