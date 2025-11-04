# 🧠 AI Nutrition Tracker — Backend

> Backend service for the AI-powered Nutrition Tracker web app.  
> It identifies food from an uploaded image using a trained deep learning model, retrieves nutrition data (calories, protein, fat, carbs, fiber), and tracks daily calorie intake per user.

---

## 🚀 Features
- 🔍 **AI Food Recognition Model** trained using MobileNetV2 (Transfer Learning)
- 🧾 **Nutrition Data Lookup** from `nutrition_data_accurate.json`
- 🍽️ **Daily Calorie Tracking** with automatic reset at midnight
- 👤 **User profile setup** — name, age, gender, height (BMR-based calorie suggestion)
- 💾 **SQLite database integration** for calorie log persistence
- 🔔 **Calorie limit notifications** when daily intake exceeds target
- 🌐 **CORS-enabled Flask API** for frontend communication

---

## 🧩 Tech Stack
- **Language:** Python 3.10+
- **Framework:** Flask
- **AI / ML:** TensorFlow, Keras, MobileNetV2
- **Database:** SQLite3
- **Others:** Flask-CORS, JSON, datetime

---

## 📂 Project Structure
