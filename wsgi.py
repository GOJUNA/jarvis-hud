# wsgi.py - Entry point für gunicorn
from web.app import socketio

# Flask-App direkt exportieren (für gunicorn)
app = socketio.app

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)