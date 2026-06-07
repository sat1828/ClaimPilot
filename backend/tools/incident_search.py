import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_MOCK_INCIDENTS = [
    {
        "title": "Multi-vehicle collision on I-95 due to heavy rain",
        "source": "Local News",
        "date": "2024-03-15",
        "location": "I-95, Mile Marker 42, Miami, FL",
        "summary": "A multi-vehicle collision occurred on I-95 southbound near Mile Marker 42 around 6:30 PM. Heavy rain was reported in the area. Three vehicles involved, minor injuries reported.",
        "url": "https://news.example.com/i95-accident-mar2024",
        "relevance_score": 0.92,
    },
    {
        "title": "Rear-end collision at intersection of Main St and Oak Ave",
        "source": "Police Report Database",
        "date": "2024-06-20",
        "location": "Main St & Oak Ave, Springfield",
        "summary": "Police responded to a rear-end collision at the intersection. Driver reported sudden stop due to pedestrian. No injuries reported. Airbags deployed.",
        "url": "https://police.example.com/report/SFD-2024-0612",
        "relevance_score": 0.88,
    },
    {
        "title": "Hail storm causes widespread property damage in Denver metro",
        "source": "Weather Service",
        "date": "2024-09-10",
        "location": "Denver, CO",
        "summary": "Severe thunderstorm produced golf ball-sized hail across the Denver metro area. Thousands of homes and vehicles reported damaged.",
        "url": "https://weather.example.com/denver-hail-sep2024",
        "relevance_score": 0.85,
    },
    {
        "title": "House fire on Elm Street ruled accidental",
        "source": "Fire Department Report",
        "date": "2024-07-04",
        "location": "123 Elm Street, Portland, OR",
        "summary": "Fire department responded to a residential structure fire. Cause determined to be faulty wiring. Structure sustained significant damage. No fatalities.",
        "url": "https://fire.example.com/portland-fire-2024",
        "relevance_score": 0.79,
    },
]


def search_incident_reports(query: str, location: str = "", date: str = "") -> list[dict]:
    if settings.tavily_api_key and settings.app_env != "development":
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.tavily_api_key)
            search_query = f"{query} {location} {date}"
            response = client.search(query=search_query, search_depth="advanced", max_results=5)
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "source": "Tavily Web Search",
                    "date": date,
                    "location": location,
                    "summary": r.get("content", "")[:500],
                    "url": r.get("url", ""),
                    "relevance_score": r.get("score", 0.5),
                })
            return results
        except Exception as e:
            logger.warning(f"Tavily search failed, using mock: {e}")

    query_lower = (query + " " + location).lower()
    scored = []
    for incident in _MOCK_INCIDENTS:
        score = 0
        for word in query_lower.split():
            if word in incident["title"].lower() or word in incident["summary"].lower():
                score += 1
        if date and date[:7] == incident["date"][:7]:
            score += 2
        if location and location.lower() in incident["location"].lower():
            score += 3
        if score > 0:
            scored.append((score, incident))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [i for _, i in scored[:5]]
    logger.info(f"Found {len(results)} incident reports for query")
    return results
