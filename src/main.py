import websocket
import time
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime

IP_ADDR = "192.168.1.146"
PW = "999999"
WS_URL = f"ws://{IP_ADDR}:8214"
CSV_FILE = "heatpump_data.csv"

ID_MAP = {}
# Names we are looking for in the pump
TARGET_NAMES = { "Außentemperatur": "Außentemperatur", "Vorlauf": "Vorlauf", "Rücklauf": "Ruecklauf", "Leistung Ist": "Leistung_Ist" }

def parse_and_save(xml_data):
    global ID_MAP
    try:
        root = ET.fromstring(xml_data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = {"Timestamp": timestamp}
        found_any = False 
        for item in root.iter('item'):
            # print(f"ITEM: {item}")
            idx = item.get("id")
            name_tag = item.find("name")
            value_tag = item.find("value")
            # print(f"Found: Nametag: {name_tag}, ValueTag: {value_tag}")

            # --- STEP 1: LEARN THE IDs ---
            # If we see a name, save it to our memory map
            if name_tag is not None and name_tag.text:
                name_text = name_tag.text.strip()
                if name_text in TARGET_NAMES:
                    ID_MAP[idx] = TARGET_NAMES[name_text]
                    print(f"Mapped {name_text} to ID {idx}")
            
            # --- STEP 2: USE THE IDs ---
            # If we have an ID in our memory, extract the value
            if idx in ID_MAP and value_tag is not None and value_tag.text:
                val_text = value_tag.text
                clean_val = "".join(c for c in val_text if c.isdigit() or c in ".-")
                row[ID_MAP[idx]] = clean_val
                found_any = True

        if found_any:
            file_exists = os.path.isfile(CSV_FILE)
            with open(CSV_FILE, "a", newline="") as f:
                fieldnames = ["Timestamp"] + list(TARGET_NAMES.values())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                    writer.writerow(row)
                    print(f"[{timestamp}] Data Logged: {row}")
                    
    except Exception as e: print(f"Parse Error: {e}") 

def on_message(ws, message):
    print(f"Message {message}")
    if message.startswith("<values>"):
        parse_and_save(message)
    elif "<Navigation" in message:
        print("Received Navigation menu. Entering 'Informationen' folder")
        try:
            nav_root = ET.fromstring(message)
            found_id = None

            for item in nav_root.findall(".//item"):
                name_tag = item.find("name")
                if name_tag is not None and name_tag.text == "Informationen":
                    found_id = item.get("id")
                    break
            if found_id:
                print(f"Found 'Informationen' folder at {found_id}. Entering...")
                ws.send(f"GET;{found_id}")
            else:
                print("Could not find 'Informationen' folder. Sending 'REFRESH'")
                ws.send("REFRESH")

        except Exception as e:
            print("Nav Parsing Error: {e}")
            ws.send("REFRESH")

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
            # time.sleep(60) # Only log data ever 60 secs
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

if __name__ == "__main__":
    start_logging()
            