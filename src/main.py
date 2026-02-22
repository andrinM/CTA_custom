from logger import start_logging
from database import init_db

if __name__ == "__main__":
    print("Starting CTA Heat Pump System...")
    init_db()       # Setup the database
    start_logging() # Start the connection