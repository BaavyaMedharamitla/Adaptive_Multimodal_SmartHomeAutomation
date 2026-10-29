
const int ledPin = 8;
String command = "";

void setup() {
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "ON") {
      digitalWrite(ledPin, HIGH);
      Serial.println("LED ON");
    }
    else if (command == "OFF") {
      digitalWrite(ledPin, LOW);
      Serial.println("LED OFF");
    }
  }
}
