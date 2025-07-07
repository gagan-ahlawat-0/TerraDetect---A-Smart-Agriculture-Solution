# 🌱 TerraDetect – A Smart Agriculture Solution

TerraDetect is a smart farming assistant that combines hardware sensors, machine learning, and a responsive web interface to help farmers make intelligent decisions about crop and fertilizer selection. Designed to support modern agriculture, the system monitors real-time soil conditions and provides actionable insights through a user-friendly web app.

---

## 🚀 Features

- 🌾 **Smart Crop & Fertilizer Prediction** using Machine Learning
- 🌡️ **Live Monitoring** of soil moisture, temperature, pH, EC, and NPK via ESP32
- 🧠 **AI-Enabled Recommendations** for optimal agriculture planning
- 🔒 **JWT-based Authentication** for device and user security
- 🌙 **Dark Mode** support for better usability
- 📡 **ThingSpeak Integration** for external sensor data logging
- 💻 **Modern UI** with responsive frontend

---

## 🛠️ Tech Stack

| Layer      | Technologies                                 |
|------------|----------------------------------------------|
| Frontend   | HTML, CSS, JavaScript                        |
| Backend    | Python (Flask), REST API, JWT Auth           |
| Hardware   | ESP32-WROOM-32, DHT, pH, EC, NPK, Moisture   |
| ML Models  | Scikit-learn based Crop & Fertilizer ML      |
| Database   | JSON storage / Future support for MongoDB    |
| External   | ThingSpeak API for IoT integration           |

---

## 📸 Screenshots

_Coming Soon!_

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/gagan-ahlawat-0/TerraDetect---A-Smart-Agriculture-Solution.git
cd TerraDetect---A-Smart-Agriculture-Solution
```

### 2. Install Backend Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Flask Server
```bash
python app.py
```

### 4. Connect Hardware (ESP32)
- Flash ESP32 with the updated Arduino sketch
- Make sure to include `device_id` and remove hardcoded WiFi credentials

---

## 🌐 API Endpoints

| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| POST   | `/api/register-device` | Registers a new hardware device      |
| POST   | `/api/data`            | Accepts sensor data from ESP32       |
| GET    | `/api/crops`           | Predicts crops based on input data   |
| GET    | `/api/fertilizers`     | Recommends fertilizers               |

---

## 🧪 Example ESP32 Data Payload
```json
{
  "device_id": "A1B2C3",
  "temperature": 27.5,
  "humidity": 68,
  "pH": 6.5,
  "moisture": 55,
  "EC": 1.2,
  "N": 90,
  "P": 40,
  "K": 35
}
```

---

## 📦 To-Do

- [ ] Add user dashboard with analytics
- [ ] Integrate MongoDB for data storage
- [ ] Export data reports
- [ ] Add mobile app support

---

## 🙋‍♂️ Author

**Gagan Ahlawat**  
📧 [Email](mailto:cg.ahlawat2036@gmail.com)  
🔗 [GitHub](https://github.com/gagan-ahlawat-0)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 💡 Inspiration

TerraDetect is inspired by the need to empower farmers with AI tools that are affordable, practical, and efficient. It bridges the gap between traditional farming and smart agriculture.

---

> **TerraDetect**
