# ==============================================
# 🧠 Initial Setup
# ==============================================
from reset_daily import reset_daily_calories
from database import init_db, get_connection
from diet_suggestions import suggest_diet
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import json, os, datetime, sys, hashlib, sqlite3

# Initialize DB and daily reset
init_db()
reset_daily_calories()

# ==============================================
# ⚙️ Flask App Setup
# ==============================================
app = Flask(__name__)
CORS(app)

# If app.py is inside backend/, BASE_DIR will be backend/.
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

# ==============================================
# 📊 Load Nutrition Data
# ==============================================
DATA_PATH = BASE_DIR / "data" / "nutrition_data.json"
if not DATA_PATH.exists():
    raise FileNotFoundError(f"❌ nutrition_data.json not found at {DATA_PATH}")
with open(DATA_PATH, "r") as f:
    nutrition_data = json.load(f)

# ==============================================
# 🧠 Import Prediction Model
# ==============================================
sys.path.append(str(BASE_DIR / "model"))
from predict_food import predict_food

# ==============================================
# 👤 Signup Route (keeps behavior but /register will be main)
# ==============================================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name = data["name"]
    password = data["password"]
    age = int(data["age"])
    height = float(data["height"])
    gender = data["gender"].lower()
    weight = float(data["weight"])

    # ✅ Calculate BMI
    bmi = weight / ((height / 100) ** 2)

    # ✅ Calculate BMR (Mifflin-St Jeor)
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # ✅ Daily calorie target (sedentary lifestyle)
    calorie_target = round(bmr * 1.2, 2)

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO Users (name, age, height, gender, weight, daily_target_calories)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET age=excluded.age, height=excluded.height,
              gender=excluded.gender, weight=excluded.weight, daily_target_calories=excluded.daily_target_calories
        """, (name, age, height, gender, weight, calorie_target))
        conn.commit()
        msg = f"User registered successfully! Your BMI: {bmi:.1f}, Daily Target: {calorie_target} kcal"
    except sqlite3.IntegrityError:
        msg = "User already exists!"
    finally:
        conn.close()

    return jsonify({
        "message": msg,
        "bmi": round(bmi, 1),
        "calorie_target": calorie_target
    })

# ==============================================
# 🔐 Login Route
# ==============================================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    name = data["name"]
    password = data["password"]

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM Users WHERE name=?", (name,))
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful", "name": name})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# ==============================================
# 🧍‍♂️ Register / Upsert Route (used by frontend)
# ==============================================
@app.route("/register", methods=["POST"])
def register():
    """
    Upsert user data: register new or update existing user.
    Returns: message, bmi, calorie_target
    """
    data = request.json
    name = data.get("name")
    try:
        age = int(data.get("age"))
    except (TypeError, ValueError):
        age = None
    try:
        height = float(data.get("height"))
    except (TypeError, ValueError):
        height = None
    try:
        weight = float(data.get("weight"))
    except (TypeError, ValueError):
        weight = None
    gender = (data.get("gender") or "").lower()

    # Compute BMI and calorie target only if height & weight & age & gender present
    bmi = None
    calorie_target = None
    if height and weight and age and gender in ("male", "female"):
        bmi = weight / ((height / 100) ** 2)
        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        calorie_target = round(bmr * 1.2, 2)
    else:
        # Provide sane defaults when not all inputs provided
        calorie_target = 2000 if gender == "male" else 1800 if gender == "female" else 2000

    conn = get_connection()
    c = conn.cursor()
    try:
        # Upsert using ON CONFLICT DO UPDATE (works on modern SQLite)
        c.execute("""
            INSERT INTO Users (name, age, height, gender, weight, daily_target_calories)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                age=excluded.age,
                height=excluded.height,
                gender=excluded.gender,
                weight=excluded.weight,
                daily_target_calories=excluded.daily_target_calories
        """, (name, age, height, gender, weight, calorie_target))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"message": f"Error registering user: {e}"}), 500

    conn.close()
    return jsonify({
        "message": "User registered!",
        "bmi": round(bmi, 1) if bmi is not None else None,
        "calorie_target": calorie_target
    })

# ==============================================
# 📸 Upload & Predict Route
# ==============================================
@app.route("/upload", methods=["POST"])
def upload_file():
    """Upload image, predict food, return nutrition + AI suggestion."""
    try:
        file = request.files["file"]
        name = request.form["name"]
    except Exception as e:
        return jsonify({"error": f"Missing data in request: {e}"}), 400

    # Save file temporarily
    filepath = Path(app.config["UPLOAD_FOLDER"]) / file.filename
    file.save(filepath)

    try:
        predicted_class, confidence = predict_food(str(filepath))
    except Exception as e:
        try:
            os.remove(filepath)
        except Exception:
            pass
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    # Lookup nutrition; handle missing gracefully
    nutrition = nutrition_data.get(predicted_class)
    if not nutrition:
        # Clean up file and return not found
        try:
            os.remove(filepath)
        except Exception:
            pass
        return jsonify({"error": f"Nutrition info for '{predicted_class}' not found in data."}), 404

    # For Salad types stored under "types"
    if predicted_class == "Salad" and "types" in nutrition:
        nutrition_info = nutrition["types"]
    else:
        nutrition_info = nutrition

    conn = get_connection()
    c = conn.cursor()

    # Get user
    c.execute("SELECT id, daily_target_calories, calories_today FROM Users WHERE name=?", (name,))
    user = c.fetchone()
    if not user:
        conn.close()
        try:
            os.remove(filepath)
        except Exception:
            pass
        return jsonify({"error": "User not found"}), 404

    user_id, daily_target, calories_today = user

    # Initialize if null
    if calories_today is None:
        calories_today = 0

    # Add food log: if nutrition_info is a dict with calories, log it
    if isinstance(nutrition_info, dict) and "calories" in nutrition_info:
        try:
            c.execute("""INSERT INTO Food_Log (user_id, date, food_name, calories, protein, fat, carbs, fiber)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (user_id, str(datetime.date.today()), predicted_class,
                       nutrition_info["calories"], nutrition_info.get("protein", 0),
                       nutrition_info.get("fat", 0), nutrition_info.get("carbs", 0), nutrition_info.get("fiber", 0)))
            calories_today += nutrition_info["calories"]
            c.execute("UPDATE Users SET calories_today=?, last_logged_date=? WHERE id=?",
                      (calories_today, str(datetime.date.today()), user_id))
            conn.commit()
        except Exception as e:
            conn.close()
            try:
                os.remove(filepath)
            except Exception:
                pass
            return jsonify({"error": f"Database logging failed: {e}"}), 500
    else:
        # For complex nutrition_info (like Salad types), do not update calories_today automatically
        # You may choose to pick a default type or ask user to choose one in future UI updates.
        pass

    # Fetch weight & height to compute BMI (optional)
    c.execute("SELECT weight, height FROM Users WHERE name=?", (name,))
    weight_height = c.fetchone()
    bmi = None
    if weight_height and all(weight_height):
        weight, height = weight_height
        try:
            bmi = weight / ((height / 100) ** 2)
        except Exception:
            bmi = None

    # Diet suggestion: pass today's total calories (function expects list of dicts)
    suggestions = suggest_diet([{"calories": calories_today}], daily_target, bmi)

    conn.close()

    # Remove uploaded file
    try:
        os.remove(filepath)
    except Exception:
        pass

    return jsonify({
        "predicted_food": predicted_class,
        "confidence": round(confidence * 100, 2),
        "nutrition": nutrition_info,
        "total_calories_today": calories_today,
        "target_exceeded": calories_today > daily_target,
        "suggestions": suggestions
    })

# ==============================================
# 📊 Weekly Data (for Chart.js)
# ==============================================
@app.route("/weekly_data", methods=["GET"])
def weekly_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT date, SUM(calories)
        FROM Food_Log
        WHERE date >= date('now', '-6 day')
        GROUP BY date
        ORDER BY date ASC
    """)
    data = c.fetchall()
    conn.close()

    dates = [d[0] for d in data]
    calories = [d[1] for d in data]
    return jsonify({"dates": dates, "calories": calories})

# ==============================================
# 🚀 Run Flask App
# ==============================================
if __name__ == "__main__":
    print("✅ AI Nutrition Tracker backend running...")
    app.run(debug=True)
# ==============================================
