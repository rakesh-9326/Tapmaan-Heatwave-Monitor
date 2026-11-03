# Code & connection guide

Exact line numbers below refer to this delivered version. They will shift if you edit the files.

## Key connections

| Connection | File and starting line | What to explain |
|---|---|---|
| `async function request` | `frontend/app.js:16` | Frontend sends JSON to Python |
| `async function load` | `frontend/app.js:36` | Loads dashboard and saved observations |
| `def do_GET` | `backend/server.py:25` | Python serves dashboard/readings JSON |
| `def do_POST` | `backend/server.py:46` | Receives save, refresh, review and delete requests |
| `def refresh` | `backend/service.py:26` | Calls the selected provider and saves returned rows |
| `def snapshot` | `backend/service.py:33` | Builds the chart, current data, warnings and model result |
| `def add_manual` | `backend/service.py:54` | Validates and stores a manual entry |
| `def connect` | `backend/database.py:13` | Opens SQLite; commit/rollback and close |
| `def save_many` | `backend/database.py:36` | Parameterized INSERT/UPDATE and warning creation |
| `class WeatherProvider` | `backend/providers.py:14` | Abstract parent class |
| `class OpenMeteoProvider` | `backend/providers.py:35` | External Open-Meteo API request |
| `def predict` | `backend/predictor.py:7` | Linear regression slope/intercept and estimate |
| `def risk_level` | `backend/models.py:7` | Temperature warning boundaries |
| `def refresh_async` | `desktop/app.py:99` | Starts a background weather thread |
| `def check_results` | `desktop/app.py:119` | Queue + after keeps widget updates on the main thread |
| `def add_dialog` | `desktop/app.py:177` | Tkinter data-entry form |
| `CREATE TABLE IF NOT EXISTS readings` | `database/schema.sql:12` | Reading columns, checks, foreign key and unique constraint |

## One save operation, end to end

1. The Add reading form is defined in `frontend/index.html`.
2. Its submit handler in `frontend/app.js` calls `request("/api/readings", payload)`.
3. `RequestHandler.do_POST()` in `backend/server.py` parses JSON.
4. `HeatwaveService.add_manual()` creates and validates a `WeatherReading`.
5. `Database.save_many()` executes parameterized SQL inside a transaction.
6. `json_response()` returns the saved ID and calculated risk to JavaScript.
7. JavaScript reloads Saved readings and shows the new row.
8. Tkinter uses `self.service.add_manual()` directly and skips the HTTP layer.

## HTTP routes

| Method | Route | Action |
|---|---|---|
| GET | `/api/cities` | Supported cities |
| GET | `/api/dashboard?city=dombivli&mode=demo` | Current, history, forecast, warnings, model |
| GET | `/api/readings?city=dombivli` | All observation sources for one city |
| POST | `/api/refresh` | Fetch selected provider and persist rows |
| POST | `/api/readings` | Add a manual observation |
| POST | `/api/acknowledge` | Save reviewed state for a warning |
| POST | `/api/delete-reading` | Delete an existing manual observation |

## OOP concepts

| Concept | Concrete example |
|---|---|
| Class and object | `WeatherReading(...)`, `Database(...)`, `HeatwaveService(...)` |
| Encapsulation | SQL is kept inside `Database`; interfaces use its methods |
| Abstraction | `WeatherProvider` defines the required `fetch` interface |
| Inheritance | `DemoProvider(WeatherProvider)`, `OpenMeteoProvider(WeatherProvider)`, `TapmaanApp(tk.Tk)` |
| Polymorphism | `self.providers[mode].fetch(city)` calls the selected implementation |
| Composition | `HeatwaveService` contains a database, providers and a model |
| Exception handling | Input validation, network errors and transaction rollback |

## Database relationships

`cities.id` (one) → `readings.city_id` (many).

`readings.id` (one) → `alerts.reading_id` (zero or one). A warning is created only for High/Severe values.

Readings have a unique key on city + time + source + kind, so repeated refreshes do not duplicate a reading. Source and kind keep fictional data, live estimates, manual observations and forecasts distinct.

## Short Hinglish explanation

Frontend ka `fetch` local Python API ko request bhejta hai. `server.py` request receive karke `service.py` ko call karta hai. Service validation aur logic chalati hai, phir `database.py` SQLite mein query execute karta hai. Result JSON mein frontend ko milta hai. Tkinter same service ko direct call karta hai.
