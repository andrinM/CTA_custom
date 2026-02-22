import threading
from logger import start_logging
from database import init_db
from gui import HeatPumpGUI

if __name__ == "__main__":
    print("Starting CTA Heat Pump System...")
    init_db()       # Setup the database
    
    # Start logging in a background thread
    logger_thread = threading.Thread(target=start_logging, daemon=True)
    logger_thread.start()
    
    # Start the GUI in the main thread
    print("Launching GUI...")
    app = HeatPumpGUI()
    app.mainloop()
