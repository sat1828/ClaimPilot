import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_MOCK_GEOCODES = {
    "miami": {"lat": 25.7617, "lon": -80.1918, "formatted": "Miami, FL, USA"},
    "springfield": {"lat": 42.1015, "lon": -72.5898, "formatted": "Springfield, MA, USA"},
    "denver": {"lat": 39.7392, "lon": -104.9903, "formatted": "Denver, CO, USA"},
    "portland": {"lat": 45.5152, "lon": -122.6784, "formatted": "Portland, OR, USA"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "formatted": "New York, NY, USA"},
    "los angeles": {"lat": 34.0522, "lon": -118.2437, "formatted": "Los Angeles, CA, USA"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "formatted": "Chicago, IL, USA"},
    "houston": {"lat": 29.7604, "lon": -95.3698, "formatted": "Houston, TX, USA"},
}

_MOCK_DISASTERS = {
    "miami": [
        {"type": "Hurricane", "name": "Hurricane Milton", "date": "2024-10-09", "severity": "Major", "description": "Category 3 hurricane making landfall near Miami"},
        {"type": "Flood", "name": "Coastal Flooding", "date": "2024-09-15", "severity": "Moderate", "description": "King tide and storm surge flooding coastal areas"},
    ],
    "denver": [
        {"type": "Hailstorm", "name": "Denver Hail Event", "date": "2024-09-10", "severity": "Severe", "description": "Golf ball-sized hail causing widespread property damage"},
        {"type": "Wildfire", "name": "Front Range Fire", "date": "2024-07-22", "severity": "Major", "description": "Wildfire in Boulder County, air quality affected Denver metro"},
    ],
    "houston": [
        {"type": "Flood", "name": "Tropical Storm Barry", "date": "2024-06-15", "severity": "Major", "description": "Widespread flooding across Harris County"},
        {"type": "Hurricane", "name": "Hurricane Beryl", "date": "2024-07-08", "severity": "Major", "description": "Category 1 hurricane with significant wind and flood damage"},
    ],
    "los angeles": [
        {"type": "Wildfire", "name": "Palisades Fire", "date": "2025-01-07", "severity": "Catastrophic", "description": "Large wildfire in Pacific Palisades area, widespread destruction"},
        {"type": "Earthquake", "name": "Ridgecrest Event", "date": "2024-08-06", "severity": "Moderate", "description": "Magnitude 5.2 earthquake felt across LA basin"},
    ],
}


def get_address_geocode(address: str) -> dict:
    if settings.google_maps_api_key and settings.app_env != "development":
        try:
            import httpx
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": address, "key": settings.google_maps_api_key}
            resp = httpx.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                return {"lat": loc["lat"], "lon": loc["lng"], "formatted": data["results"][0]["formatted_address"]}
        except Exception as e:
            logger.warning(f"Google Maps geocoding failed, using mock: {e}")

    address_lower = address.lower()
    for key, geo in _MOCK_GEOCODES.items():
        if key in address_lower:
            logger.info(f"Geocoded '{address[:50]}' -> {geo['formatted']}")
            return geo

    logger.info(f"Using default geocode for unrecognized address: {address[:50]}")
    return {"lat": 40.7128, "lon": -74.0060, "formatted": address}


def check_disaster_records(location: str, date: str) -> dict:
    location_lower = location.lower()
    disasters = []
    for key, records in _MOCK_DISASTERS.items():
        if key in location_lower or location_lower in key:
            for d in records:
                if not date or d["date"][:7] == date[:7]:
                    disasters.append(d)

    if not disasters:
        logger.info(f"No disaster records found for {location} on {date}")
        return {"location": location, "date": date, "disasters": [], "has_disasters": False}

    logger.info(f"Found {len(disasters)} disaster records for {location}")
    return {"location": location, "date": date, "disasters": disasters, "has_disasters": True}
