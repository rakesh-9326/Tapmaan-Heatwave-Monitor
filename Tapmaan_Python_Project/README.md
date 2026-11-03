# Tapmaan — Climate & Heatwave Monitoring

A simple Python mini project with two interfaces: an interactive website and a
Tkinter desktop application. Both use the SAME Python service and SQLite database.

## Start here (Windows / VS Code)

1. Extract the complete ZIP. Do not run files from inside the ZIP.
2. Open the extracted `Tapmaan_Python_Project` folder in VS Code.
3. Open **Terminal → New Terminal** in that folder.
4. Check Python: `python --version` (Python 3.10 or newer).
5. Start the website:

```bash
python run_web.py
```

6. Open **http://127.0.0.1:8000** in Chrome or Edge. Keep the terminal open.
7. Open a second terminal and run the required Tkinter application:

```bash
python run_desktop.py
```

On Windows, `py -3` can replace `python`. The two `.bat` files are shortcuts.
No pip packages, API key, PostgreSQL server or database setup are needed.
SQLite automatically uses `database/tapmaan.db`. A clean sample database is included.

If Tkinter is missing, test with `python -m tkinter`. On Windows, modify the
official Python installation and enable Tcl/Tk. On Ubuntu, install `python3-tk`
using your normal system package manager. Tkinter requires a graphical desktop.

## Important: online preview vs real Python project

The published online page is a clearly labelled interactive SAMPLE PREVIEW.
It stores preview changes in browser localStorage. It cannot run Python,
Tkinter or the local SQLite file. Use this downloaded project for the assessed
demonstration of Python, Tkinter, SQL and multithreading.

The local website is real: JavaScript → Python HTTP API → SQLite. The desktop
app calls the same Python service directly. Entries saved in either interface
appear in the other after clicking Refresh / Reload saved data.

## Features

- Six cities: Dombivli, Mumbai, Pune, Nagpur, New Delhi and Jaipur.
- Clearly labelled fictional sample scenario, fixed at 18 May 2026, noon IST.
- Optional live weather: select **Live weather**, then **Refresh**.
- Current temperature and humidity, hourly chart, next 24-hour outlook.
- A small linear-regression model fitted to the previous six hours; a separate
  three-hour trend projection, not a validated forecast.
- Educational warning levels, reviewable forecast/current high-heat alerts.
- Save, validate, list and delete manual observations; export them as CSV.
- A Tkinter GUI with worker-thread fetching, queue-based results and a table/chart.
- `docs/Project_Report.pdf`, `docs/CODE_GUIDE.md` and `docs/DEMO_GUIDE.md`.

## Files are separated by responsibility

| Folder / file | Responsibility |
|---|---|
| `frontend/index.html` | Website layout, controls and forms |
| `frontend/styles.css` | Responsive website design |
| `frontend/app.js` | API calls, chart, navigation, forms and CSV export |
| `frontend/runtime.js` | Marks this as the real local Python version |
| `backend/server.py` | JSON HTTP endpoints and static frontend serving |
| `backend/service.py` | Shared application logic |
| `backend/models.py` | WeatherReading class, validation and warning thresholds |
| `backend/providers.py` | Abstract provider, demo provider and live API provider |
| `backend/predictor.py` | Simple linear regression |
| `backend/database.py` | SQLite connections and parameterized SQL |
| `backend/config.py` | Cities, paths and IST timezone |
| `database/schema.sql` | Three-table database structure |
| `database/tapmaan.db` | Actual SQLite database file, created if absent |
| `database/example_queries.sql` | Queries to explain to the professor |
| `desktop/app.py` | Tkinter widgets, threading, queue and callbacks |
| `run_web.py`, `run_desktop.py` | Start the two interfaces |
| `tests/test_project.py` | 13 meaningful backend/API tests |

## Source and forecast honesty

Sample values are synthetic, not current weather. Live current/historical values
from Open-Meteo are model-based estimates, not readings from a physical sensor.
Manual, demo and live observations stay separate; forecasts never train the
trend model. Humidity is displayed and stored but is NOT used by the threshold
classifier. The warning levels are classroom rules, NOT official IMD criteria:

| Temperature | Project level |
|---|---|
| Below 35°C | Normal |
| 35°C to below 40°C | Watch |
| 40°C to below 45°C | High |
| 45°C and above | Severe |

High and Severe readings create warning records. The dashboard warning list
shows the selected provider's current-to-next-24-hour window. Reviewing a warning
does not change the weather or the warning level. Manual warnings are reflected
in each saved reading's risk and in SQLite, not mixed into the provider outlook.

This project does not perform long-term climate analysis, send SMS/email, run
unattended monitoring or claim verified prediction accuracy. It is a local
classroom demonstration. The HTTP server binds only to your own computer.

## Tests and verification

```bash
python -m unittest discover -s tests -v
```

13 tests passed during development, covering thresholds, validation, data source
separation, database persistence, concurrent writes, regression, provider parsing,
network failures and real HTTP requests. A live Open-Meteo request also succeeded.
Browser preview: layout, manual save, reload persistence, CSV download and warning
review verified. The Tkinter window could not be visually launched in the build
environment because it has no graphical display; test it on your laptop before
class. Its Python source compiled and its shared backend passed the tests.

## Common issues

- **Page does not open:** keep `run_web.py` running; open the printed URL, not the
  HTML file directly. If port 8000 is busy, use `python run_web.py --port 8001`.
- **Live fetch fails:** check internet, retry, or use Sample data. A failed fetch
  preserves existing rows. The saved timestamp and stale-data banner identify
  older live data.
- **A manual entry is absent from the chart:** this is intentional. Find it under
  Saved readings → Manual only; provider forecasts do not include manual values.
- **Other interface shows old data:** click Reload saved data in Tkinter or Refresh
  on the website; the apps do not push updates to one another automatically.
- **Missing Python:** install Python with Tcl/Tk and the PATH option from python.org.
- **Reset classroom samples:** stop both apps, back up `database/tapmaan.db`, then
  remove that local file and restart. This erases saved manual entries and reviews.

## Assignment checklist

Python OOP, Tkinter GUI, SQLite connectivity, multithreading and a report are
included. The supplied notice requests **4–5 students from the same lab batch**
with the same AI use case; confirm your actual group and fill in the report cover.
The report does not claim that unassigned teammates performed specific work.

References: https://docs.python.org/3/library/tkinter.html,
https://docs.python.org/3/library/sqlite3.html,
https://docs.python.org/3/library/http.server.html,
https://open-meteo.com/en/docs
