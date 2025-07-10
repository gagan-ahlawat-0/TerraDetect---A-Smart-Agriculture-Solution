#include <WiFi.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <HardwareSerial.h>
#include <ArduinoOTA.h>
#include "esp_task_wdt.h"
#include <WiFiManager.h>
#include <EEPROM.h>
#include <HTTPClient.h>
#include <time.h>
#include <WiFiClientSecure.h>

// WiFi and ThingSpeak settings
// Remove ThingSpeak settings
// const char *write_apiKey = "U8APYGOIS38JY8SU";
// const char *read_apiKey = "ZGSNHEY6VC3URKUH";
// const int channelID = 2899894;

// Sensor Pins
const int pH_sensor_pin = 39;
const int moisture_sensor_pin = 36;
const int Temp_pin = 25;
const int EC_Read = 32;
const int ECPower = 33;
const int LED_PIN = 2;

// RS485 control pins
#define DE_Control 4
#define RE_Control 15

HardwareSerial rs485(1);
OneWire oneWire(Temp_pin);
DallasTemperature sensors(&oneWire);

const int R1 = 1000;
const float Vin = 3.3;
const float K = 0.27;
const float Temp_Coef = 0.019;

float emaPH = 7.0, emaMoisture = 50.0, emaTemp = 25.0, emaEC = 1.0;
float emaN_scaled = 0.0, emaP_scaled = 0.0, emaK_scaled = 0.0;
const float alpha = 0.1;
uint8_t NPK_slave_address = 0x13;

#define DEVICE_ID_LENGTH 7
char device_id[DEVICE_ID_LENGTH] = "000000";

#define API_KEY "8300856b04b7d84043ff65c773ff701ebf8372e0a426e74d1b39c0a0c6646803"

void saveDeviceID(const char *id)
{
  EEPROM.begin(64);
  for (int i = 0; i < DEVICE_ID_LENGTH; i++)
  {
    EEPROM.write(i, id[i]);
  }
  EEPROM.commit();
  EEPROM.end();
}

void loadDeviceID()
{
  EEPROM.begin(64);
  for (int i = 0; i < DEVICE_ID_LENGTH; i++)
  {
    device_id[i] = EEPROM.read(i);
  }
  device_id[DEVICE_ID_LENGTH - 1] = '\0';
  EEPROM.end();
}

bool validateDeviceID(const char* device_id) {
  if (WiFi.status() != WL_CONNECTED) return false;
  HTTPClient http;
  http.begin("https://terradetect.onrender.com/api/check_device_id");
  http.addHeader("Content-Type", "application/json");
  String payload = "{\"device_id\":\"" + String(device_id) + "\"}";
  int httpResponseCode = http.POST(payload);
  String response = http.getString();
  http.end();
  return (httpResponseCode == 200 && response.indexOf("\"registered\":true") != -1);
}

void setupWiFi()
{
  WiFiManager wifiManager;
  WiFiManagerParameter custom_device_id("device_id", "Device ID (6 chars)", device_id, DEVICE_ID_LENGTH);
  wifiManager.addParameter(&custom_device_id);
  wifiManager.autoConnect("TerraDetect-Setup");
  strncpy(device_id, custom_device_id.getValue(), DEVICE_ID_LENGTH);
  device_id[DEVICE_ID_LENGTH - 1] = '\0';
  saveDeviceID(device_id);
  Serial.print("\nConnected to WiFi. Device ID: ");
  Serial.println(device_id);
}

float mapPH(float analogValue)
{
  const float coeffA = -24.71;
  const float coeffB = 195.15;
  float ph = coeffA * log(analogValue) + coeffB;
  return constrain(ph, 0.0, 14.0);
}

float readMoisture()
{
  int moistureValue = analogRead(moisture_sensor_pin);
  float moisturePercentage = map(moistureValue, 2500, 1000, 0, 100);
  return constrain(moisturePercentage, 0, 100);
}

float readTemperature()
{
  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);
  return constrain(temperature, -10.00, 60.00);
}

float readEC(float tempC)
{
  digitalWrite(ECPower, HIGH);
  delay(100);
  int raw = analogRead(EC_Read);
  delay(100);
  raw = analogRead(EC_Read);
  digitalWrite(ECPower, LOW);

  if (raw == 0)
    return 0.00;
  float Vdrop = (Vin * raw) / 4095.0;
  if (Vin - Vdrop == 0)
    return 0.00;
  float Rwater = (Vdrop * R1) / (Vin - Vdrop);
  float ec = 1000 / (Rwater * K);
  float ec25 = ec / (1 + Temp_Coef * (tempC - 25.0));
  return ec25;
}

void readNPK(float &N_scaled, float &P_scaled, float &K_scaled)
{
  uint8_t request[] = {NPK_slave_address, 0x03, 0x00, 0x00, 0x00, 0x06};
  uint16_t crc = calculateCRC(request, 6);
  uint8_t query[8];
  memcpy(query, request, 6);
  query[6] = crc & 0xFF;
  query[7] = (crc >> 8) & 0xFF;

  digitalWrite(DE_Control, HIGH);
  digitalWrite(RE_Control, HIGH);
  delay(2);
  rs485.write(query, 8);
  rs485.flush();
  delay(2);
  digitalWrite(DE_Control, LOW);
  digitalWrite(RE_Control, LOW);
  delay(300);

  if (rs485.available() >= 16)
  {
    uint8_t response[16];
    for (int i = 0; i < 16; i++)
      response[i] = rs485.read();
    int N_raw = (response[9] << 8) | response[10];
    int P_raw = (response[11] << 8) | response[12];
    int K_raw = (response[13] << 8) | response[14];
    N_scaled = (N_raw / 25000.0) * 150.0;
    P_scaled = (P_raw / 8000.0) * 200.0;
    K_scaled = (K_raw / 28000.0) * 240.0;
  }
  else
  {
    N_scaled = P_scaled = K_scaled = -1.0;
  }
  while (rs485.available())
    rs485.read();
}

uint16_t calculateCRC(uint8_t *data, uint8_t length)
{
  uint16_t crc = 0xFFFF;
  for (uint8_t i = 0; i < length; i++)
  {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++)
      crc = (crc >> 1) ^ (crc & 1 ? 0xA001 : 0);
  }
  return crc;
}

float updateEMA(float prev, float curr)
{
  return alpha * curr + (1 - alpha) * prev;
}

// Remove ThingSpeak settings
// void sendToThingSpeak(float pH, float moisture, float temp, float EC, float N, float P, float K)
// {
//   WiFiClient client;
//   if (client.connect("api.thingspeak.com", 80))
//   {
//     String postStr = "api_key=" + String(write_apiKey) + "&field1=" + String(device_id) + "&field2=" + String(pH, 2) + "&field3=" + String(moisture, 1) + "&field4=" + String(temp, 2) + "&field5=" + String(EC, 2) + "&field6=" + String(N, 2) + "&field7=" + String(P, 2) + "&field8=" + String(K, 2);
//     client.println("POST /update HTTP/1.1");
//     client.println("Host: api.thingspeak.com");
//     client.println("Content-Type: application/x-www-form-urlencoded");
//     client.print("Content-Length: ");
//     client.println(postStr.length());
//     client.println("Connection: close");
//     client.println();
//     client.print(postStr);
//     while (client.connected() || client.available())
//       if (client.available())
//         client.readStringUntil('\n');
//     client.stop();
//   }
//   delay(20000);
// }

void sendToServer(float pH, float moisture, float temp, float EC, float N, float P, float K)
{
  const int maxRetries = 3;
  int attempt = 0;
  bool success = false;
  while (attempt < maxRetries && !success)
  {
    if (WiFi.status() == WL_CONNECTED)
    {
      WiFiClientSecure client;
      client.setInsecure();
      HTTPClient http;
      http.begin(client, "https://terradetect.onrender.com/api/esp32");
      http.addHeader("Content-Type", "application/json");
      // Compose JSON payload as expected by backend, including device_id
      String payload = "{";
      payload += "\"device_id\":\"" + String(device_id) + "\",";
      payload += "\"temperature\":" + String(temp, 2) + ",";
      payload += "\"ph\":" + String(pH, 2) + ",";
      payload += "\"humidity\":" + String(moisture, 1) + ","; // Use moisture as humidity if no separate sensor
      payload += "\"moisture\":" + String(moisture, 1) + ",";
      payload += "\"ec\":" + String(EC, 2) + ",";
      payload += "\"N\":" + String(N, 2) + ",";
      payload += "\"P\":" + String(P, 2) + ",";
      payload += "\"K\":" + String(K, 2);
      payload += "}";
      int httpResponseCode = http.POST(payload);
      String response = http.getString();
      Serial.print("Server response: ");
      Serial.println(response);
      http.end();
      if (httpResponseCode > 0 && httpResponseCode < 400)
      {
        success = true;
      }
      else
      {
        Serial.print("HTTP POST failed, code: ");
        Serial.println(httpResponseCode);
        attempt++;
        delay(2000); // Wait 2 seconds before retry
      }
    }
    else
    {
      Serial.println("WiFi not connected, cannot send data.");
      break;
    }
  }
  if (!success)
  {
    Serial.println("Failed to send data to server after multiple attempts.");
  }
}

void setup()
{
  Serial.begin(115200);
  rs485.begin(9600, SERIAL_8N1, 16, 17);
  pinMode(DE_Control, OUTPUT);
  pinMode(RE_Control, OUTPUT);
  digitalWrite(DE_Control, LOW);
  digitalWrite(RE_Control, LOW);
  pinMode(EC_Read, INPUT);
  pinMode(ECPower, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  sensors.begin();
  setupWiFi();

  // Validate device ID with backend before proceeding
  if (!validateDeviceID(device_id)) {
    Serial.println("Device ID not registered. Resetting WiFiManager...");
    WiFiManager wifiManager;
    wifiManager.resetSettings();
    ESP.restart();
  }

  esp_task_wdt_init(10, true);
  esp_task_wdt_add(NULL);

  ArduinoOTA.begin();

  loadDeviceID();
}

void loop()
{
  esp_task_wdt_reset();
  ArduinoOTA.handle();

  digitalWrite(LED_PIN, HIGH);

  emaPH = mapPH(analogRead(pH_sensor_pin));
  emaMoisture = readMoisture();
  emaTemp = readTemperature();
  emaEC = readEC(emaTemp);
  readNPK(emaN_scaled, emaP_scaled, emaK_scaled);

  for (int i = 0; i < 24; i++)
  {
    float pH = mapPH(analogRead(pH_sensor_pin));
    float moisture = readMoisture();
    float temp = readTemperature();
    float ec = readEC(temp);
    float N, P, K;
    readNPK(N, P, K);

    emaPH = updateEMA(emaPH, pH);
    emaMoisture = updateEMA(emaMoisture, moisture);
    emaTemp = updateEMA(emaTemp, temp);
    emaEC = updateEMA(emaEC, ec);
    emaN_scaled = updateEMA(emaN_scaled, N);
    emaP_scaled = updateEMA(emaP_scaled, P);
    emaK_scaled = updateEMA(emaK_scaled, K);

    delay(5000);
    esp_task_wdt_reset();
  }

  // Remove sendToThingSpeak call
  // sendToThingSpeak(emaPH, emaMoisture, emaTemp, emaEC, emaN_scaled, emaP_scaled, emaK_scaled);
  sendToServer(emaPH, emaMoisture, emaTemp, emaEC, emaN_scaled, emaP_scaled, emaK_scaled);
  digitalWrite(LED_PIN, LOW);

  delay(60000); // Wait 1 minute before next reading
}
