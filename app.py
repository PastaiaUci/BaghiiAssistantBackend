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
import pyautogui
from hand_gesture.hand_track_module import HandDetector
from hand_gesture.gesture_control import GestureControl

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:3000"}})
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")

voice_assistant_process = None
last_known_hand_position = None

app.config["MONGO_URI"] = "mongodb://localhost:27017/YourDatabase"
mongo = PyMongo(app)

detector = HandDetector(maxHands=1)

# USERS ROUTES
@app.route('/users', methods=['GET'])
def get_users():
    users = mongo.db.users.find()
    return jsonify(list(users)), 200

@app.route('/users', methods=['POST'])
def add_user():
    user_data = request.json
    existing_user = mongo.db.users.find_one({'username': user_data['username']})
    if existing_user:
        return jsonify({"msg": "Username already exists"}), 400

    user_data['password'] = generate_password_hash(user_data['password'])
    mongo.db.users.insert_one(user_data)
    return jsonify({"msg": "User added successfully"}), 201

@app.route('/login', methods=['POST'])
def login_user():
    user_data = request.json
    user = mongo.db.users.find_one({'username': user_data['username']})
    if user and check_password_hash(user['password'], user_data['password']):
        session['username'] = user['username']
        return jsonify({"msg": "Login successful"}), 200
    return jsonify({"msg": "Invalid username or password"}), 401

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

# VOICE ASSISTANT ROUTES 
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
            os.kill(voice_assistant_process.pid, signal.CTRL_BREAK_EVENT)
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
    voice_assistant_process = subprocess.Popen(['python', 'voice_assistant/assistant.py'], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

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
        
        _, buffer = cv2.imencode('.jpg', img)
        frame = base64.b64encode(buffer).decode('utf-8')
        emit('response_frame', {'image': frame})

    except Exception as e:
        print(f"Error handling frame: {e}")

if __name__ == '__main__':
    socketio.run(app, debug=True)
