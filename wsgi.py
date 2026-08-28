# wsgi.py - Entry point für gunicorn
from web.app import socketio

# Flask-App ist socketio.server (bei Flask-SocketIO)
app = socketio.server

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)