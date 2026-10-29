
import cv2
import mediapipe as mp
import serial
import time
import threading
import speech_recognition as sr

# Arduino connection
arduino = serial.Serial("COM3", 9600, timeout=1)
time.sleep(2)

command_lock = threading.Lock()
last_command = None

def send_command(command):
    global last_command

    with command_lock:
        if command != last_command:
            arduino.write((command + "\n").encode())
            print("Command sent:", command)
            last_command = command

# Voice control runs in the background
def voice_control():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.8
    recognizer.energy_threshold = 200

    try:
        microphone = sr.Microphone()

        with microphone as source:
            print("Calibrating microphone...")
            recognizer.adjust_for_ambient_noise(source, duration=2)

        print("Voice control ready! Say ON or OFF.")

        while True:
            try:
                with microphone as source:
                    audio = recognizer.listen(
                        source, timeout=1, phrase_time_limit=4
                    )

                text = recognizer.recognize_google(
                    audio, language="en-IN"
                ).lower()

                print("You said:", text)

                if any(word in text.split() for word in ["on", "one"]):
                    send_command("ON")
                elif "off" in text.split():
                    send_command("OFF")

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print("Speech recognition internet error:", e)
                time.sleep(2)

    except Exception as e:
        print("Microphone error:", e)

# Start voice control thread
threading.Thread(target=voice_control, daemon=True).start()

# Hand gesture setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Webcam could not be opened.")
    arduino.close()
    raise SystemExit

print("Gesture control ready!")
print("Thumbs up = ON | Thumbs down = OFF")
print("Press Q to quit.")

gesture_candidate = None
gesture_count = 0
stable_gesture = None

try:
    while True:
        success, frame = cap.read()

        if not success:
            print("Could not read webcam.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        detected_gesture = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                lm = hand_landmarks.landmark

                # Four fingers curled?
                fingers_curled = all(
                    lm[tip].y > lm[pip].y
                    for tip, pip in [
                        (8, 6),    # Index
                        (12, 10),  # Middle
                        (16, 14),  # Ring
                        (20, 18)   # Pinky
                    ]
                )

                thumb_tip_y = lm[4].y
                thumb_joint_y = lm[3].y

                if fingers_curled:
                    if thumb_tip_y < thumb_joint_y:
                        detected_gesture = "ON"
                    elif thumb_tip_y > thumb_joint_y:
                        detected_gesture = "OFF"

                break

        # Require the same gesture for 5 frames
        if detected_gesture is not None:
            if detected_gesture == gesture_candidate:
                gesture_count += 1
            else:
                gesture_candidate = detected_gesture
                gesture_count = 1

            if gesture_count >= 5 and stable_gesture != detected_gesture:
                stable_gesture = detected_gesture
                send_command(detected_gesture)
        else:
            gesture_candidate = None
            gesture_count = 0
            stable_gesture = None

        label = "Show thumbs up/down or speak ON/OFF"
        cv2.putText(
            frame, label, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        cv2.imshow("Hand Gesture + Voice LED Control", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    arduino.close()
    print("Program closed.")
