from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    socketio.init_app(app)  # Initialize SocketIO with your Flask app

    with app.app_context():
        from . import routes
        return app
