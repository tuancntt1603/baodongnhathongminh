/*
 * Smart Home Intrusion Alarm System - Arduino/ESP8266 Firmware
 *
 * Hardware Connections (Recommended for Arduino Uno/Nano):
 * - PIR Motion Sensor:
 *   - VCC -> 5V (or 3.3V for ESP8266)
 *   - GND -> GND
 *   - OUT -> Pin 2 (Interrupt capable)
 * - Magnetic Door Sensor:
 *   - Pin A -> Pin 3 (Internal Pull-Up enabled)
 *   - Pin B -> GND
 *   - Note: Door closed = Switch closed = Pin LOW. Door open = Switch open = Pin HIGH.
 * - Active Buzzer:
 *   - Positive -> Pin 4 (Via 100 ohm resistor if necessary)
 *   - Negative -> GND
 * - Warning LED:
 *   - Anode -> Pin 5 (Via 220 ohm resistor)
 *   - Cathode -> GND
 *
 * Serial Commands (Laptop -> Arduino):
 * - "ARM"     : Turn security mode ON.
 * - "DISARM"  : Turn security mode OFF and silence buzzer/LED.
 * - "STATUS"  : Request current sensor states immediately.
 *
 * Serial Telemetry (Arduino -> Laptop):
 * - "STATUS:ARMED=<0|1>,PIR=<0|1>,DOOR=<0|1>,ALARM=<0|1>" : Periodic state update.
 * - "TRIGGER:PIR"  : Sent immediately when motion triggers the alarm.
 * - "TRIGGER:DOOR" : Sent immediately when door opening triggers the alarm.
 */

// Pin Definitions (Conditional for ESP8266 vs Arduino)
#ifdef ESP8266
  #define PIR_PIN D2    // GPIO4 (Kết nối tới OUT của PIR)
  #define DOOR_PIN D1   // GPIO5 (Kết nối tới một dây cảm biến cửa, dây kia nối GND)
  #define BUZZER_PIN D5 // GPIO14 (Kết nối tới cực dương còi báo)
  #define LED_PIN D6    // GPIO12 (Kết nối tới cực dương LED qua điện trở)
#else
  #define PIR_PIN 2     // Arduino Pin 2
  #define DOOR_PIN 3    // Arduino Pin 3
  #define BUZZER_PIN 4  // Arduino Pin 4
  #define LED_PIN 5     // Arduino Pin 5
#endif

// Buzzer Logic (Change these if your buzzer is Active-LOW or Active-HIGH)
#define BUZZER_ON HIGH
#define BUZZER_OFF LOW

// System State
bool isArmed = false;
bool isAlarmTriggered = false;
String triggerSource = "";

// Sensor States
bool lastPirState = false;
bool lastDoorState = false;

// Timers for non-blocking execution
unsigned long lastStatusTime = 0;
const unsigned long statusInterval = 1000; // Send status every 1 second

// Alarm audio/visual pattern variables
unsigned long lastAlarmPatternTime = 0;
bool alarmPatternState = false;
const unsigned int alarmPatternInterval = 250; // Beep/flash rate (ms)

void setup() {
  Serial.begin(9600);
  
  pinMode(PIR_PIN, INPUT);
  pinMode(DOOR_PIN, INPUT_PULLUP); // Use internal pull-up for door switch
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // ---- TEST CÒI BUZZER KHI VỪA KHỞI ĐỘNG ----
  // digitalWrite(BUZZER_PIN, HIGH);
  // delay(500); // Kêu 0.5 giây
  // digitalWrite(BUZZER_PIN, LOW);
  // -------------------------------------------

  // Turn off alert indicators on startup
  digitalWrite(BUZZER_PIN, BUZZER_OFF);
  digitalWrite(LED_PIN, LOW);

  // Notify laptop that Arduino is ready
  Serial.println("SYSTEM:READY");
}

void loop() {
  // 1. Read Serial commands from Laptop
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "ARM") {
      isArmed = true;
      sendStatus();
    } else if (cmd == "DISARM") {
      isArmed = false;
      isAlarmTriggered = false;
      triggerSource = "";
      // Turn off buzzer and LED immediately
      digitalWrite(BUZZER_PIN, BUZZER_OFF);
      digitalWrite(LED_PIN, LOW);
      sendStatus();
    } else if (cmd == "STATUS") {
      sendStatus();
    }
  }

  // 2. Read Sensors
  // DOOR_PIN is INPUT_PULLUP: LOW = closed, HIGH = open
  bool doorState = digitalRead(DOOR_PIN) == HIGH;
  
  // YÊU CẦU MỚI: Chỉ quét cảm biến chuyển động khi cửa đang mở.
  // Nếu cửa đóng, mặc định coi như không có chuyển động.
  bool pirState = false;
  if (doorState == true) {
    pirState = digitalRead(PIR_PIN) == HIGH; // HIGH = motion detected
  }

  // TÍNH NĂNG AUTO-ARM (Tự động kích hoạt cách 3)
  // Phải đọc trực tiếp cảm biến PIR phần cứng để biết thực sự có người trong phòng hay không
  bool realPir = digitalRead(PIR_PIN) == HIGH;
  static unsigned long lastActivityTime = millis();
  
  // Nếu có người múa trước cảm biến hoặc cửa đang mở -> Reset bộ đếm thời gian
  if (doorState || realPir) {
    lastActivityTime = millis();
  }

  // Nếu đang Tắt (isArmed = false) VÀ đã 15 giây (15000ms) trôi qua không có chuyển động/mở cửa
  // -> TỰ ĐỘNG BẬT! (Để test cho nhanh mình để 15s. Sau khi test ok bạn có thể đổi thành 300000 cho 5 phút)
  if (!isArmed && (millis() - lastActivityTime >= 15000)) {
    isArmed = true;
    sendStatus(); // Gửi trạng thái mới lên Web
  }

  // 3. Alarm Trigger Logic
  if (isArmed) {
    static unsigned long lastTriggerTime = 0;
    unsigned long currentMillis = millis();
    
    // Nếu có chuyển động VÀ cửa đang mở, cứ mỗi 3 giây sẽ gửi lệnh chụp ảnh 1 lần
    if ((pirState && doorState) && (currentMillis - lastTriggerTime >= 3000)) {
      isAlarmTriggered = true;
      lastTriggerTime = currentMillis;
      
      if (pirState) {
        triggerSource = "PIR";
        Serial.println("TRIGGER:PIR");
      } else {
        triggerSource = "DOOR";
        Serial.println("TRIGGER:DOOR");
      }
    }
  }

  // 4. Handle Active Alarm Indicators (Blinking & Beeping)
  if (isAlarmTriggered) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastAlarmPatternTime >= alarmPatternInterval) {
      lastAlarmPatternTime = currentMillis;
      alarmPatternState = !alarmPatternState;
      
      if (alarmPatternState) {
        digitalWrite(BUZZER_PIN, BUZZER_ON);
        digitalWrite(LED_PIN, HIGH);
      } else {
        digitalWrite(BUZZER_PIN, BUZZER_OFF);
        digitalWrite(LED_PIN, LOW);
      }
    }
  } else {
    // If not triggered, ensure alarm outputs are off
    digitalWrite(BUZZER_PIN, BUZZER_OFF);
    digitalWrite(LED_PIN, LOW);
  }

  // 5. Periodic status updates
  unsigned long currentMillis = millis();
  if (currentMillis - lastStatusTime >= statusInterval) {
    lastStatusTime = currentMillis;
    sendStatus();
  }

  // Save states for edge detection
  lastPirState = pirState;
  lastDoorState = doorState;
}

// Helper to compile and send the current system status
void sendStatus() {
  bool pirState = digitalRead(PIR_PIN) == HIGH;
  bool doorState = digitalRead(DOOR_PIN) == HIGH;
  
  Serial.print("STATUS:ARMED=");
  Serial.print(isArmed ? "1" : "0");
  Serial.print(",PIR=");
  Serial.print(pirState ? "1" : "0");
  Serial.print(",DOOR=");
  Serial.print(doorState ? "1" : "0");
  Serial.print(",ALARM=");
  Serial.println(isAlarmTriggered ? "1" : "0");
}
