#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// 1. Setup pins and sensor types
#define DHTPIN 2          // DHT11 data pin is connected to Digital Pin 2
#define DHTTYPE DHT11     // Tell the code we are using a DHT11 sensor
#define MQ135_PIN A0      // MQ-135 analog pin is connected to A0

// 2. Setup safe limits (Thresholds) for studio
float maxTemp = 30.0;     // Warn if temperature goes above 30°C
int maxAir = 400;         // Warn if air quality reading goes above 400

// 3. Initialize LCD (Address 0x27, 16 columns, 2 rows) and DHT sensor
LiquidCrystal_I2C lcd(0x27, 16, 2);
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  lcd.init();             // Start the LCD
  lcd.backlight();        // Turn on the LCD light
  dht.begin();            // Start the DHT11 sensor
  
  // Show welcome message for 2 seconds
  lcd.setCursor(0, 0);
  lcd.print("Studio Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Starting up...");
  delay(2000);
  lcd.clear();
}

void loop() {
  // Read values from both sensors
  float temp = dht.readTemperature();   // Reads Temperature in Celsius
  float hum = dht.readHumidity();       // Reads Humidity in %
  int air = analogRead(MQ135_PIN);      // Reads Air Quality (0 to 1023)

  // Check if DHT11 failed to read
  if (isnan(temp) or isnan(hum)) {
    lcd.setCursor(0, 0);
    lcd.print("DHT11 Error!    ");
    delay(2000);
    return;
  }

  // Show live readings on the LCD
  lcd.setCursor(0, 0);    // Top row
  lcd.print("T:");
  lcd.print(temp, 1);     // 1 decimal place (e.g., 26.5)
  lcd.print("C H:");
  lcd.print((int)hum);    // Whole number (e.g., 55%)
  lcd.print("%  ");

  lcd.setCursor(0, 1);    // Bottom row
  // Check if any reading crosses our safe studio threshold
  if (temp > maxTemp) {
    lcd.print("WARN: HIGH TEMP!");
  } 
  else if (air > maxAir) {
    lcd.print("WARN: POOR AIR! ");
  } 
  else {
    lcd.print("Air:");
    lcd.print(air);
    lcd.print(" [OK]   ");
  }

  delay(2000);            // Wait 2 seconds before updating
}