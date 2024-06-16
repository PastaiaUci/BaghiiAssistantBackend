import pyttsx3
import datetime
import speech_recognition as sr
import wikipedia
import webbrowser
import pyjokes
import pywhatkit as kit
import socketio

# Create a Socket.IO client instance
sio = socketio.Client()

# Define event handlers
@sio.event
def connect():
    print('Connection established')
    sio.emit('assistant_message', {'type': 'info', 'text': 'Assistant connected.'})

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.event
def connect_error(data):
    print("The connection failed!")

# Start the TTS engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def speak(audio):
    sio.emit('assistant_message', {'type': 'assistant', 'text': audio})
    engine.say(audio)
    engine.runAndWait()

def wish_time():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 4:
        speak('Hello, at this late hour into the night')
        sio.emit('assistant_message', {'type': 'assistant', 'text': "Hello, at this late hour into the night"})
    elif 4 <= hour < 12:
        speak('Good morning!')
        sio.emit('assistant_message', {'type': 'assistant', 'text': 'Good morning!'})
    elif 12 <= hour < 18:
        speak('Good afternoon!')
        sio.emit('assistant_message', {'type': 'assistant', 'text': 'Good afternoon!'})
    else:
        speak('Good evening!')
        sio.emit('assistant_message', {'type': 'assistant', 'text': 'Good evening!'})

def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening")
        sio.emit('assistant_message', {'type': 'info', 'text': 'Listening...'})
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        speak("Recognizing")
        sio.emit('assistant_message', {'type': 'info', 'text': 'Recognizing...'})
        query = recognizer.recognize_google(audio, language='en-in')
    except Exception as e:
        return "None"
    return query

if __name__ == "__main__":
    # Connect to the Flask server
    sio.connect('http://127.0.0.1:5000')

    wish_time()
    while True:
        query = take_command().lower()
        sio.emit('assistant_message', {'type': 'info', 'text': f'You said {query}'})
        if 'wikipedia' in query:
            speak('Searching Wikipedia...')
            sio.emit('assistant_message', {'type': 'info', 'text': 'Searching Wikipedia...'})
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            sio.emit('assistant_message', {'type': 'info', 'text': 'According to Wikipedia'})
            speak(results)
            sio.emit('assistant_message', {'type': 'info', 'text': results})
        elif 'open youtube' in query:
            webbrowser.open("youtube.com")
        elif 'play' in query:
            song = query.replace('play', '')
            speak('playing ' + song)
            kit.playonyt(song)
        elif 'the time' in query:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            speak(f"Sir, the time is {strTime}")
            sio.emit('assistant_message', {'type': 'info', 'text': f"Sir, the time is {strTime}"})
        elif 'joke' in query:
            joke = pyjokes.get_joke()
            speak(joke)
            sio.emit('assistant_message', {'type': 'info', 'text': joke})
        elif 'exit' in query:
            speak("!Goodbye")
            sio.emit('assistant_message', {'type': 'info', 'text': "!Goodbye"})
            break

    # Disconnect from the server
    sio.disconnect()
