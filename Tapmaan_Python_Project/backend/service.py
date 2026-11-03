"""Business logic shared by both interfaces."""
from datetime import datetime, timedelta
from .config import CITIES, IST
from .database import Database
from .models import WeatherReading
from .predictor import LinearTrendModel
from .providers import DemoProvider, OpenMeteoProvider


class HeatwaveService:
    def __init__(self, database=None):
        self.database = database or Database()
        self.database.initialize()
        self.providers = {"demo": DemoProvider(), "live": OpenMeteoProvider()}
        self.predictor = LinearTrendModel()
        for city in CITIES:
            if not self.database.readings(city["id"], "demo"):
                self.database.save_many(self.providers["demo"].fetch(city))

    def city(self, city_id):
        for city in CITIES:
            if city["id"] == city_id:
                return city
        raise ValueError("Choose one of the supported cities.")

    def refresh(self, city_id, mode):
        if mode not in self.providers:
            raise ValueError("Mode must be demo or live.")
        readings = self.providers[mode].fetch(self.city(city_id))
        self.database.save_many(readings)
        return self.snapshot(city_id, mode)

    def snapshot(self, city_id, mode="demo"):
        city = self.city(city_id)
        if mode not in self.providers:
            raise ValueError("Mode must be demo or live.")
        observations = self.database.readings(city_id, mode, "observation")
        if not observations:
            return {"city": city, "mode": mode, "empty": True,
                    "message": "No live data yet. Select Refresh to fetch Open-Meteo weather."}
        current = observations[-1]
        anchor = datetime.fromisoformat(current["recorded_at"])
        history = [r for r in observations if datetime.fromisoformat(r["recorded_at"]) > anchor - timedelta(hours=24)]
        until = anchor + timedelta(hours=24)
        forecast = [r for r in self.database.readings(city_id, mode, "forecast")
                    if anchor < datetime.fromisoformat(r["recorded_at"]) <= until]
        alerts = self.database.alerts(city_id, mode, anchor.isoformat(), until.isoformat())
        return {"city": city, "mode": mode, "empty": False, "current": current,
                "history": history, "forecast": forecast, "alerts": alerts,
                "prediction": self.predictor.predict(history),
                "stale": mode == "live" and datetime.now(IST) - anchor > timedelta(hours=2),
                "peak": max((r["temperature"] for r in forecast), default=current["temperature"])}

    def add_manual(self, payload):
        city = self.city(payload.get("city_id", ""))
        if "temperature" not in payload or "humidity" not in payload:
            raise ValueError("Temperature and humidity are required.")
        recorded_at = payload.get("recorded_at") or datetime.now(IST).isoformat(timespec="microseconds")
        moment = datetime.fromisoformat(recorded_at)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=IST)
        moment = moment.astimezone(IST)
        if moment > datetime.now(IST) + timedelta(minutes=5):
            raise ValueError("An observation cannot be in the future.")
        reading = WeatherReading(city["id"], moment.isoformat(), payload["temperature"],
                                 payload["humidity"], "manual")
        row_id = self.database.save_many([reading])[0]
        return {"id": row_id, **reading.to_dict()}
