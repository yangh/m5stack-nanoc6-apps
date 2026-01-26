#include <M5Unified.h>
#include <MFRC522_I2C.h>

MFRC522_I2C mfrc522(0x28, -1);  // 0x28: I2C address of Unit RFID / RFID2; -1: reset pin (not connected)

#define LED_PIN    20
#define ENABLE_PIN 19
#define NUM_LEDS   1
#define GPIO1      1
#define GPIO2      2

void setup() {
  // Initialize NanoC6 and serial communication
  auto cfg = M5.config();
  M5.begin(cfg);

  Serial.begin(115200);

  // Enable I2C GPIO1/2
  Wire.begin(GPIO2, GPIO1);   // SDA, SCL
  delay(100);
  mfrc522.PCD_Init();

  // Enable LED
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH);
  // Set initial LED color to Blue (Standby)
  M5.Led.begin();

  led_standby();
  Serial.println("Ready to scan RFID/NFC cards...");
}

void stamp() {
    // Add timestamp (Milliseconds since boot)
        unsigned long now = millis();
        Serial.print("Now: ");
        Serial.print(now);
        Serial.println(" ms");
}

void led_standby() {
    // Reset to Blue (Standby)
    M5.Led.setBrightness(100);
    M5.Led.setAllColor(0, 0, 255);
}

void led_card_found() {
    // Visual Feedback: Flash Green
    M5.Led.setBrightness(200);
    for(int i=0; i<3; i++) {
        M5.Led.setAllColor(0, 255, 0); // Green
        delay(100);
        M5.Led.setAllColor(0, 0, 0);   // Off
        delay(100);
    }
}

void loop() {
  M5.update();

  // PICC: Proximity Integrated Circuit Card
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    stamp();
    Serial.println("New RFID/NFC card found...");

    uint8_t piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    Serial.print(F("PICC type: "));
    Serial.println(mfrc522.PICC_GetTypeName(piccType));

    // Check if the tag / card is of type MIFARE Classic
    if (piccType != MFRC522_I2C::PICC_TYPE_MIFARE_MINI
        && piccType != MFRC522_I2C::PICC_TYPE_MIFARE_1K
        && piccType != MFRC522_I2C::PICC_TYPE_MIFARE_4K) {
      Serial.println(F("This tag / card is not of type MIFARE Classic.\n"));
      delay(500);
      return;
    }

    // Output the stored UID data
    Serial.print("Card UID: ");
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      Serial.printf("%02X ", mfrc522.uid.uidByte[i]);
    }
    Serial.println("\n");

    led_card_found();
    led_standby();
    delay(500);
  } else {
    delay(500);
  }
} 