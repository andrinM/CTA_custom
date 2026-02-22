import sqlite3
from datetime import datetime, timedelta

DB_NAME = "heatpump.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # High-res table
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs_minute 
                         (timestamp DATETIME, aussentemp REAL, vorlauf REAL, ruecklauf REAL, leistung REAL)''')
        # Low-res table
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs_day 
                         (date DATE PRIMARY KEY, avg_aussen REAL, avg_vorlauf REAL, avg_ruecklauf REAL, max_leistung REAL)''')
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

def run_daily_maintenance():
    """" Add averages and maximums to logs_day. Delete rows from logs_minute that are older than 7 days. """
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Calculate averages and insert into logs_day
        cursor.execute('''
            INSERT INTO logs_day (date, avg_aussen, avg_vorlauf, avg_ruecklauf, max_leistung)
            SELECT DATE(timestamp), AVG(aussentemp), AVG(vorlauf), AVG(ruecklauf), MAX(leistung)
            FROM logs_minute
            WHERE DATE(timestamp) = ?
        ''', (yesterday,))
        
        # Delete entries older than 7 days
        cursor.execute("DELETE FROM logs_minute WHERE timestamp < date('now', '-7 days')")
        
        conn.commit()
        print(f"Maintenance complete: Archived {yesterday} and cleaned old logs.")

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