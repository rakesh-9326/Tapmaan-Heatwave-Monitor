# Five-minute demonstration (English + Hinglish)

## Before class

Run `python run_web.py` and `python run_desktop.py` in two terminals. Open the local
website. Use Sample data first, so your demo does not depend on the internet.
Check the Tkinter window on your own laptop before the evaluation.

## 0:00–0:40 — Purpose

**English:** “Our project is Tapmaan, a climate and heatwave monitoring prototype.
It displays temperature and humidity, stores weather data and gives early warnings
when forecast temperatures cross our project thresholds. We have built both a
website and a Tkinter desktop interface using a common Python backend.”

**Hinglish:** “Sir, hamara project Tapmaan hai. Isme temperature aur humidity dekh
sakte hain, readings save kar sakte hain aur high temperature ka early warning milta
hai. Website aur Tkinter app dono same Python logic aur SQLite database use karte hain.”

## 0:40–1:30 — Website

Choose Dombivli. Show the source label, current temperature and forecast chart.
Switch Past 24h / Next 24h. Mark one warning reviewed. Change the city to Jaipur.

**English:** “These are clearly labelled sample values, not today's weather. The
24-hour outlook comes from our selected provider. The separate learning model fits
a straight line to recent observations and estimates the next three-hour trend.”

**Hinglish:** “Abhi sample data use ho raha hai. Ye aaj ka live weather nahi hai.
Chart provider ka forecast dikhata hai. Side ka learning model previous observations
se trend calculate karta hai. Dono alag outputs hain.”

## 1:30–2:30 — Prove database connectivity

Add a manual reading, e.g. 42.5°C and 58% humidity. Open Saved readings; show the
Manual label and High risk. Export CSV. In Tkinter choose the same city and click
Reload saved data. Find the same reading there.

**English:** “The same record appears in both interfaces because both use
database/tapmaan.db. We use parameterized INSERT, SELECT, UPDATE and DELETE queries.”

**Hinglish:** “Website se save kiya hua record desktop app mein bhi aa gaya. Isse
prove hota hai ki dono same SQLite database se connected hain.”

## 2:30–3:30 — Tkinter and threading

Show the city selector, table, chart, add form and warning-review button. Choose
live mode and Refresh weather if connected. While fetching, move the window or
switch the table tab to demonstrate that the UI still responds. If the fetch is
fast, explain the worker and queue in source code; do not pretend a delay occurred.

**English:** “The API call runs in threading.Thread. It puts its result into a
queue. Tkinter's after method checks that queue, so all widget updates happen in
the main thread. Each database operation opens its own SQLite connection.”

**Hinglish:** “Network request background thread mein chalti hai. Result queue mein
aata hai aur after callback main thread pe GUI update karta hai. Isliye window
network ka response wait karte time freeze nahi hoti.”

## 3:30–4:30 — OOP and file connections

Open `docs/CODE_GUIDE.md` for exact file names and function line locations. Explain:

- WeatherReading is a data class with validation.
- WeatherProvider is abstract; DemoProvider and OpenMeteoProvider inherit it.
- Both implement fetch(city), demonstrating polymorphism.
- HeatwaveService holds the database and model objects: composition.
- TapmaanApp inherits from tk.Tk.

## 4:30–5:00 — Limits and conclusion

**English:** “The warning thresholds are educational rules, not official IMD
criteria. The regression is a small learning demonstration with no validated
accuracy claim. We can extend the project with better models and official alert
integration after collecting suitable data.”

**Hinglish:** “Sir, warning thresholds project ke rules hain. Hum official IMD
warning ya model ki accuracy ka claim nahi kar rahe. Future mein real historical
data aur better model add kar sakte hain.”

## Suggested responsibility split — assign only after actual work

| Role | Suggested work |
|---|---|
| Person 1 | Website layout, chart, JavaScript API calls |
| Person 2 | Python classes, providers and trend model |
| Person 3 | SQLite schema, SQL and data validation |
| Person 4 | Tkinter interface, threading and integration tests |
| Person 5, if present | Report, test cases and demo coordination |

The uploaded notice specifies 4–5 students within one lab batch. These are suggested
roles, not a record of who actually wrote which code. Use your actual contributions.

## Likely viva questions

**Why SQLite?** It is a small file-based relational database. No separate database
server is needed, and Python supplies sqlite3.

**Is Tkinter inside the website?** No. Tkinter is the separate Python desktop GUI.
The website uses HTML/CSS/JS. They share the backend and database.

**What is an API?** A defined way for components to exchange data. Our frontend
calls local /api routes; OpenMeteoProvider calls the external weather API.

**Where is multithreading?** ThreadingHTTPServer handles web requests in threads;
Tkinter's refresh_async starts a dedicated background thread for weather fetching.

**Where is AI/ML?** LinearTrendModel fits slope and intercept from recent observations
using least squares. Warning classification itself uses explicit rules.

**Why does the model differ from the forecast?** The trend model extrapolates a
short straight-line trend; the provider forecast is a separate time series. Real
temperature has a daily cycle, so the simple model can overshoot.

**What happens offline?** Sample mode still works. Failed live fetching reports an
error and preserves previously saved data.

**What is a foreign key?** readings.city_id refers to cities.id; alerts.reading_id
refers to readings.id. This prevents records referencing missing parent rows.

**What does commit do?** It makes the transaction's changes persistent. A failed
operation rolls back; the connection is closed in finally.
