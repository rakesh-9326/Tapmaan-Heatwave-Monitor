"""Tkinter desktop app. Network work runs on a worker; GUI updates stay on main thread."""
import csv
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from backend.config import CITIES
from backend.service import HeatwaveService


class TapmaanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tapmaan | Python • Tkinter • SQLite")
        self.geometry("1100x760")
        self.minsize(880, 650)
        self.configure(bg="#f6f5f0")
        self.service = HeatwaveService()
        self.results = queue.Queue()
        self.busy = False
        self.rows = []
        self.city_var = tk.StringVar(value=CITIES[0]["name"])
        self.mode_var = tk.StringVar(value="demo")
        self.status_var = tk.StringVar(value="Ready. Sample data is fictional; live data comes from Open-Meteo.")
        self.summary_var = tk.StringVar()
        self.prediction_var = tk.StringVar()
        self.build_widgets()
        self.load_saved()
        self.after(100, self.check_results)

    def city_id(self):
        return next(city["id"] for city in CITIES if city["name"] == self.city_var.get())

    def build_widgets(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f5f0")
        style.configure("TLabel", background="#f6f5f0", foreground="#354c3b", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=7)
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 10))
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="tapmaan.  /  Climate & heatwave monitor", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(wrap, text="Tkinter desktop companion • shared Python logic and SQLite database").pack(anchor="w", pady=(5, 16))
        controls = ttk.Frame(wrap)
        controls.pack(fill="x")
        self.city_box = ttk.Combobox(controls, textvariable=self.city_var, values=[city["name"] for city in CITIES], state="readonly", width=16)
        self.city_box.pack(side="left", padx=(0, 10))
        self.city_box.bind("<<ComboboxSelected>>", lambda _: self.load_saved())
        self.mode_box = ttk.Combobox(controls, textvariable=self.mode_var, values=["demo", "live"], state="readonly", width=9)
        self.mode_box.pack(side="left", padx=(0, 10))
        self.mode_box.bind("<<ComboboxSelected>>", lambda _: self.load_saved())
        self.refresh_button = ttk.Button(controls, text="Refresh weather", command=self.refresh_async)
        self.refresh_button.pack(side="left", padx=(0, 10))
        ttk.Button(controls, text="Reload saved data", command=self.load_saved).pack(side="left")
        ttk.Button(controls, text="Add reading", command=self.add_dialog).pack(side="right")
        ttk.Label(wrap, textvariable=self.summary_var, font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(18, 4))
        ttk.Label(wrap, textvariable=self.prediction_var).pack(anchor="w", pady=(0, 14))
        self.chart = tk.Canvas(wrap, height=190, bg="#fffefa", highlightthickness=1, highlightbackground="#dce1d1")
        self.chart.pack(fill="x")
        self.chart.bind("<Configure>", lambda _: self.draw_chart())
        self.tabs = ttk.Notebook(wrap)
        self.tabs.pack(fill="both", expand=True, pady=(16, 12))
        readings_frame = ttk.Frame(self.tabs, padding=8)
        alerts_frame = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(readings_frame, text="Saved observations")
        self.tabs.add(alerts_frame, text="Forecast warnings")
        self.readings_tree = self.make_table(readings_frame, ("Time (IST)", "Temp °C", "Humidity %", "Risk", "Source"))
        actions = ttk.Frame(readings_frame)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Export CSV", command=self.export_csv).pack(side="left")
        ttk.Button(actions, text="Delete selected manual entry", command=self.delete_selected).pack(side="left", padx=10)
        self.alerts_tree = self.make_table(alerts_frame, ("Time (IST)", "Temp °C", "Level", "Reviewed"))
        ttk.Button(alerts_frame, text="Mark selected warning reviewed", command=self.acknowledge).pack(anchor="w", pady=(8, 0))
        ttk.Label(wrap, textvariable=self.status_var, wraplength=1000).pack(anchor="w")
        ttk.Label(wrap, text="Educational thresholds: Watch ≥35°C | High ≥40°C | Severe ≥45°C. Not an official heatwave warning.", font=("Segoe UI", 9)).pack(anchor="w", pady=(7, 0))

    def make_table(self, parent, columns):
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        tree = ttk.Treeview(holder, columns=columns, show="headings", height=5, selectmode="browse")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=150 if column == columns[0] else 100, anchor="w")
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def load_saved(self):
        try:
            self.snapshot = self.service.snapshot(self.city_id(), self.mode_var.get())
            self.rows = self.service.database.readings(self.city_id(), kind="observation")
            self.render()
        except Exception as error:
            messagebox.showerror("Unable to load", str(error), parent=self)

    def refresh_async(self):
        if self.busy:
            return
        self.busy = True
        self.refresh_button.configure(state="disabled")
        self.city_box.configure(state="disabled")
        self.mode_box.configure(state="disabled")
        city, mode = self.city_id(), self.mode_var.get()
        self.status_var.set("Fetching weather on a worker thread. You can still use the window.")

        def worker():
            # Do not read/write any Tkinter widget in this background thread.
            try:
                self.service.refresh(city, mode)
                self.results.put(("success", "Weather refreshed and saved."))
            except Exception:
                self.results.put(("error", "Weather fetch failed. Check your connection; saved data is unchanged."))

        threading.Thread(target=worker, daemon=True, name="weather-fetch").start()

    def check_results(self):
        try:
            status, message = self.results.get_nowait()
            self.busy = False
            self.refresh_button.configure(state="normal")
            self.city_box.configure(state="readonly")
            self.mode_box.configure(state="readonly")
            self.load_saved()
            self.status_var.set(message)
            if status == "error":
                messagebox.showerror("Weather unavailable", message, parent=self)
        except queue.Empty:
            pass
        self.after(100, self.check_results)

    def render(self):
        data = self.snapshot
        if data["empty"]:
            self.summary_var.set("No live data yet. Click Refresh weather.")
            self.prediction_var.set("The live fetch needs an internet connection.")
        else:
            current = data["current"]
            self.summary_var.set(f"{data['city']['name']}   {current['temperature']:.1f}°C   |   Humidity {current['humidity']:.1f}%   |   {current['risk']}")
            model = data["prediction"]
            self.prediction_var.set(f"Learning model: {model['temperature']:.1f}°C in 3h, using {model['samples']} observations. Not a validated forecast." if model["available"] else model["reason"])
            self.status_var.set(f"{'FICTIONAL SAMPLE' if data['mode']=='demo' else 'OPEN-METEO'} · Updated {current['recorded_at']}" + (" · STALE: refresh live weather." if data["stale"] else ""))
        for tree in (self.readings_tree, self.alerts_tree):
            for item in tree.get_children():
                tree.delete(item)
        for row in reversed(self.rows):
            self.readings_tree.insert("", "end", iid=str(row["id"]), values=(row["recorded_at"][:16].replace("T", " "), row["temperature"], row["humidity"], row["risk"], row["source"]))
        for alert in data.get("alerts", []):
            self.alerts_tree.insert("", "end", iid=str(alert["id"]), values=(alert["recorded_at"][:16].replace("T", " "), alert["temperature"], alert["level"], "Yes" if alert["acknowledged"] else "No"))
        self.draw_chart()

    def draw_chart(self):
        self.chart.delete("all")
        if not hasattr(self, "snapshot"):
            return
        rows = self.snapshot.get("forecast", [])
        if len(rows) < 2:
            self.chart.create_text(30, 50, text="No forecast to display", anchor="w", fill="#7d8971")
            return
        width = max(500, self.chart.winfo_width())
        low = min(35, min(row["temperature"] for row in rows)) - 2
        high = max(45, max(row["temperature"] for row in rows)) + 2
        x = lambda index: 45 + index * (width - 75) / (len(rows) - 1)
        y = lambda value: 145 - (value - low) / (high - low) * 110
        self.chart.create_text(15, 14, text="NEXT 24 HOURS • °C • IST", anchor="w", fill="#8b977e", font=("Segoe UI", 9))
        for temperature in (30, 35, 40, 45, 50):
            if low <= temperature <= high:
                self.chart.create_line(45, y(temperature), width - 30, y(temperature), fill="#e5e9dd", dash=(4, 3) if temperature == 40 else ())
                self.chart.create_text(25, y(temperature), text=str(temperature), fill="#89977b")
        points = [coordinate for index, row in enumerate(rows) for coordinate in (x(index), y(row["temperature"]))]
        self.chart.create_line(points, fill="#df8954", width=2)
        for index in range(0, len(rows), 4):
            self.chart.create_text(x(index), 167, text=rows[index]["recorded_at"][11:16], fill="#89977b", font=("Segoe UI", 9))

    def add_dialog(self):
        window = tk.Toplevel(self)
        window.title("Add manual reading")
        window.geometry("350x275")
        window.transient(self)
        window.grab_set()
        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=f"New observation · {self.city_var.get()}").pack(anchor="w", pady=(0, 15))
        values = {}
        for label, key in [("Temperature (°C)", "temperature"), ("Humidity (%)", "humidity")]:
            ttk.Label(frame, text=label).pack(anchor="w")
            entry = ttk.Entry(frame)
            entry.pack(fill="x", pady=(4, 10))
            values[key] = entry

        def save():
            try:
                reading = self.service.add_manual({"city_id": self.city_id(), **{key: entry.get() for key, entry in values.items()}})
                window.destroy()
                self.load_saved()
                self.status_var.set(f"Manual reading saved. Temperature level: {reading['risk']}.")
            except (ValueError, TypeError) as error:
                messagebox.showerror("Check your input", str(error), parent=window)

        ttk.Button(frame, text="Save to SQLite", command=save).pack(fill="x", pady=5)

    def delete_selected(self):
        selected = self.readings_tree.selection()
        if not selected:
            return messagebox.showinfo("Select a reading", "Select a manual reading first.", parent=self)
        row = next(row for row in self.rows if str(row["id"]) == selected[0])
        if row["source"] != "manual":
            return messagebox.showinfo("Provider data", "Only manual readings can be deleted.", parent=self)
        if messagebox.askyesno("Delete reading", "Delete this manual reading?", parent=self):
            self.service.database.delete_manual(row["id"])
            self.load_saved()

    def acknowledge(self):
        selected = self.alerts_tree.selection()
        if selected:
            self.service.database.acknowledge(int(selected[0]))
            self.load_saved()

    def export_csv(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=f"tapmaan-{self.city_id()}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["city", "time_IST", "temperature_c", "humidity_percent", "risk", "source"])
                writer.writerows((row["city_id"], row["recorded_at"], row["temperature"], row["humidity"], row["risk"], row["source"]) for row in self.rows)
            self.status_var.set(f"Exported {len(self.rows)} observations.")
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self)
