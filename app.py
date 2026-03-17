import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from database import db
from models import User, History
from auth import hash_password, verify_password, create_access_token, token_required
import uuid
from predictor import load_model, predict as run_predict
from flask import send_from_directory

try:
    cnn, svm, class_names, device = load_model()
    print("Model loaded successfully!")
except Exception as e:
    print(f"Model failed to load: {e}")
    cnn, svm, class_names, device = None, None, None, None

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "http://localhost:3000",
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}})
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error: {e}")

@app.route("/")
def root():
    return jsonify({"status": "ok", "message": "Flask API is running"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing email or password"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already registered"}), 400

    new_user = User(
        email=data["email"],
        hashed_password=hash_password(data["password"]),
        name=data.get("name", data["email"].split("@")[0])
    )
    db.session.add(new_user)
    db.session.commit()

    token = create_access_token(new_user.email)
    return jsonify({
        "token": token,
        "user": new_user.to_dict()
    }), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() if request.is_json else request.form
    email = data.get("email") or data.get("username")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        return jsonify({"message": "Invalid email or password"}), 401

    token = create_access_token(user.email)
    return jsonify({
        "token": token,
        "user": user.to_dict()
    })

@app.route("/predict", methods=["POST"])
@token_required
def predict_disease(current_user):
    if cnn is None:
        return jsonify({"message": "Model not loaded"}), 500

    if "image" not in request.files:
        return jsonify({"message": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    try:
        predicted_class, confidence = run_predict(filepath, cnn, svm, class_names, device)

        entry = History(
            user_id=current_user.id,
            image_filename=filename,
            predicted_class=predicted_class,
            confidence=confidence
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify({
            "predicted_class": predicted_class,
            "confidence": round(confidence * 100, 2),
            "image_filename": filename
        })
    except Exception as e:
        return jsonify({"message": f"Prediction failed: {str(e)}"}), 500
    

@app.route("/history", methods=["GET"])
@token_required
def get_history(current_user):
    records = History.query.filter_by(user_id=current_user.id)\
        .order_by(History.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])

@app.route("/history/<int:history_id>", methods=["DELETE"])
@token_required
def delete_history_item(current_user, history_id):
    record = History.query.filter_by(id=history_id, user_id=current_user.id).first()
    if not record:
        return jsonify({"message": "Record not found"}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Deleted successfully"})

@app.route("/history", methods=["DELETE"])
@token_required
def delete_all_history(current_user):
    History.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"message": "All history deleted"})

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"UNCAUGHT ERROR: {e}")
    return jsonify({"message": f"Unhandled error: {str(e)}"}), 500



@app.route("/uploads/<filename>", methods=["GET"])
def get_image(filename):
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    return send_from_directory(upload_dir, filename)

if __name__ == "__main__":
    app.run(debug=True)