from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.json_util import dumps
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import subprocess

app = Flask(__name__)

CORS(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/virtual_assistant"
mongo = PyMongo(app)

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

    user_data['password'] = generate_password_hash(user_data['password'])
    mongo.db.users.insert_one(user_data)
    return jsonify({"msg": "User added successfully"}), 201

@app.route('/login', methods=['POST'])
def login_user():
    user_data = request.json
    user = mongo.db.users.find_one({'username': user_data['username']})
    if user and check_password_hash(user['password'], user_data['password']):
        return jsonify({"msg": "Login successful"}), 200
    return jsonify({"msg": "Invalid username or password"}), 401

@app.route('/start_voice_assistant', methods=['POST'])
def start_voice_assistant():
    threading.Thread(target=voice_assistant_function).start()
    return jsonify({"status": "Voice assistant started"}), 200

@app.route('/start_hand_gesture', methods=['POST'])
def start_hand_gesture():
    threading.Thread(target=hand_gesture_function).start()
    return jsonify({"status": "Hand gesture recognition started"}), 200

def voice_assistant_function():
    # Your voice assistant code here
    pass

def hand_gesture_function():
    subprocess.run(["python", "hand_mouse/virt_mouse.py"])
    
def voice_assistant_function():
    subprocess.run(["python", "voice_assistant/assistant.py"])

if __name__ == '__main__':
    app.run(debug=True)
