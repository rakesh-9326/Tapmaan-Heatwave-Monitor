"""A tiny linear-regression model, written directly for easy viva explanation."""
from datetime import datetime, timedelta
from .models import risk_level


class LinearTrendModel:
    def predict(self, readings):
        # Observations only, from one source. Do not train on future forecast rows.
        if len(readings) < 3:
            return {"available": False, "reason": "At least 3 observations are needed."}
        latest = datetime.fromisoformat(readings[-1]["recorded_at"])
        points = [r for r in readings if datetime.fromisoformat(r["recorded_at"]) >= latest - timedelta(hours=6)]
        if len(points) < 3:
            return {"available": False, "reason": "Need 3 observations within the last 6 hours."}
        origin = datetime.fromisoformat(points[0]["recorded_at"])
        x = [(datetime.fromisoformat(r["recorded_at"]) - origin).total_seconds() / 3600 for r in points]
        y = [r["temperature"] for r in points]
        x_mean, y_mean = sum(x) / len(x), sum(y) / len(y)
        denominator = sum((value - x_mean) ** 2 for value in x)
        if denominator == 0:
            return {"available": False, "reason": "Observation times must be different."}
        slope = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y)) / denominator
        intercept = y_mean - slope * x_mean
        estimate = round(intercept + slope * (x[-1] + 3), 1)
        return {"available": True, "temperature": estimate, "slope": round(slope, 2),
                "samples": len(points), "risk": risk_level(estimate),
                "for_time": (latest + timedelta(hours=3)).isoformat(),
                "method": "Linear regression on the last 6 hours; 3-hour extrapolation",
                "limitation": "Learning demonstration; no validated forecast accuracy."}
