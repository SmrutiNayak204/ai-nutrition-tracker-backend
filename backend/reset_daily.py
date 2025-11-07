from datetime import date
from database import get_connection

def reset_daily_calories():
    conn = get_connection()
    c = conn.cursor()

    today = date.today().isoformat()

    c.execute("UPDATE Users SET calories_today = 0, last_logged_date = ? WHERE last_logged_date != ?", (today, today))
    conn.commit()
    conn.close()
    print("✅ Daily calorie data reset successfully.")
# ==============================================
