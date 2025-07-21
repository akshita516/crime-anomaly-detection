from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import time
from routes.auth_utils import login_required
import os
from routes.auth_routes import auth_bp
from routes.news_routes import news_bp
from routes.incident_routes import incident_bp
import pprint

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

mongo = PyMongo(app)
app.mongo = mongo  # ✅ Allows access via current_app.mongo in blueprints

# ✅ Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(news_bp)
app.register_blueprint(incident_bp)

# ✅ Print registered routes AFTER registering blueprints
print("\n✅ Registered Routes:")
pprint.pprint([str(rule) for rule in app.url_map.iter_rules()])
print("\n")

# ✅ Load ML model
model_path = os.path.join("model", "model.keras")
if not os.path.exists(model_path):
    raise FileNotFoundError(f"❌ Model not found at {model_path}")

try:
    model = load_model(model_path)
    print("✅ Model loaded.")
except Exception as e:
    print("❌ Error loading model:", e)
    raise

# ✅ Define Class Labels
class_labels = [
    "Abuse", "Arrest", "Arson", "Assault", "Burglary", "Explosion", "Fighting",
    "Normal", "Accident", "Robbery", "Shooting", "Shoplifting", "Stealing", "Vandalism"
]

def preprocess_image(file):
    try:
        image = Image.open(file).convert("RGB").resize((64, 64))
        image = np.array(image) / 255.0
        return np.expand_dims(image, axis=0)
    except Exception as e:
        print("❌ Preprocessing error:", e)
        return None

# ✅ Routes
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/home")
@login_required
def home():
    news_list = list(app.mongo.db.news.find().sort("timestamp", -1))
    return render_template("homePage.html", news=news_list)

@app.route("/about")
@login_required
def about():
    return render_template("about.html")

@app.route("/status")
@login_required
def status():
    return render_template("crimeStatus.html")

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    start_time = time.time()

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    image = preprocess_image(request.files["file"])
    if image is None:
        return jsonify({"error": "Image preprocessing failed"}), 500

    try:
        prediction = model.predict(image)[0]
        predicted_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))
        predicted_label = class_labels[predicted_index] if predicted_index < len(class_labels) else "Unknown"
    except Exception as e:
        print("❌ Prediction error:", e)
        return jsonify({"error": "Prediction failed"}), 500

    print(f"✅ Prediction done in {time.time() - start_time:.2f} sec")

    return jsonify({
        "prediction": predicted_label,
        "confidence": f"{confidence*100:.2f}%"
    })

if __name__ == "__main__":
    app.run(debug=True)
