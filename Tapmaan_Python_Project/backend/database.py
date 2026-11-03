"""SQLite storage. Each operation opens its own thread-safe connection."""
import sqlite3
from contextlib import contextmanager
from .config import CITIES, DB_PATH, ROOT
from .models import risk_level


class Database:
    def __init__(self, path=DB_PATH):
        self.path = path

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript((ROOT / "database/schema.sql").read_text())
            db.executemany(
                "INSERT OR IGNORE INTO cities VALUES (?, ?, ?, ?, ?)",
                [(c["id"], c["name"], c["region"], c["latitude"], c["longitude"]) for c in CITIES],
            )

    def save_many(self, readings):
        ids = []
        with self.connect() as db:
            for reading in readings:
                db.execute(
                    """INSERT INTO readings(city_id, recorded_at, temperature, humidity, source, kind)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(city_id, recorded_at, source, kind) DO UPDATE SET
                    temperature=excluded.temperature, humidity=excluded.humidity""",
                    (reading.city_id, reading.recorded_at, reading.temperature,
                     reading.humidity, reading.source, reading.kind),
                )
                row_id = db.execute(
                    "SELECT id FROM readings WHERE city_id=? AND recorded_at=? AND source=? AND kind=?",
                    (reading.city_id, reading.recorded_at, reading.source, reading.kind),
                ).fetchone()[0]
                level = risk_level(reading.temperature)
                if level in {"High", "Severe"}:
                    db.execute(
                        """INSERT INTO alerts(reading_id, level) VALUES (?, ?)
                        ON CONFLICT(reading_id) DO UPDATE SET level=excluded.level,
                        acknowledged=CASE WHEN alerts.level=excluded.level
                        THEN alerts.acknowledged ELSE 0 END""", (row_id, level),
                    )
                else:
                    db.execute("DELETE FROM alerts WHERE reading_id=?", (row_id,))
                ids.append(row_id)
        return ids

    def readings(self, city_id, source=None, kind=None):
        sql = "SELECT * FROM readings WHERE city_id=?"
        parameters = [city_id]
        if source:
            sql += " AND source=?"
            parameters.append(source)
        if kind:
            sql += " AND kind=?"
            parameters.append(kind)
        sql += " ORDER BY recorded_at, id"
        with self.connect() as db:
            rows = db.execute(sql, parameters).fetchall()
        return [{**dict(row), "risk": risk_level(row["temperature"])} for row in rows]

    def alerts(self, city_id, source, since, until):
        with self.connect() as db:
            rows = db.execute(
                """SELECT a.id, a.level, a.acknowledged, r.temperature,
                r.recorded_at, r.source, r.kind FROM alerts a
                JOIN readings r ON a.reading_id=r.id
                WHERE r.city_id=? AND r.source=? AND r.recorded_at>=? AND r.recorded_at<=?
                ORDER BY r.recorded_at""", (city_id, source, since, until),
            ).fetchall()
        return [dict(row) for row in rows]

    def acknowledge(self, alert_id):
        with self.connect() as db:
            return db.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,)).rowcount > 0

    def delete_manual(self, reading_id):
        with self.connect() as db:
            return db.execute("DELETE FROM readings WHERE id=? AND source='manual'", (reading_id,)).rowcount > 0
