def suggest_diet(food_logs, daily_target, bmi=None):
    """
    Generate AI-based diet suggestions based on calorie intake and BMI.
    Args:
        food_logs (list of dict): List of foods eaten today with calorie info.
        daily_target (float): User's daily calorie target.
        bmi (float, optional): User's current Body Mass Index.
    Returns:
        list: List of personalized diet suggestions.
    """

    total_calories = sum([f["calories"] for f in food_logs]) if food_logs else 0
    suggestions = []

    # ========== 🧮 Calorie-Based Suggestions ==========
    if total_calories > daily_target:
        suggestions.append("⚠️ You've exceeded your calorie goal! Try lighter meals tomorrow — include more salads, soups, and boiled foods.")
    elif total_calories < daily_target * 0.8:
        suggestions.append("🍎 You're under your calorie goal. Add fruits, nuts, eggs, and dairy to reach your target.")
    else:
        suggestions.append("✅ Great job! You're maintaining a balanced calorie intake today.")

    # ========== ⚖️ BMI-Based Suggestions ==========
    if bmi is not None:
        if bmi < 18.5:
            suggestions.append("🏋️ You’re underweight (BMI < 18.5). Focus on calorie-dense foods like paneer, avocados, dry fruits, peanut butter, and milk.")
        elif 18.5 <= bmi < 24.9:
            suggestions.append("🌿 You have a healthy BMI. Maintain it with a mix of proteins, fibers, and moderate carbs.")
        elif 25 <= bmi < 29.9:
            suggestions.append("🥗 You're overweight (BMI ≥ 25). Try cutting down sugar, fried foods, and increase daily fiber & protein intake.")
        else:
            suggestions.append("⚠️ You’re obese (BMI ≥ 30). Focus on a low-carb, high-fiber diet with regular exercise — salads, oats, and fruits are ideal.")
    else:
        suggestions.append("💡 Tip: Enter your weight and height to get BMI-based suggestions!")

    # ========== 🥤 Hydration Reminder ==========
    suggestions.append("💧 Drink at least 2–3 liters of water daily for optimal metabolism.")

    return suggestions
# ==============================================
