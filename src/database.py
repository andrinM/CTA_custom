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
            data.get("Außentemperatur"),
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
            # Convert each value to a string, use "N/A" if the value is None
            ts = str(row[0])
            at = str(row[1]) if row[1] is not None else "N/A"
            vl = str(row[2]) if row[2] is not None else "N/A"
            rl = str(row[3]) if row[3] is not None else "N/A"
            
            print(f"{ts:<20} | {at:<8} | {vl:<8} | {rl:<8}")
        
    conn.close()

def clear_table():
    conn = sqlite3.connect("heatpump.db")
    cursor = conn.cursor()
    
    # This removes all rows but keeps the table structure
    cursor.execute("DELETE FROM logs")
    
    conn.commit()
    conn.close()
    print("Table 'logs' has been cleared!")

if __name__ == "__main__":
    check_data()