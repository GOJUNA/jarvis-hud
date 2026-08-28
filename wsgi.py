# wsgi.py - Entry point für gunicorn
from web.app import socketio

if __name__ == "__main__":
    socketio.run(socketio.app, host="0.0.0.0", port=5000)