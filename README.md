# 🌱 TerraDetect – A Smart Agriculture Solution

TerraDetect is a smart farming assistant that combines hardware sensors, machine learning, and a responsive web interface to help farmers make intelligent decisions about crop and fertilizer selection. Designed to support modern agriculture, the system monitors real-time soil conditions and provides actionable insights through a user-friendly web app.

---

## 📁 Project Structure

```
Software/
  backend/      # Flask backend, ML models, data, MongoDB integration
  frontend/     # Static files and HTML templates for the web UI
  render.yaml   # Deployment config
```

---

## 🚀 Features

- 🌾 **Smart Crop & Fertilizer Prediction** using Machine Learning
- 🌡️ **Live Monitoring** of soil moisture, temperature, pH, EC, and NPK via ESP32
- 🧠 **AI-Enabled Recommendations** for optimal agriculture planning
- 🔒 **User & Device Authentication** (MongoDB Atlas)
- 📡 **ThingSpeak Integration** for external sensor data logging
- 💻 **Modern UI** with responsive frontend

---

## 🛠️ Backend Setup

### 1. Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in `backend/` with:
```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority
THINGSPEAK_API_KEY=...
THINGSPEAK_CHANNEL_ID=...
THINGSPEAK_READ_KEY=...
THINGSPEAK_WRITE_KEY=...
```

### 3. Run the Flask Server
```bash
python app.py
```

---

## 🌐 Main API Endpoints

| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| POST   | `/api/register`        | Register a new user                  |
| POST   | `/api/login`           | User login                           |
| GET    | `/api/sensor/latest`   | Get latest sensor data               |
| POST   | `/predict`             | Crop/fertilizer/suitability predict  |

---

## 🧪 Example Sensor Data Payload
```json
{
  "device_id": "A1B2C3",
  "temperature": 27.5,
  "humidity": 68,
  "ph": 6.5,
  "moisture": 55,
  "ec": 1.2,
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

## 💡 Inspiration

TerraDetect is inspired by the need to empower farmers with AI tools that are affordable, practical, and efficient. It bridges the gap between traditional farming and smart agriculture.

---

> **TerraDetect**
