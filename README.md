# TerraDetect IoT Platform

## Overview
TerraDetect is a secure, user/device-authenticated IoT agriculture platform. It consists of:
- ESP32-based sensor device (firmware)
- Flask backend (API, authentication, data storage)
- Web frontend (dashboard, history, user management)

## ESP32 Firmware Setup

### Two-Factor Authentication (2FA) with Device ID
- Each ESP32 is provisioned with a unique `PROVISIONED_DEVICE_ID` in the firmware.
- On first boot or reset, the user connects to the ESP32's WiFiManager portal and enters the device ID.
- The device only proceeds if the entered device ID matches the provisioned one **and** is validated by the backend.
- This prevents unauthorized use and device spoofing.

### Flashing and Provisioning
1. Set your unique device ID in the sketch:
   ```cpp
   #define PROVISIONED_DEVICE_ID "YOUR_DEVICE_ID"
   #define API_KEY "YOUR_API_KEY"
   ```
2. Flash the firmware to your ESP32.
3. Power on the device. Connect to the WiFiManager AP (e.g., `TerraDetect-Setup`).
4. Enter WiFi credentials and the device ID when prompted.
5. The device will connect, validate the device ID, and begin sending data to the backend.

### Testing
- Use the Serial Monitor (115200 baud) to view connection, validation, and data transfer logs.
- The device sends simulated sensor data every 60 seconds. Replace with real sensor code as needed.

## Backend API
- `/api/check_device_id` — Validates device ID (POST JSON: `{ "device_id": "..." }`)
- `/api/esp32` — Accepts sensor data (POST JSON, requires `x-api-key` header)

## Security Notes
- Device ID and API key are required for all data submissions.
- Device ID is checked both in firmware and backend for two-factor authentication.
- Never share your API key or provisioned device ID publicly.

## Project Structure
- `backend/` — Flask app, models, requirements
- `frontend/` — Web UI, static assets, templates
- `esp32_terradetect.ino` — Main ESP32 firmware (see above)

## For New Users
1. Obtain a pre-provisioned ESP32 (with device ID and API key).
2. Register on the web app and link your device.
3. Power on the ESP32, connect it to WiFi, and enter the device ID.
4. Use the dashboard and history features to view your device's data.

---
For more details, see code comments and the backend/frontend README files.
