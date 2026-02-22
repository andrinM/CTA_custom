import customtkinter as ctk
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HeatPumpGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CTA Heat Pump Monitor v1.0")
        self.geometry("1100x600")
        ctk.set_appearance_mode("dark")
        
        # Configure Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Current Values) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.lbl_title = ctk.CTkLabel(self.sidebar, text="Live Status", font=("Roboto", 20, "bold"))
        self.lbl_title.pack(pady=20)

        # Value Displays
        self.val_aussen = self.create_stat_widget("Outside Temp", "N/A")
        self.val_vorlauf = self.create_stat_widget("Vorlauf", "N/A")
        self.val_ruecklauf = self.create_stat_widget("Rücklauf", "N/A")
        self.val_update = ctk.CTkLabel(self.sidebar, text="Last update: --", font=("Roboto", 10))
        self.val_update.pack(side="bottom", pady=10)

        # --- Main Content (Graph Area) ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Placeholder for Graph (using Matplotlib)
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b') # Dark background
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Initial Update
        self.refresh_data()

    def create_stat_widget(self, label_text, initial_val):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.pack(pady=10, padx=20, fill="x")
        
        lbl = ctk.CTkLabel(frame, text=label_text, font=("Roboto", 12))
        lbl.pack(anchor="w")
        
        val_lbl = ctk.CTkLabel(frame, text=initial_val, font=("Roboto", 24, "bold"), text_color="#1f538d")
        val_lbl.pack(anchor="w")
        return val_lbl

    def refresh_data(self):
        try:
            conn = sqlite3.connect("heatpump.db")
            cursor = conn.cursor()
            
            # 1. Fetch Latest Entry for Sidebar
            cursor.execute("SELECT * FROM logs_minute ORDER BY timestamp DESC LIMIT 1")
            last_entry = cursor.fetchone()
            
            if last_entry:
                # Based on your table structure: ts, aussen, vor, rueck, leist
                self.val_aussen.configure(text=f"{last_entry[1]} °C")
                self.val_vorlauf.configure(text=f"{last_entry[2]} °C")
                self.val_ruecklauf.configure(text=f"{last_entry[3]} °C")
                self.val_update.configure(text=f"Last update: {last_entry[0]}")

            # 2. Fetch last 60 mins for Graph
            cursor.execute("SELECT timestamp, vorlauf, ruecklauf FROM logs_minute ORDER BY timestamp DESC LIMIT 60")
            rows = cursor.fetchall()[::-1] # Reverse for time flow
            
            if rows:
                times = [r[0].split(" ")[1] for r in rows] # Just time, not date
                v_vals = [r[1] for r in rows]
                r_vals = [r[2] for r in rows]

                self.ax.clear()
                self.ax.plot(times, v_vals, label="Vorlauf", color="#ff4b4b", linewidth=2)
                self.ax.plot(times, r_vals, label="Rücklauf", color="#4b4bff", linewidth=2)
                self.ax.set_xticks(times[::15]) # Show every 15th label to avoid crowding
                self.ax.legend()
                self.canvas.draw()

            conn.close()
        except Exception as e:
            print(f"GUI Refresh Error: {e}")
        
        # Schedule next refresh in 10 seconds
        self.after(10000, self.refresh_data)

if __name__ == "__main__":
    app = HeatPumpGUI()
    app.mainloop()