import websocket
import time
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime
from database import init_db, insert_log

IP_ADDR = "192.168.1.146"
PW = "999999"
WS_URL = f"ws://{IP_ADDR}:8214"
CSV_FILE = "heatpump_data.csv"

ID_MAP = {}
# Names we are looking for in the pump
TARGET_NAMES = { "Außentemperatur": "Außentemperatur", "Vorlauf": "Vorlauf", "Rücklauf": "Ruecklauf", "Leistung Ist": "Leistung_Ist" }
LAST_SAVED_MINUTE = -1
LAST_MAINTENANCE_DAY = datetime.now().day

def parse_and_save(xml_data):
    global ID_MAP, LAST_SAVED_MINUTE, LAST_MAINTENANCE_DAY
    current_time = datetime.now()
    
    # Check if maintenance is necessary
    if current_time.day != LAST_MAINTENANCE_DAY:
        from database import run_daily_maintenance
        try:
            run_daily_maintenance()
            LAST_MAINTENANCE_DAY = now.day
        except Exception as e:
            print(f"Maintenance Error: {e}")
    
    # THROTTLE: Only proceed if the minute has changed
    if current_time.minute == LAST_SAVED_MINUTE:
        return

    try:
        root = ET.fromstring(xml_data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = {"Timestamp": timestamp}
        found_any_data = False

        # Look through every item in the <values> message
        for item in root.iter('item'):
            idx = item.get("id")
            
            # If this ID is one we "learned" earlier in Phase 2
            if idx in ID_MAP:
                val_text = item.find("value").text
                if val_text:                    
                    # Clean "39.3°C" -> "39.3"
                    clean_val = "".join(c for c in val_text if c.isdigit() or c in ".-")
                    row[ID_MAP[idx]] = float(clean_val)
                    found_any_data = True

        if found_any_data:
            insert_log(row)
            LAST_SAVED_MINUTE = current_minute # Update the throttle
            print(f"[{row['Timestamp']}] Data persisted to SQLite.")
        else:
            print(f"[{timestamp}] Values received, but IDs didn't match our learned map.")

    except Exception as e:
        print(f"Parsing Error: {e}")

def on_message(ws, message):
    global ID_MAP
    
    # PHASE 1: The Menu (First message)
    if message.startswith("<Navigation"):
        print("Menu received. Looking for 'Informationen' folder...")
        nav_root = ET.fromstring(message)
        for item in nav_root.iter('item'):
            name_tag = item.find("name")
            if name_tag is not None and name_tag.text == "Informationen":
                folder_id = item.get("id")
                print(f"Opening folder {folder_id}...")
                ws.send(f"GET;{folder_id}")
                break

    # PHASE 2: The Dictionary (Second message - contains Name + ID)
    elif message.startswith("<Content"):
        print("Dictionary received! Mapping names to IDs...")
        content_root = ET.fromstring(message)
        for item in content_root.iter('item'):
            name_tag = item.find("name")
            if name_tag is not None and name_tag.text:
                clean_name = name_tag.text.strip()
                if clean_name in TARGET_NAMES:
                    idx = item.get("id")
                    ID_MAP[idx] = TARGET_NAMES[clean_name]
                    print(f"-> Learned: {clean_name} is ID {idx}")
        
        # After learning, some pumps need one REFRESH to start the values stream
        ws.send("REFRESH")

    # PHASE 3: The Data Stream (Third and all future messages)
    elif message.startswith("<values"):
        parse_and_save(message)

def on_error(ws, error):
    print("Error: %s", error)

def on_close(ws, close_status_code, close_msg):
    print("Conection closed due to code: %s, wit Message %s", close_status_code, close_msg)
    print("Try again in 30 seconds")
    time.sleep(30)
    start_logging()

def on_open(ws):
    print("Connected to SCTA Heat Pump. Logging in...")
    ws.send(f"LOGIN;{PW}")
    def run():
        time.sleep(2)
        while True:
            ws.send("REFRESH")
            time.sleep(60) # Only log data ever 60 secs
    import _thread
    _thread.start_new_thread(run, ())

def start_logging():
    print(WS_URL)
    ws = websocket.WebSocketApp(
        WS_URL,
        subprotocols=["Lux_WS"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()
