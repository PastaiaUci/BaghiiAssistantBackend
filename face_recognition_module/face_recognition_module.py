import cv2
import face_recognition
import numpy as np
import base64
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["BaghiiAssistant"]
encodings_collection = db["face_encodings"]
users_collection = db["users"]

def save_face_image_and_encoding(username, encoding, image):
    encoding_list = encoding.tolist()
    encodings_collection.update_one(
        {"username": username},
        {"$set": {"encoding": encoding_list}},
        upsert=True
    )
    
    _, buffer = cv2.imencode('.jpg', image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    users_collection.update_one(
        {"username": username},
        {"$set": {"image": image_base64}},
        upsert=True
    )

def load_face_encodings():
    face_encodings = {}
    for record in encodings_collection.find():
        face_encodings[record["username"]] = np.array(record["encoding"])
    return face_encodings

def process_face_recognition(img, username):
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_img)
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    known_face_encodings = load_face_encodings()
    known_face_names = list(known_face_encodings.keys())
    known_encodings = list(known_face_encodings.values())
    
    print(f"Loaded {len(known_encodings)} known face encodings")
    for i, enc in enumerate(known_encodings):
        print(f"Shape of known encoding {i}: {enc.shape}")
    
    new_user_face_saved = False
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        print(f"Shape of current face encoding: {face_encoding.shape}")
        if face_encoding.shape[0] != 128:
            print("Invalid face encoding shape:", face_encoding.shape)
            continue
        
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"
        
        if len(known_encodings) > 0:
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
            else:
                if not new_user_face_saved:
                    save_face_image_and_encoding(username, face_encoding, img)
                    new_user_face_saved = True
                    name = username
        else:
            if not new_user_face_saved:
                save_face_image_and_encoding(username, face_encoding, img)
                new_user_face_saved = True
                name = username
        
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(img, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    return img

def handle_face_login(img):
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_img)
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    known_face_encodings = load_face_encodings()
    known_face_names = list(known_face_encodings.keys())
    known_encodings = list(known_face_encodings.values())

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        if face_encoding.shape[0] != 128:
            continue

        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        if True in matches:
            best_match_index = matches.index(True)
            username = known_face_names[best_match_index]

            return username, img

    return None, img
