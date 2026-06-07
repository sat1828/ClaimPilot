import json
import logging
from typing import Optional

from config import settings
from agents.base_agent import BaseAgent, AgentError
from tools.weather_api import get_weather_on_date
from tools.incident_search import search_incident_reports
from tools.fhir_mock import query_fhir_records, lookup_icd10_code
from tools.geo_service import get_address_geocode, check_disaster_records
from orchestrator.state_schema import InvestigationBundle

logger = logging.getLogger(__name__)

INVESTIGATION_SYSTEM_PROMPT = """You are the Investigation Agent for ClaimPilot. You are the detective.

Your role: Autonomously gather external evidence for a claim based on its type.
You decide which tools to call based on the claim context. This is the core agentic behavior.

For AUTO claims, you should typically use:
- get_weather_on_date: Check weather conditions on the incident date/location
- search_incident_reports: Search for police reports or news about the incident
- get_address_geocode: Geocode the incident location for precise coordinates

For MEDICAL claims, you should typically use:
- query_fhir_records: Retrieve hospital/medical records from the FHIR endpoint
- lookup_icd10_code: Validate diagnosis codes
- get_address_geocode: Geocode provider address

For PROPERTY claims, you should typically use:
- get_address_geocode: Geocode the property location
- check_disaster_records: Check for natural disasters in the area/date
- get_weather_on_date: Check weather conditions

Explain your tool selection reasoning before calling each tool.
This creates an auditable chain of thought for compliance purposes.

If a tool fails or returns no data, proceed with partial evidence and flag the gap.
Your investigation_summary should clearly state what evidence was found and what gaps exist."""

INVESTIGATION_TOOLS = [
    {
        "name": "get_weather_on_date",
        "description": "Get historical weather data for a specific location and date. Useful for validating weather-related claims (e.g., rain, hail, flood).",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude of the incident location"},
                "lon": {"type": "number", "description": "Longitude of the incident location"},
                "date": {"type": "string", "description": "Date of the incident (YYYY-MM-DD)"}
            },
            "required": ["lat", "lon", "date"]
        }
    },
    {
        "name": "search_incident_reports",
        "description": "Search for police reports, news articles, or incident records matching the claim description. Returns relevant reports with source URLs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Description of the incident to search for"},
                "location": {"type": "string", "description": "Location of the incident"},
                "date": {"type": "string", "description": "Date of the incident (YYYY-MM-DD)"}
            },
            "required": ["query", "location"]
        }
    },
    {
        "name": "query_fhir_records",
        "description": "Query the mock FHIR R4 server for patient medical records. Returns patient data, encounter history, and diagnosis information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient identifier"},
                "date_range": {"type": "string", "description": "Date range for records (e.g., '2024-01-01 to 2024-12-31')"}
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "lookup_icd10_code",
        "description": "Validate and get description for an ICD-10 diagnosis code. Confirms the code exists and matches expected diagnoses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "ICD-10 diagnosis code (e.g., 'S06.0X9A', 'M54.5')"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_address_geocode",
        "description": "Geocode an address string to latitude/longitude coordinates. Used to validate incident locations and enable weather lookups.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Street address or location description"}
            },
            "required": ["address"]
        }
    },
    {
        "name": "check_disaster_records",
        "description": "Check for natural disasters (floods, hurricanes, earthquakes, wildfires) recorded at a specific location and date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Location to check"},
                "date": {"type": "string", "description": "Date to check (YYYY-MM-DD)"}
            },
            "required": ["location", "date"]
        }
    },
]


class InvestigationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="investigation_agent", max_retries=3)

    async def run(self, state: dict) -> dict:
        claim = state.get("claim_payload", {})
        if not claim:
            raise AgentError("No claim_payload in state for investigation", self.name, recoverable=False)

        self._log_reasoning(state, f"Investigation Agent analyzing {claim.get('claim_type')} claim")

        claim_type = claim.get("claim_type", "").lower()
        event_description = claim.get("event_description", "")
        incident_location = claim.get("incident_location", "")
        event_date = claim.get("event_date", "")
        lat = claim.get("incident_lat")
        lon = claim.get("incident_lon")

        bundle = {
            "weather_data": None,
            "incident_reports": [],
            "fhir_records": None,
            "icd10_validation": None,
            "geocode_data": None,
            "disaster_records": None,
            "evidence_items": [],
            "evidence_gaps": [],
            "investigation_summary": "",
            "confidence_score": 0.0,
        }

        tools_called = []

        if claim_type in ("auto", "car", "vehicle"):
            self._log_reasoning(state, "Claim type is AUTO. Selecting weather + incident report + geocode tools.")
            tools_called = ["weather", "incident", "geocode"]

            if lat and lon and event_date:
                try:
                    weather = get_weather_on_date(lat, lon, event_date[:10])
                    bundle["weather_data"] = weather
                    bundle["evidence_items"].append({"type": "weather", "data": weather, "source": "OpenWeatherMap"})
                    self._log_tool_call(state, "get_weather_on_date", f"{lat},{lon},{event_date}", "success")
                except Exception as e:
                    self._log_tool_call(state, "get_weather_on_date", f"{lat},{lon},{event_date}", None, success=False, error=str(e))
                    bundle["evidence_gaps"].append(f"Weather data unavailable: {e}")

            if incident_location and event_description:
                try:
                    reports = search_incident_reports(event_description[:200], incident_location, event_date[:10] if event_date else None)
                    bundle["incident_reports"] = reports
                    if reports:
                        bundle["evidence_items"].append({"type": "incident_report", "data": reports, "source": "Tavily/Web"})
                    self._log_tool_call(state, "search_incident_reports", f"{event_description[:50]}", f"{len(reports)} reports")
                except Exception as e:
                    self._log_tool_call(state, "search_incident_reports", event_description[:50], None, success=False, error=str(e))
                    bundle["evidence_gaps"].append(f"Incident search unavailable: {e}")

            if incident_location:
                try:
                    geo = get_address_geocode(incident_location)
                    bundle["geocode_data"] = geo
                    bundle["evidence_items"].append({"type": "geocode", "data": geo, "source": "Google Maps"})
                    self._log_tool_call(state, "get_address_geocode", incident_location, "success")
                except Exception as e:
                    self._log_tool_call(state, "get_address_geocode", incident_location, None, success=False, error=str(e))

        elif claim_type in ("medical", "health"):
            self._log_reasoning(state, "Claim type is MEDICAL. Selecting FHIR + ICD-10 tools.")
            tools_called = ["fhir", "icd10"]

            patient_id = claim.get("claimant_name", "").replace(" ", ".").lower() + ".patient"
            try:
                fhir_data = query_fhir_records(patient_id, event_date[:10] if event_date else None)
                bundle["fhir_records"] = fhir_data
                bundle["evidence_items"].append({"type": "fhir_records", "data": fhir_data, "source": "FHIR Mock Server"})
                self._log_tool_call(state, "query_fhir_records", patient_id, "success")
            except Exception as e:
                self._log_tool_call(state, "query_fhir_records", patient_id, None, success=False, error=str(e))
                bundle["evidence_gaps"].append(f"FHIR records unavailable: {e}")

            if "icd10" in str(claim).upper() or "diagnosis" in str(event_description).lower():
                try:
                    import re
                    codes = re.findall(r'[A-Z]\d{2}\.\d+', event_description)
                    for code in codes[:3]:
                        validation = lookup_icd10_code(code)
                        if validation:
                            bundle["icd10_validation"] = validation
                            bundle["evidence_items"].append({"type": "icd10_validation", "data": validation, "source": "ICD-10 DB"})
                            self._log_tool_call(state, "lookup_icd10_code", code, "success")
                except Exception as e:
                    self._log_tool_call(state, "lookup_icd10_code", "N/A", None, success=False, error=str(e))

        elif claim_type in ("property", "home", "renters", "commercial"):
            self._log_reasoning(state, "Claim type is PROPERTY. Selecting geocode + disaster + weather tools.")
            tools_called = ["geocode", "disaster", "weather"]

            if incident_location:
                try:
                    geo = get_address_geocode(incident_location)
                    bundle["geocode_data"] = geo
                    bundle["evidence_items"].append({"type": "geocode", "data": geo, "source": "Google Maps"})
                    self._log_tool_call(state, "get_address_geocode", incident_location, "success")
                except Exception as e:
                    self._log_tool_call(state, "get_address_geocode", incident_location, None, success=False, error=str(e))

            if incident_location and event_date:
                try:
                    disasters = check_disaster_records(incident_location, event_date[:10])
                    bundle["disaster_records"] = disasters
                    if disasters and disasters.get("disasters"):
                        bundle["evidence_items"].append({"type": "disaster", "data": disasters, "source": "FEMA/NOAA Mock"})
                    self._log_tool_call(state, "check_disaster_records", f"{incident_location},{event_date}", "success")
                except Exception as e:
                    self._log_tool_call(state, "check_disaster_records", f"{incident_location},{event_date}", None, success=False, error=str(e))

            if lat and lon and event_date:
                try:
                    weather = get_weather_on_date(lat, lon, event_date[:10])
                    bundle["weather_data"] = weather
                    bundle["evidence_items"].append({"type": "weather", "data": weather, "source": "OpenWeatherMap"})
                    self._log_tool_call(state, "get_weather_on_date", f"{lat},{lon},{event_date}", "success")
                except Exception as e:
                    self._log_tool_call(state, "get_weather_on_date", f"{lat},{lon},{event_date}", None, success=False, error=str(e))

        else:
            self._log_reasoning(state, f"Unknown claim type '{claim_type}'. Calling generic tools.")
            if incident_location:
                try:
                    geo = get_address_geocode(incident_location)
                    bundle["geocode_data"] = geo
                    bundle["evidence_items"].append({"type": "geocode", "data": geo, "source": "Google Maps"})
                except Exception as e:
                    bundle["evidence_gaps"].append(f"Geocode unavailable: {e}")

        evidence_count = len(bundle["evidence_items"])
        gap_count = len(bundle["evidence_gaps"])
        bundle["investigation_summary"] = f"Investigation complete for {claim_type} claim. Found {evidence_count} evidence items, {gap_count} gaps. Tools used: {', '.join(tools_called)}."
        bundle["confidence_score"] = 0.9 if gap_count == 0 else max(0.3, 0.9 - (gap_count * 0.2))

        state["investigation_bundle"] = bundle

        self._log_reasoning(state, bundle["investigation_summary"])

        return state
