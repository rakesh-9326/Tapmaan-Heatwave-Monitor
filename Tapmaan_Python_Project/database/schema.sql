-- SQLite database. The Python backend creates this automatically.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id TEXT NOT NULL REFERENCES cities(id),
    recorded_at TEXT NOT NULL,
    temperature REAL NOT NULL CHECK(temperature BETWEEN -20 AND 60),
    humidity REAL NOT NULL CHECK(humidity BETWEEN 0 AND 100),
    source TEXT NOT NULL CHECK(source IN ('demo', 'live', 'manual')),
    kind TEXT NOT NULL CHECK(kind IN ('observation', 'forecast')),
    UNIQUE(city_id, recorded_at, source, kind)
);
CREATE INDEX IF NOT EXISTS idx_readings_city_time
ON readings(city_id, source, kind, recorded_at);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_id INTEGER NOT NULL UNIQUE REFERENCES readings(id) ON DELETE CASCADE,
    level TEXT NOT NULL CHECK(level IN ('High', 'Severe')),
    acknowledged INTEGER NOT NULL DEFAULT 0 CHECK(acknowledged IN (0, 1))
);
