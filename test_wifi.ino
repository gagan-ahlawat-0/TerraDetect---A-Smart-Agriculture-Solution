// test_wifi.ino
// Test ESP32 device_id verification with backend
// Open Serial Monitor at 115200 baud to view output

#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>

// Preload your device_id here (must match what is registered in the backend)
#define DEVICE_ID "123456"  // <-- Replace with your actual device_id

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[Device ID Test] Starting...");

  WiFiManager wifiManager;
  wifiManager.autoConnect("ESP32-DeviceIDTest");

  Serial.println("[Device ID Test] Connected to WiFi!");
  Serial.print("[Device ID Test] IP Address: ");
  Serial.println(WiFi.localIP());

  // Test device_id verification
  if (validateDeviceID(DEVICE_ID)) {
    Serial.println("[Device ID Test] Device ID is registered! Proceeding to normal operation...");
    // You can add your normal operation code here
  } else {
    Serial.println("[Device ID Test] Device ID is NOT registered! Resetting WiFiManager...");
    delay(2000);
    wifiManager.resetSettings();
    ESP.restart();
  }
}

void loop() {
  // Nothing to do in loop
}

bool validateDeviceID(const char* device_id) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[Device ID Test] Not connected to WiFi!");
    return false;
  }
  HTTPClient http;
  http.begin("https://terradetect.onrender.com/api/check_device_id");
  http.addHeader("Content-Type", "application/json");
  String payload = "{\"device_id\":\"" + String(device_id) + "\"}";
  int httpResponseCode = http.POST(payload);
  Serial.print("[Device ID Test] HTTP POST code: ");
  Serial.println(httpResponseCode);
  String response = http.getString();
  Serial.print("[Device ID Test] Response: ");
  Serial.println(response);
  http.end();
  return (httpResponseCode == 200 && response.indexOf("\"registered\":true") != -1);
} 