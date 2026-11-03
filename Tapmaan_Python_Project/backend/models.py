"""Data objects and transparent classroom warning thresholds."""
from dataclasses import asdict, dataclass
from datetime import datetime
import math


def risk_level(temperature):
    """Educational thresholds, NOT the official IMD heatwave definition."""
    if temperature >= 45:
        return "Severe"
    if temperature >= 40:
        return "High"
    if temperature >= 35:
        return "Watch"
    return "Normal"


@dataclass
class WeatherReading:
    city_id: str
    recorded_at: str
    temperature: float
    humidity: float
    source: str
    kind: str = "observation"

    def __post_init__(self):
        self.temperature = float(self.temperature)
        self.humidity = float(self.humidity)
        if not math.isfinite(self.temperature) or not -20 <= self.temperature <= 60:
            raise ValueError("Temperature must be between -20 and 60 C.")
        if not math.isfinite(self.humidity) or not 0 <= self.humidity <= 100:
            raise ValueError("Humidity must be between 0 and 100%.")
        moment = datetime.fromisoformat(self.recorded_at)
        if moment.tzinfo is None:
            raise ValueError("Reading time must include its timezone.")
        if self.source not in {"demo", "live", "manual"}:
            raise ValueError("Unknown reading source.")
        if self.kind not in {"observation", "forecast"}:
            raise ValueError("Unknown reading kind.")

    def to_dict(self):
        return {**asdict(self), "risk": risk_level(self.temperature)}
