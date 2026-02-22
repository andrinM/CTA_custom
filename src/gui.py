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
        self.val_leistung = self.create_stat_widget("Leistung Ist", "N/A")
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

        self.graph_mode = ctk.StringVar(value="Temperatures") # State variable

        # Add the Dropdown to the Sidebar
        self.lbl_menu = ctk.CTkLabel(self.sidebar, text="View Select", font=("Roboto", 12, "bold"))
        self.lbl_menu.pack(pady=(20, 0))

        self.dropdown = ctk.CTkOptionMenu(
            self.sidebar, 
            values=["Temperatures", "Power & Outside"],
            variable=self.graph_mode,
            command=lambda _: self.refresh_data() # Refresh graph immediately on change
        )
        self.dropdown.pack(pady=10, padx=20)

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
        if not self.winfo_exists(): return

        try:
            conn = sqlite3.connect("file:heatpump.db?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # --- 1. Sidebar Updates (Always show latest) ---
            cursor.execute("SELECT * FROM logs_minute ORDER BY timestamp DESC LIMIT 1")
            last_entry = cursor.fetchone()
            if last_entry:
                self.val_aussen.configure(text=f"{last_entry[1]} °C")
                self.val_vorlauf.configure(text=f"{last_entry[2]} °C")
                self.val_ruecklauf.configure(text=f"{last_entry[3]} °C")
                self.val_leistung.configure(text=f"{last_entry[4]} kW")
                self.val_update.configure(text=f"Last update: {last_entry[0]}")

            # --- 2. Graph Updates based on Dropdown ---
            cursor.execute("SELECT timestamp, aussentemp, vorlauf, ruecklauf, leistung FROM logs_minute ORDER BY timestamp DESC LIMIT 60")
            rows = cursor.fetchall()[::-1]
            
            if rows:
                times = [r[0].split(" ")[1] for r in rows] # HH:MM:SS
                self.ax.clear()
                
                if self.graph_mode.get() == "Temperatures":
                    v_vals = [r[2] for r in rows]
                    r_vals = [r[3] for r in rows]
                    self.ax.plot(times, v_vals, label="Vorlauf", color="#ff4b4b", linewidth=2)
                    self.ax.plot(times, r_vals, label="Rücklauf", color="#4b4bff", linewidth=2)
                    self.ax.set_ylabel("Celsius (°C)", color="white")
                
                else: # Power & Outside Mode
                    o_vals = [r[1] for r in rows]
                    l_vals = [r[4] for r in rows]
                    self.ax.plot(times, o_vals, label="Outside Temp", color="#4bff4b", linewidth=2)
                    self.ax.plot(times, l_vals, label="Leistung (kW)", color="#ffcc00", linewidth=2, linestyle="--")
                    self.ax.set_ylabel("Temp (°C) / Power (kW)", color="white")

                # Formatting the X-Axis
                step = max(1, len(times)//5)
                self.ax.set_xticks(times[::step])
                self.ax.tick_params(axis='x', rotation=45, colors='white')
                self.ax.tick_params(axis='y', colors='white')
                self.ax.legend(facecolor='#2b2b2b', labelcolor='white')
                self.fig.tight_layout()
                self.canvas.draw()

            conn.close()
        except Exception as e:
            print(f"GUI Refresh Error: {e}")
        
        if self.winfo_exists():
            self.after(10000, self.refresh_data)

if __name__ == "__main__":
    app = HeatPumpGUI()
    app.mainloop()