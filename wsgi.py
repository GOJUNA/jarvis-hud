# wsgi.py - Entry point fuer gunicorn auf Render
from web.app import app, start_background_threads

# Hintergrund-Threads starten (System-Stats, Erinnerungen)
start_background_threads()

# `app` ist die Flask WSGI-App - gunicorn startet mit wsgi:app
# SocketIO laeuft im threading-Modus via Long-Polling (kein eventlet/gevent noetig)
