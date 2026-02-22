import sqlite3

DB_NAME = "heatpump.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                aussentemp REAL,
                vorlauf REAL,
                ruecklauf REAL,
                leistung REAL
            )
        ''')
        conn.commit()

def insert_log(data):
    """Expects a dict with cleaned float values"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (timestamp, aussentemp, vorlauf, ruecklauf, leistung)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get("Timestamp"),
            data.get("Aussentemperatur"),
            data.get("Vorlauf"),
            data.get("Ruecklauf"),
            data.get("Leistung_Ist")
        ))
        conn.commit()

def check_data():
    conn = sqlite3.connect("heatpump.db")
    cursor = conn.cursor()
    
    # Get the last 5 entries
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print(f"{'Timestamp':<20} | {'Aussen':<8} | {'Vorlauf':<8} | {'Ruecklauf':<8}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<20} | {row[1]:<8} | {row[2]:<8} | {row[3]:<8}")
    
    conn.close()

if __name__ == "__main__":
    check_data()