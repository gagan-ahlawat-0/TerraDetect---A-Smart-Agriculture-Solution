# 🌱 TerraDetect – A Smart Agriculture Solution

[![Live](https://img.shields.io/badge/Live-Demo-00C853?style=flat-square&logo=vercel&logoColor=white)](https://terradetect.onrender.com)
[![Built with Flask](https://img.shields.io/badge/Built%20with-Flask-000?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-FFD43B?style=flat-square&logo=python&logoColor=blue)](https://python.org)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32-3C873A?style=flat-square&logo=esphome)](https://www.espressif.com/en/products/socs/esp32)

> 🔗 **Live Demo**: [https://terradetect.onrender.com](https://terradetect.onrender.com)

---

TerraDetect is a smart farming assistant that combines real-time **soil monitoring**, **sensor-based data collection**, and **ML-powered crop & fertilizer recommendations**. It uses ESP32 microcontrollers to gather environmental data and a Flask web app to display and analyze this information.

---

## 🔧 Key Features

### 🌐 Web Dashboard (Flask)
- 📊 Visualize real-time & historical soil data
- 🌾 Crop and fertilizer prediction using ML
- 🌓 Dark mode UI with mobile responsiveness
- 🔒 Secure API endpoints with JWT authentication

### 🔌 IoT Integration (ESP32)
- 📡 WiFiManager for dynamic setup
- 🔐 User-entered 6-character Device ID (stored in EEPROM)
- 📈 HTTPS sensor data uploads with API key validation
- 🌿 Sensor support:
  - Soil pH
  - Moisture
  - Temperature
  - EC (Electrical Conductivity)
  - NPK (via RS485 Modbus)

---

## 📁 Folder Structure

```
TerraDetect/
├── esp32/                # ESP32 firmware & sensor integration
├── static/               # CSS, JS, images
├── templates/            # Jinja2 HTML templates
├── models/               # Crop & fertilizer ML models
├── utils/                # Utility scripts (auth, helpers)
├── app.py                # Flask backend
└── requirements.txt      # Python dependencies
```

---

## 🚀 Getting Started

### 🧰 Requirements
- Python 3.9+
- Flask, scikit-learn, pandas
- ESP32-WROOM-32 (30-pin or 38-pin)
- Arduino IDE / PlatformIO for flashing ESP32

### ⚙️ Setup

```bash
# Clone the repo
git clone https://github.com/gagan-ahlawat-0/TerraDetect---A-Smart-Agriculture-Solution.git
cd TerraDetect---A-Smart-Agriculture-Solution

# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
```

### 📡 Flashing ESP32

- Open `esp32/` code in Arduino IDE
- Upload to ESP32 board
- On first boot:
  - Connect to ESP32 AP
  - Enter WiFi credentials + Device ID

---

## 🔐 Security

- 🔑 HTTPS requests from ESP32 with API key
- 🧠 Device identity stored in EEPROM
- 🔒 JWT tokens for secure API access

---

## 📊 ML Prediction Modules

- **Crop Recommendation**  
  Based on NPK, pH, and other sensor values

- **Fertilizer Suggestion**  
  Trained on real-world datasets to identify soil deficiencies

---

## 🧑‍🌾 Use Cases

- Farmers optimizing fertilizer use
- Students building Agri-IoT projects
- Researchers monitoring field soil health

---

## 🖼️ Preview

![TerraDetect Dashboard](https://github.com/gagan-ahlawat-0/TerraDetect---A-Smart-Agriculture-Solution/blob/main/static/dashboard_darkmode.png)

---

## ⚙️ Tech Stack

| Layer         | Tech Used                       |
|---------------|----------------------------------|
| Frontend      | HTML, CSS, JS, FontAwesome       |
| Backend       | Python, Flask, REST APIs         |
| ML            | Scikit-learn, Pandas, NumPy      |
| IoT Hardware  | ESP32, RS485 NPK, analog sensors |
| Auth & Security | JWT, API keys, EEPROM, HTTPS   |

---

## 📬 Contact

Developed by [**Gagan Ahlawat**](https://github.com/gagan-ahlawat-0) and Team **TerraDetect**
🔗 [https://terradetect.onrender.com](https://terradetect.onrender.com)

Contributions, issues, and feature requests are welcome!

---
