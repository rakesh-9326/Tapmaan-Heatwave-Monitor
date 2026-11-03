"""Inheritance and polymorphism: two providers expose the same fetch method."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import math
from urllib.parse import urlencode
from urllib.request import urlopen
from .config import IST
from .models import WeatherReading

DEMO_NOW = datetime(2026, 5, 18, 12, tzinfo=IST)


class WeatherProvider(ABC):
    @abstractmethod
    def fetch(self, city):
        """Return a list of WeatherReading objects."""


class DemoProvider(WeatherProvider):
    def fetch(self, city):
        readings = []
        for hour in range(-23, 25):
            time = DEMO_NOW + timedelta(hours=hour)
            temperature = round(34.5 + 6.5 * math.cos((time.hour - 15) * math.pi / 12)
                                + city["offset"] + max(0, hour) * 0.025, 1)
            humidity = round(max(15, min(90, 65 - (temperature - 28) * 2.3)), 1)
            readings.append(WeatherReading(
                city["id"], time.isoformat(), temperature, humidity,
                "demo", "forecast" if hour > 0 else "observation",
            ))
        return readings


class OpenMeteoProvider(WeatherProvider):
    def fetch(self, city):
        params = urlencode({
            "latitude": city["latitude"], "longitude": city["longitude"],
            "current": "temperature_2m,relative_humidity_2m",
            "hourly": "temperature_2m,relative_humidity_2m",
            "past_days": 1, "forecast_days": 2, "timezone": "Asia/Kolkata",
        })
        with urlopen("https://api.open-meteo.com/v1/forecast?" + params, timeout=15) as response:
            data = json.load(response)
        current = data["current"]
        now = datetime.fromisoformat(current["time"]).replace(tzinfo=IST)
        readings = []
        hourly = data["hourly"]
        for time, temperature, humidity in zip(hourly["time"], hourly["temperature_2m"], hourly["relative_humidity_2m"]):
            moment = datetime.fromisoformat(time).replace(tzinfo=IST)
            if now - timedelta(hours=24) <= moment <= now + timedelta(hours=24):
                if temperature is not None and humidity is not None:
                    readings.append(WeatherReading(city["id"], moment.isoformat(), temperature,
                                                   humidity, "live", "forecast" if moment > now else "observation"))
        readings.append(WeatherReading(city["id"], now.isoformat(),
                                       current["temperature_2m"], current["relative_humidity_2m"], "live"))
        return readings
