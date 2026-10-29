
import speech_recognition as sr

r = sr.Recognizer()
r.pause_threshold = 0.8
r.energy_threshold = 200

with sr.Microphone() as source:
    print("Stay quiet for a moment...")
    r.adjust_for_ambient_noise(source, duration=2)
    print("Say: TURN ON THE LIGHT or TURN OFF THE LIGHT")
    try:
        audio = r.listen(source, timeout=10, phrase_time_limit=5)
        print("Processing...")
        text = r.recognize_google(audio, language="en-IN")
        print("Recognized:", text)
    except sr.UnknownValueError:
        print("Could not understand. Speak louder and closer to the mic.")
    except sr.RequestError as e:
        print("Recognition service error:", e)
    except sr.WaitTimeoutError:
        print("No speech detected.")
