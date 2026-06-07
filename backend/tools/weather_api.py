import logging
from datetime import datetime
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_MOCK_WEATHER = {
    "2024-03-15": {"condition": "Rain", "temp": 58.3, "humidity": 82, "wind_speed": 12.4, "precipitation": 0.45, "description": "Moderate rain with overcast skies"},
    "2024-06-20": {"condition": "Clear", "temp": 78.5, "humidity": 45, "wind_speed": 5.2, "precipitation": 0.0, "description": "Sunny and clear"},
    "2024-09-10": {"condition": "Cloudy", "temp": 65.2, "humidity": 68, "wind_speed": 8.1, "precipitation": 0.05, "description": "Overcast with light drizzle"},
    "2024-01-15": {"condition": "Snow", "temp": 28.4, "humidity": 75, "wind_speed": 15.3, "precipitation": 2.1, "description": "Heavy snowfall, reduced visibility"},
    "2024-07-04": {"condition": "Clear", "temp": 92.1, "humidity": 35, "wind_speed": 3.8, "precipitation": 0.0, "description": "Hot and dry"},
    "2024-11-28": {"condition": "Rain", "temp": 42.7, "humidity": 88, "wind_speed": 18.6, "precipitation": 1.2, "description": "Heavy rain with strong winds"},
    "2024-05-01": {"condition": "Partly Cloudy", "temp": 68.9, "humidity": 55, "wind_speed": 6.7, "precipitation": 0.0, "description": "Mild with partial cloud cover"},
    "2025-01-01": {"condition": "Clear", "temp": 35.2, "humidity": 40, "wind_speed": 4.1, "precipitation": 0.0, "description": "Cold and clear"},
}

_DEFAULT_WEATHER = {"condition": "Unknown", "temp": 60.0, "humidity": 50, "wind_speed": 5.0, "precipitation": 0.0, "description": "Weather data unavailable for this date"}


def get_weather_on_date(lat: float, lon: float, date: str) -> dict:
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    else:
        date = date[:10]

    if settings.openweathermap_api_key and settings.app_env != "development":
        try:
            import httpx
            url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine"
            params = {"lat": lat, "lon": lon, "dt": int(datetime.strptime(date, "%Y-%m-%d").timestamp()), "appid": settings.openweathermap_api_key, "units": "imperial"}
            resp = httpx.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {
                "condition": data.get("data", [{}])[0].get("weather", [{}])[0].get("main", "Unknown"),
                "temp": data.get("data", [{}])[0].get("temp", 60),
                "humidity": data.get("data", [{}])[0].get("humidity", 50),
                "wind_speed": data.get("data", [{}])[0].get("wind_speed", 5),
                "precipitation": data.get("data", [{}])[0].get("rain", {}).get("1h", 0),
                "description": data.get("data", [{}])[0].get("weather", [{}])[0].get("description", "No data"),
            }
        except Exception as e:
            logger.warning(f"OpenWeatherMap API failed, using mock: {e}")

    weather = _MOCK_WEATHER.get(date, _DEFAULT_WEATHER)
    logger.info(f"Weather for {date} at ({lat}, {lon}): {weather['condition']}")
    return weather
