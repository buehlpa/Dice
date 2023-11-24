from flask import Flask
import webbrowser
import threading

# Import routes from routes.py
from routes import configure_routes

app = Flask(__name__)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

def create_app():
    configure_routes(app)
    return app

if __name__ == '__main__':
    threading.Timer(0.5, open_browser).start()
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
