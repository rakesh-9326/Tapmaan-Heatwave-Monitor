"""Project paths and the small list of supported cities."""
from datetime import timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "tapmaan.db"
IST = timezone(timedelta(hours=5, minutes=30))
CITIES = [
    {"id": "dombivli", "name": "Dombivli", "region": "Maharashtra", "latitude": 19.2183, "longitude": 73.0865, "offset": 0},
    {"id": "mumbai", "name": "Mumbai", "region": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777, "offset": -2.1},
    {"id": "pune", "name": "Pune", "region": "Maharashtra", "latitude": 18.5204, "longitude": 73.8567, "offset": -1.2},
    {"id": "nagpur", "name": "Nagpur", "region": "Maharashtra", "latitude": 21.1458, "longitude": 79.0882, "offset": 3.2},
    {"id": "delhi", "name": "New Delhi", "region": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "offset": 2.2},
    {"id": "jaipur", "name": "Jaipur", "region": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873, "offset": 3.7},
]
