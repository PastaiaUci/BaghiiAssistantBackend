from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

from app import *

if __name__ == '__main__':
    socketio.run(app, debug = True)
