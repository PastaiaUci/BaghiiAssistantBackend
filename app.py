from flask import Flask, request, jsonify, session
from flask_pymongo import PyMongo
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from flask_socketio import SocketIO, emit
import threading
import subprocess
import os
import signal
import cv2
import base64
import numpy as np
from bson.json_util import dumps
from hand_gesture.hand_track_module import HandDetector
from hand_gesture.gesture_control import GestureControl
from face_recognition_module.face_recognition_module import process_face_recognition, handle_face_login

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session/'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:3000"}})

Session(app)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

voice_assistant_process = None
last_known_hand_position = None

app.config["MONGO_URI"] = "mongodb://localhost:27017/BaghiiAssistant"
mongo = PyMongo(app)

detector = HandDetector(maxHands=1)

@app.route('/users', methods=['GET'])
def get_users():
    users = mongo.db.users.find()
    return dumps(users), 200

@app.route('/users', methods=['POST'])
def add_user():
    user_data = request.json
    existing_user = mongo.db.users.find_one({'username': user_data['username']})
    if existing_user:
        return jsonify({"msg": "Username already exists"}), 400

    user_data['password'] = user_data['password']
    mongo.db.users.insert_one(user_data)
    return jsonify({"msg": "User added successfully"}), 201

@app.route('/login', methods=['POST'])
def login_user():
    try:
        user_data = request.json
        username = user_data.get('username')
        password = user_data.get('password')

        if not username or not password:
            return jsonify({"msg": "Username and password are required"}), 400

        user = mongo.db.users.find_one({'username': username})

        if user:
            if user['password'] ==  password:
                session['username'] = user['username']
                return jsonify({"msg": "Login successful"}), 200
            else:
                return jsonify({"msg": "Invalid username or password"}), 401
        else:
            return jsonify({"msg": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"msg": "Internal server error"}), 500

@app.route('/logout', methods=['POST'])
def logout_user():
    session.pop('username', None)
    return jsonify({"msg": "Logout successful"}), 200

@app.route('/session', methods=['GET'])
def get_session():
    username = session.get('username')
    if username:
        return jsonify({"username": username}), 200
    return jsonify({"msg": "No active session"}), 401

@app.route('/start_voice_assistant', methods=['POST'])
def start_voice_assistant():
    global voice_assistant_process
    try:
        if voice_assistant_process is None or voice_assistant_process.poll() is not None:
            start_voice_assistant_process()
            threading.Thread(target=monitor_voice_assistant).start()
            return jsonify({"status": "Voice assistant started"}), 200
        else:
            return jsonify({"status": "Voice assistant already running"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop_voice_assistant', methods=['POST'])
def stop_voice_assistant():
    global voice_assistant_process
    try:
        if voice_assistant_process is not None:
            os.kill(voice_assistant_process.pid, signal.SIGTERM)
            voice_assistant_process = None
            return jsonify({"status": "Voice assistant stopped"}), 200
        else:
            return jsonify({"status": "Voice assistant not running"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/voice_assistant_status', methods=['GET'])
def voice_assistant_status():
    global voice_assistant_process
    if voice_assistant_process is not None and voice_assistant_process.poll() is None:
        return jsonify({"status": "active"}), 200
    else:
        return jsonify({"status": "inactive"}), 200

def monitor_voice_assistant():
    global voice_assistant_process
    voice_assistant_process.wait()
    voice_assistant_process = None

def start_voice_assistant_process():
    global voice_assistant_process
    voice_assistant_process = subprocess.Popen(['python', 'assistant.py'], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

gesture_control = GestureControl()

@socketio.on('frame')
def handle_frame(data):
    try:
        img_data = base64.b64decode(data['image'])
        np_img = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        mode = data.get('mode')

        if mode == 'handGesture':
            img = gesture_control.process_frame(img)

        elif mode == 'faceRecognition':
            img = process_face_recognition(img, data.get('username'))

        elif mode == 'faceLogin':
            username, img = handle_face_login(img)
            if username:
                user = mongo.db.users.find_one({'username': username})
                emit('face_login_success', {'username': user['username'], 'password': user['password']})
                session['username'] = username
            else:
                emit('face_login_failure')

        _, buffer = cv2.imencode('.jpg', img)
        frame = base64.b64encode(buffer).decode('utf-8')
        emit('response_frame', {'image': frame})

    except Exception as e:
        print(f"Error handling frame: {e}")

@socketio.on('assistant_message')
def handle_assistant_message(data):
    emit('assistant_message', data, broadcast=True)

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    header['Access-Control-Allow-Credentials'] = 'true'
    header['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

if __name__ == '__main__':
    if not os.path.exists(app.config['SESSION_FILE_DIR']):
        os.makedirs(app.config['SESSION_FILE_DIR'])
    socketio.run(app, debug=True)
