from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import secrets

# Load environment variables from .env (only for local development)
load_dotenv()

app = Flask(
    __name__,
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/static')),
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/templates'))
)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://192.168.223.53:3000"])
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError('SECRET_KEY environment variable not set!')

# Store sensor data per device_id
sensor_data = {}  # device_id -> latest data dict

# Hardcoded valid device IDs (replace with DB or CSV as needed)
VALID_DEVICE_IDS = {"ABC123", "DEF456", "GHI789", "JKL012", "MNO345"}

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['terradetect']
users_col = db['users']
devices_col = db['device_ids']
sensor_data_col = db['sensor_data']

def load_models():
    """Load all required models and data"""
    models = {
        'crop_model': None,
        'fertilizer_model': None,
        'label_encoders': None,
        'fertilizer_details': [],
        'crop_mapping': {},
        'crop_data': None
    }

    try:
        # Load crop recommendation model
        with open(os.path.join(os.path.dirname(__file__), "crop-model.pkl"), "rb") as f:
            models['crop_model'] = pickle.load(f)
        print("Crop recommendation model loaded successfully.")

        # Load fertilizer model and data
        with open(os.path.join(os.path.dirname(__file__), "fertilizer-model.pkl"), "rb") as f:
            data = pickle.load(f)
            models['fertilizer_model'] = data['model']
            models['label_encoders'] = data['label_encoders']
            models['fertilizer_details'] = data['fertilizer_details']
            models['crop_mapping'] = data.get('crop_mapping', {})
        print("Fertilizer recommendation model loaded successfully.")
        
        # Load crop data for suitability calculations
        models['crop_data'] = pd.read_csv(os.path.join(os.path.dirname(__file__), "crop-data.csv"))
        print("Crop data loaded successfully.")
        
    except Exception as e:
        print(f"Error loading models: {e}")
    
    return models

# Load models at startup
models = load_models()

@app.route('/api/esp32', methods=['POST'])
def receive_esp32_data():
    """Endpoint for ESP32 to send sensor data (with API key authorization)"""
    try:
        api_key = request.headers.get('x-api-key')
        data = request.get_json()
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({"error": "Missing device_id"}), 400
        # Validate API key for this device_id
        device = devices_col.find_one({"device_id": device_id})
        if not device or device.get("api_key") != api_key:
            return jsonify({"error": "Unauthorized: Invalid API key for device_id"}), 401
        # Validate required fields
        required_fields = ['temperature', 'ph', 'humidity']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required sensor fields"}), 400
        # Prepare sensor data document
        sensor_doc = {
            'device_id': device_id,
            'temperature': float(data['temperature']),
            'ph': float(data['ph']),
            'humidity': float(data['humidity']),
            'ec': float(data.get('ec', 0)),
            'N': float(data.get('N', 0)),
            'P': float(data.get('P', 0)),
            'K': float(data.get('K', 0)),
            'moisture': float(data.get('moisture', 40)),
            'timestamp': datetime.now()
        }
        result = sensor_data_col.insert_one(sensor_doc)
        print(f"Inserted sensor_doc: {sensor_doc}")
        inserted_doc = sensor_data_col.find_one({'_id': result.inserted_id})
        print(f"Fetched inserted_doc: {inserted_doc}")
        if inserted_doc and '_id' in inserted_doc:
            del inserted_doc['_id']
        if inserted_doc and 'device_id' in inserted_doc:
            del inserted_doc['device_id']
        # Also update in-memory latest for compatibility
        sensor_data[device_id] = {k: v for k, v in sensor_doc.items() if k != 'device_id'}
        response_data = {k: v for k, v in sensor_data[device_id].items() if k != 'timestamp'}
        return jsonify({
            "status": "success",
            "message": "Sensor data received",
            "data": inserted_doc or response_data
        })
    except Exception as e:
        print(f"Error in /api/esp32: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensor/latest', methods=['GET'])
def get_latest_sensor_data():
    """Endpoint to fetch latest sensor data for the logged-in user's device_id from DB"""
    device_id = session.get('device_id')
    if not device_id:
        return jsonify({"error": "No sensor data available for your device"}), 404
    doc = sensor_data_col.find_one({'device_id': device_id}, sort=[('timestamp', -1)])
    if not doc:
        return jsonify({"error": "No sensor data available for your device"}), 404
    # Remove MongoDB _id and device_id from response
    doc.pop('_id', None)
    doc.pop('device_id', None)
    return jsonify({
        "data": {k: v for k, v in doc.items() if k != 'timestamp'},
        "timestamp": doc.get('timestamp', datetime.now().isoformat()),
        "source": "esp32"
    })

@app.route('/api/sensor/history', methods=['GET'])
def get_sensor_history():
    """Endpoint to fetch paginated sensor data for the logged-in user's device_id from DB"""
    device_id = session.get('device_id')
    if not device_id:
        return jsonify({"error": "No sensor data available for your device"}), 404
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1: page = 1
        if per_page < 1: per_page = 10
    except Exception:
        page = 1
        per_page = 10
    skip = (page - 1) * per_page
    total = sensor_data_col.count_documents({'device_id': device_id})
    cursor = sensor_data_col.find({'device_id': device_id}, sort=[('timestamp', -1)]).skip(skip).limit(per_page)
    history = []
    for doc in cursor:
        doc.pop('_id', None)
        doc.pop('device_id', None)
        history.append(doc)
    return jsonify({
        "history": history,
        "total": total,
        "page": page,
        "per_page": per_page
    })

def calculate_suitability(user_input, crop_name):
    """
    Calculate crop suitability and provide soil adjustment recommendations.
    """
    # Find the specific crop's ideal parameters
    crop_info = models['crop_data'][models['crop_data']["label"] == crop_name]

    if crop_info.empty:
        return None, "Crop not found in dataset.", None

    # Extract ideal values
    ideal_values = crop_info.iloc[0][["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]].values.astype(float)
    
    # Calculate percentage suitability
    user_values = np.array(user_input).astype(float)
    deviation = np.abs(user_values - ideal_values)
    max_deviation = ideal_values * 0.2  # 20% deviation tolerance
    suitability_score = (max(0, abs(100 - (np.sum(deviation / max_deviation) * 100 / len(ideal_values)))) ) % 100
    
    # Generate detailed recommendations as structured data for table
    adjustments = []
    param_names = ["Nitrogen (N)", "Phosphorus (P)", "Potassium (K)", "Temperature", "Humidity", "pH", "Rainfall"]
    
    fertilizer_recommendations = {
        "Nitrogen (N)": "Apply nitrogen-rich fertilizers like urea or ammonium sulfate",
        "Phosphorus (P)": "Use phosphorus fertilizers such as bone meal or superphosphate",
        "Potassium (K)": "Add potassium-based fertilizers like potash or wood ash",
        "Temperature": "Use greenhouse techniques or choose planting times strategically",
        "Humidity": "Implement irrigation systems or use mulching techniques",
        "pH": "Add lime to increase pH or sulfur to decrease pH",
        "Rainfall": "Use drip irrigation or rainwater harvesting techniques"
    }
    
    fertilizer_recommendations_2 = {
        "Nitrogen (N)": "Consider soil amendments or drainage improvements.",
        "Phosphorus (P)": "Consider soil amendments or drainage improvements.",
        "Potassium (K)": "Consider soil amendments or drainage improvements.",
        "Temperature": "Use greenhouse techniques or choose planting times strategically",
        "Humidity": "Consider improving ventilation or using humidifiers/dehumidifiers",
        "pH": "Add lime to increase pH or sulfur to decrease pH",
        "Rainfall": "Improve drainage or implement water conservation measures"
    }
    
    table_data = []
    
    for i in range(len(user_values)):
        param_entry = {
            "parameter": param_names[i],
            "recommended": round(ideal_values[i], 2),
            "observed": round(user_values[i], 2),
            "remarks": "Optimal"
        }
        
        if user_values[i] < ideal_values[i] * 0.8:
            shortage = round(ideal_values[i] - user_values[i], 2)
            param_entry["remarks"] = f"Too low. Increase by {shortage}. {fertilizer_recommendations[param_names[i]]}."
            adjustments.append(f"{param_names[i]} is too low (Current: {user_values[i]}, Ideal: {ideal_values[i]}). Increase by {shortage}.")
        elif user_values[i] > ideal_values[i] * 1.2:
            excess = round(user_values[i] - ideal_values[i], 2)
            
            if param_names[i] in ["Humidity", "Rainfall"]:
                param_entry["remarks"] = "Too high."
                adjustments.append(f"{param_names[i]} is too high (Current: {user_values[i]}, Ideal: {ideal_values[i]}).")
            else:
                param_entry["remarks"] = f"Too high. Decrease by {excess}. {fertilizer_recommendations_2[param_names[i]]}"
                adjustments.append(f"{param_names[i]} is too high (Current: {user_values[i]}, Ideal: {ideal_values[i]}). Decrease by {excess}.")
        
        table_data.append(param_entry)

    return round(suitability_score, 2), adjustments, table_data

def predict_fertilizer(soil_data, crop_name):
    """
    Use the trained model to predict fertilizer based on soil and crop parameters.
    """
    if models['fertilizer_model'] is None or models['label_encoders'] is None:
        return {"error": "Fertilizer recommendation model not available."}
    
    try:
        # Prepare input data for the model
        input_data = {
            'Temperature': soil_data.get('temperature', 25),
            'Humidity': soil_data.get('humidity', 50),
            'Moisture': soil_data.get('moisture', 40),
            'Soil': soil_data.get('soil', 'Black'),  # Default to Black if not specified
            'Crop': crop_name or 'Wheat',  # Default to Wheat if not specified
            'Nitrogen': soil_data.get('N', 0),
            'Potassium': soil_data.get('K', 0),
            'Phosphorus': soil_data.get('P', 0)
        }
        
        # Convert to DataFrame for easier processing
        input_df = pd.DataFrame([input_data])
        
        # Apply label encoding to categorical features
        for col, encoder in models['label_encoders'].items():
            if col in input_df.columns:
                # Handle potential unknown categories
                try:
                    input_df[col] = encoder.transform(input_df[col])
                except ValueError:
                    # If category is unknown, use the first category as default
                    print(f"Warning: Unknown category in {col}, using default")
                    input_df[col] = 0
        
        # Make prediction
        fertilizer_name = models['fertilizer_model'].predict(input_df)[0]
        
        # Get composition from fertilizer details
        composition = next((item['composition'] for item in models['fertilizer_details'] 
                           if item['name'] == fertilizer_name), "Varies")
        
        # Generate application advice
        application_advice = generate_application_advice(fertilizer_name, crop_name)
        
        # Calculate soil nutrient deficiencies
        deficiencies = {
            "N": max(0, 50 - soil_data.get('N', 0)),  # Assuming 50 is a good threshold
            "P": max(0, 40 - soil_data.get('P', 0)),  # Assuming 40 is a good threshold
            "K": max(0, 40 - soil_data.get('K', 0))   # Assuming 40 is a good threshold
        }
        
        # Create recommendation result
        recommendation = {
            "fertilizer": fertilizer_name,
            "composition": composition,
            "deficiencies": deficiencies,
            "rationale": "Recommended based on soil and crop requirements",
            "application": application_advice
        }
        
        # Add specific advice for deficient nutrients
        fertilizer_options = {
            "N": ["Urea", "Ammonium Sulfate", "Calcium Nitrate"],
            "P": ["DAP", "Single Super Phosphate", "Rock Phosphate"],
            "K": ["Muriate of Potash", "Sulfate of Potash", "Potassium Nitrate"]
        }
        
        if deficiencies["N"] > 0:
            recommendation["nitrogen_advice"] = f"Add {deficiencies['N']} kg/ha of nitrogen using {fertilizer_options['N'][0]} or similar"
        if deficiencies["P"] > 0:
            recommendation["phosphorus_advice"] = f"Add {deficiencies['P']} kg/ha of phosphorus using {fertilizer_options['P'][0]} or similar"
        if deficiencies["K"] > 0:
            recommendation["potassium_advice"] = f"Add {deficiencies['K']} kg/ha of potassium using {fertilizer_options['K'][0]} or similar"
        
        return recommendation
        
    except Exception as e:
        print(f"Error in model prediction: {e}")
        return {"error": f"Error in fertilizer recommendation: {str(e)}"}

def generate_application_advice(fertilizer, crop_name=None):
    """Generate specific application advice based on fertilizer type and crop"""
    advice = ""
    
    # General application advice
    if "Urea" in fertilizer:
        advice = "Apply in split doses - half at planting and half during vegetative growth"
    elif "DAP" in fertilizer:
        advice = "Best applied at planting time, can be mixed with seeds"
    elif "Potash" in fertilizer:
        advice = "Apply during early growth stages for best results"
    elif "NPK" in fertilizer or "-" in fertilizer:
        advice = "Can be used as basal dose at planting time"
    elif "Super Phosphate" in fertilizer:
        advice = "Apply before planting and incorporate into soil"
    elif "Ammonium" in fertilizer:
        advice = "Apply in moist soil conditions for best results"
    
    # Crop-specific adjustments
    if crop_name:
        if crop_name.lower() in ["rice", "wheat"]:
            advice += ". For cereals, incorporate into soil before planting."
        elif crop_name.lower() in ["vegetables", "tomato", "potato", "carrot", "onion"]:
            advice += ". For vegetables, apply in multiple split doses throughout growth."
        elif crop_name.lower() in ["fruit", "mango", "apple", "banana", "orange"]:
            advice += ". For fruit trees, apply in circular band around drip line."
        elif crop_name.lower() in ["cotton", "sugarcane", "jute"]:
            advice += ". For commercial crops, apply in bands along the rows."
    
    return advice or "Apply according to standard practices for your region."

# Remove generate_api_key and create_device_id functions from this file

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            device_id = request.form.get("device_id", "").strip()
            if authenticate_user(username, password, device_id):
                session["username"] = username
                session["device_id"] = device_id
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid username, password, or device ID. Please try again."
        except Exception as e:
            print("Login error:", e)
            error = "An internal error occurred. Please try again later."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            device_id = request.form.get("device_id", "").strip()
            if not is_valid_device_id(device_id):
                error = "Invalid or already registered Device ID. Please check your device ID."
            else:
                success, err = register_user(username, password, device_id)
                if success:
                    # Fetch the api_key for this device_id
                    device = devices_col.find_one({"device_id": device_id})
                    api_key = device.get("api_key") if device else None
                    return render_template("register_success.html", device_id=device_id, api_key=api_key)
                else:
                    error = f"Registration failed: {err}"
        except Exception as e:
            print("Registration error:", e)
            error = "An internal error occurred. Please try again later."
    return render_template("register.html", error=error)

@app.route("/dashboard")
def dashboard():
    device_id = session.get("device_id")
    if not device_id:
        return redirect(url_for("login"))
    # Only pass this user's device's data
    user_sensor_data = sensor_data.get(device_id, {})
    return render_template("index.html", device_id=device_id, sensor_data=user_sensor_data)

@app.route("/software")
def software_only():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        print("/predict called with data:", data)
        mode = data.get("mode", "crop")
        print("Mode:", mode)
        use_sensor_data = data.get("use_sensor_data", False)
        print("use_sensor_data:", use_sensor_data)

        if use_sensor_data:
            # Try to fetch fresh data from ThingSpeak
            # if not sensor_data or (datetime.now() - datetime.fromisoformat(sensor_data.get('timestamp', '2000-01-01'))).total_seconds() > 300:
            #     fetch_thingspeak_data() # This line is removed
            parameters = [
                sensor_data.get("N", 0),
                sensor_data.get("P", 0),
                sensor_data.get("K", 0),
                sensor_data.get("temperature", 25),
                data.get("humidity", sensor_data.get("humidity", 50)),
                sensor_data.get("ph", 7),
                float(data.get("rainfall", 100))
            ]
            ec_value = sensor_data.get("ec", 0)
        else:
            parameters = [
                float(data.get("N", 0)),
                float(data.get("P", 0)),
                float(data.get("K", 0)),
                float(data.get("temperature", 25)),
                float(data.get("humidity", 50)),
                float(data.get("ph", 7)),
                float(data.get("rainfall", 100))
            ]
            ec_value = float(data.get("ec", 0))
        print("Parameters:", parameters)
        print("EC value:", ec_value)

        if mode == "crop":
            if models['crop_model'] is None:
                print("Crop model not available!")
                return jsonify({"error": "Crop model not available"}), 500
            prediction = models['crop_model'].predict([parameters])[0]
            confidence = models['crop_model'].predict_proba([parameters])[0].max() * 100 if hasattr(models['crop_model'], "predict_proba") else 85
            all_crops = models['crop_data']["label"].unique()
            suitability_scores = []
            for crop in all_crops:
                suitability, _, _ = calculate_suitability(parameters, crop)
                if suitability is not None:
                    suitability_scores.append((crop, suitability))
            if suitability_scores:
                best_crop_by_suitability = max(suitability_scores, key=lambda x: x[1])
            else:
                best_crop_by_suitability = (None, 0)
            print("Prediction:", prediction, "Best by suitability:", best_crop_by_suitability)
            return jsonify({
                "crop": best_crop_by_suitability[0],
                "confidence": round(best_crop_by_suitability[1], 2),
                "crop-predicted": prediction,
                "confidence-predicted": round(confidence, 2)
            })
        elif mode == "suitability":
            crop_name = data.get("crop_name")
            if not crop_name:
                print("No crop name provided!")
                return jsonify({"error": "Crop name is required"}), 400
            suitability, recommendations, table_data = calculate_suitability(parameters, crop_name)
            if suitability is None:
                print("Suitability error:", recommendations)
                return jsonify({"error": recommendations}), 400
            return jsonify({
                "crop": crop_name,
                "suitability": suitability,
                "recommendations": recommendations,
                "table_data": table_data
            })
        elif mode == "fertilizer":
            soil_data = {
                "N": parameters[0],
                "P": parameters[1],
                "K": parameters[2],
                "temperature": parameters[3],
                "humidity": parameters[4],
                "ph": parameters[5],
                "moisture": sensor_data.get("moisture", 40) if use_sensor_data else float(data.get("moisture", 40)),
                "ec": ec_value,
                "soil": data.get("soil", "Black")
            }
            print("Soil data:", soil_data)
            recommendation = predict_fertilizer(soil_data, data.get("crop_name"))
            if "error" in recommendation:
                print("Fertilizer error:", recommendation["error"])
                return jsonify({"error": recommendation["error"]}), 500
            return jsonify(recommendation)
        else:
            print("Invalid mode specified:", mode)
            return jsonify({"error": "Invalid mode specified"}), 400
    except Exception as e:
        print("Exception in /predict:", str(e))
        return jsonify({"error": str(e)}), 500
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

API_KEY = "YOUR_SUPER_SECRET_KEY"

@app.route('/api/device_data', methods=['POST'])
def receive_device_data():
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    device_id = data.get('device_id')
    # TODO: Validate device_id, save to database, etc.
    print(f"Received data from {device_id}: {data}")
    return jsonify({"status": "success"})

@app.route('/api/check_device_id', methods=['POST'])
def check_device_id():
    data = request.get_json()
    device_id = data.get('device_id', '').strip()
    device = devices_col.find_one({"device_id": device_id, "registered": True})
    return jsonify({"registered": bool(device)})

def is_valid_device_id(device_id):
    return devices_col.find_one({"device_id": device_id, "registered": False}) is not None

def register_user(username, password, device_id):
    password_hash = generate_password_hash(password)
    try:
        users_col.insert_one({
            "username": username,
            "password_hash": password_hash,
            "device_id": device_id
        })
        devices_col.update_one({"device_id": device_id}, {"$set": {"registered": True}})
        return True, None
    except Exception as e:
        return False, str(e)

def authenticate_user(username, password, device_id):
    user = users_col.find_one({"username": username, "device_id": device_id})
    if user and check_password_hash(user['password_hash'], password):
        return True
    return False

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        device_id = data.get('device_id', '').strip()
        if not is_valid_device_id(device_id):
            return jsonify({'success': False, 'message': 'Invalid or already registered Device ID'}), 400
        success, err = register_user(username, password, device_id)
        if success:
            return jsonify({'success': True, 'message': 'Registration successful'})
        else:
            return jsonify({'success': False, 'message': f'Registration failed: {err}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Internal server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        device_id = data.get('device_id', '').strip()
        if authenticate_user(username, password, device_id):
            return jsonify({'success': True, 'message': 'Login successful', 'username': username, 'device_id': device_id})
        else:
            return jsonify({'success': False, 'message': 'Invalid username, password, or device ID'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Internal server error: {str(e)}'}), 500

@app.route('/history')
def history_page():
    device_id = session.get('device_id')
    username = session.get('username')
    if not device_id or not username:
        return redirect(url_for('login'))
    return render_template('history.html', device_id=device_id, username=username)

app = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)