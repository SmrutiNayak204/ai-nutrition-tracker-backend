import sqlite3
from pathlib import Path

# Assume this file lives in backend/ — DB will be backend/data/nutrition_tracker.db
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "nutrition_tracker.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1️⃣ Users table
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    height REAL,
                    gender TEXT,
                    weight REAL,
                    daily_target_calories REAL,
                    last_logged_date TEXT DEFAULT CURRENT_DATE,
                    calories_today REAL DEFAULT 0
                )''')

    # 2️⃣ Food_Log table
    c.execute('''CREATE TABLE IF NOT EXISTS Food_Log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    food_name TEXT,
                    calories REAL,
                    protein REAL,
                    fat REAL,
                    carbs REAL,
                    fiber REAL,
                    FOREIGN KEY(user_id) REFERENCES Users(id)
                )''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")

def get_connection():
    # Use a connection per request; default sqlite behavior is fine for your use case
    return sqlite3.connect(DB_PATH)
