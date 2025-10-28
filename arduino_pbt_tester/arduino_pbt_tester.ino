// Arduino PBT Tester - GPIO Control for Arcade Machine
// Handles PIN5_HIGH, PIN6_HIGH commands from Pi for PBT testing
// No PBT sensor reading - just GPIO control for testing

const int LED_PIN = 13;           // Status LED
const int GPIO_PIN6 = 6;          // Arcade motherboard Pin 6 (Press START)
const int GPIO_PIN5 = 5;          // Arcade motherboard Pin 5 (Press ACTIVE)

// GPIO command buffer
String gpioCommand = "";

void setup() {
  Serial.begin(115200);
  
  // Pin setup
  pinMode(LED_PIN, OUTPUT);
  pinMode(GPIO_PIN6, OUTPUT);
  pinMode(GPIO_PIN5, OUTPUT);
  
  // Set initial states
  digitalWrite(LED_PIN, LOW);
  digitalWrite(GPIO_PIN6, LOW);   // Pin 6 normally LOW
  digitalWrite(GPIO_PIN5, HIGH);  // Pin 5 normally HIGH
  
  delay(100);
  
  Serial.println("========================================");
  Serial.println("SICK7 PBT Tester - GPIO Control");
  Serial.println("========================================");
  Serial.println("GPIO: Pin 5 (ACTIVE), Pin 6 (START)");
  Serial.println("Commands: PIN5_HIGH, PIN5_LOW, PIN6_HIGH, PIN6_LOW");
  Serial.println("Ready for PBT testing...");
  Serial.println("========================================");
}

void loop() {
  // Handle GPIO commands from Pi
  handleGPIOCommands();
  
  // Blink LED to show activity
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 1000) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    lastBlink = millis();
  }
}

void handleGPIOCommands() {
  // Read serial commands from Pi
  while (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      processCommand();
      gpioCommand = "";
    } else {
      gpioCommand += c;
    }
  }
}

void processCommand() {
  String command = gpioCommand;
  command.trim();
  
  if (command == "PIN6_HIGH") {
    digitalWrite(GPIO_PIN6, HIGH);
    Serial.println("# GPIO: Pin 6 → HIGH (5V) - START pressed");
    digitalWrite(LED_PIN, HIGH);  // LED on during activity
  } 
  else if (command == "PIN6_LOW") {
    digitalWrite(GPIO_PIN6, LOW);
    Serial.println("# GPIO: Pin 6 → LOW (0V) - START released");
  } 
  else if (command == "PIN5_HIGH") {
    digitalWrite(GPIO_PIN5, HIGH);
    Serial.println("# GPIO: Pin 5 → HIGH (5V) - ACTIVE high");
  } 
  else if (command == "PIN5_LOW") {
    digitalWrite(GPIO_PIN5, LOW);
    Serial.println("# GPIO: Pin 5 → LOW (0V) - ACTIVE pressed");
    digitalWrite(LED_PIN, HIGH);  // LED on during activity
  }
  else if (command == "RESET_GPIO") {
    digitalWrite(GPIO_PIN6, LOW);
    digitalWrite(GPIO_PIN5, HIGH);
    Serial.println("# GPIO: Reset to default states");
  }
  else if (command == "STATUS") {
    Serial.println("# STATUS: Ready for PBT testing");
    Serial.println("# Pin 5 (ACTIVE): " + String(digitalRead(GPIO_PIN5) ? "HIGH" : "LOW"));
    Serial.println("# Pin 6 (START): " + String(digitalRead(GPIO_PIN6) ? "HIGH" : "LOW"));
  }
  else if (command.length() > 0) {
    Serial.println("# UNKNOWN: " + command);
  }
}

// Hardware Setup:
// Arcade Pin 5 ──── Arduino Pin 5 (ACTIVE signal)
// Arcade Pin 6 ──── Arduino Pin 6 (START signal)
// Arcade GND  ──── Arduino GND
//
// This Arduino only handles GPIO control for PBT testing.
// The Pi generates the PBT waveforms and sends GPIO commands.
