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