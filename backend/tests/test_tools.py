import pytest
import os
import json
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPDFParser:
    def test_parse_pdf_no_file(self):
        from tools.pdf_parser import parse_pdf
        with pytest.raises(FileNotFoundError):
            parse_pdf("/nonexistent/file.pdf")


class TestVectorStore:
    def test_retrieve_policy_chunks_valid(self):
        from tools.vector_store import retrieve_policy_chunks
        chunks = retrieve_policy_chunks("POL-AUTO-001", "collision coverage")
        assert len(chunks) > 0
        assert any("collision" in c["text"].lower() for c in chunks)

    def test_retrieve_policy_chunks_unknown(self):
        from tools.vector_store import retrieve_policy_chunks
        chunks = retrieve_policy_chunks("UNKNOWN-POLICY", "test")
        assert isinstance(chunks, list)


class TestWeatherAPI:
    def test_get_weather_valid(self):
        from tools.weather_api import get_weather_on_date
        weather = get_weather_on_date(25.7617, -80.1918, "2024-03-15")
        assert "condition" in weather
        assert "temp" in weather

    def test_get_weather_invalid_date(self):
        from tools.weather_api import get_weather_on_date
        weather = get_weather_on_date(25.7617, -80.1918, "2099-01-01")
        assert weather["condition"] != ""


class TestFHIRMock:
    def test_query_fhir_found(self):
        from tools.fhir_mock import query_fhir_records
        result = query_fhir_records("john.doe.patient")
        assert "patient" in result
        assert result["patient"]["id"] == "patient-001"

    def test_query_fhir_not_found(self):
        from tools.fhir_mock import query_fhir_records
        result = query_fhir_records("nonexistent.patient")
        assert "error" in result

    def test_lookup_icd10_valid(self):
        from tools.fhir_mock import lookup_icd10_code
        result = lookup_icd10_code("S13.4XXA")
        assert result is not None
        assert result["valid"] is True

    def test_lookup_icd10_invalid(self):
        from tools.fhir_mock import lookup_icd10_code
        result = lookup_icd10_code("INVALID00")
        assert result is not None
        assert result["valid"] is False


class TestGeoService:
    def test_geocode_found(self):
        from tools.geo_service import get_address_geocode
        result = get_address_geocode("Miami, FL")
        assert "lat" in result
        assert "lon" in result

    def test_disaster_records(self):
        from tools.geo_service import check_disaster_records
        result = check_disaster_records("Miami", "2024-10-09")
        assert "disasters" in result


class TestFraudScorer:
    def test_ml_scorer(self):
        from tools.fraud_scorer import run_ml_fraud_scorer
        features = {
            "days_since_policy_start": 100,
            "claim_amount": 5000,
            "num_prior_claims_12mo": 1,
            "submission_delay_days": 5,
            "incident_time_of_day": 14,
        }
        result = run_ml_fraud_scorer(features)
        assert "anomaly_score" in result

    def test_timing_delta(self):
        from tools.fraud_scorer import compute_timing_delta
        result = compute_timing_delta("2024-06-20", "2024-06-21")
        assert result["delay_days"] == 1


class TestPDFGenerator:
    def test_generate_approve_letter(self):
        from tools.pdf_generator import generate_settlement_letter
        letter = generate_settlement_letter(
            "APPROVE",
            {"name": "John Doe", "policy": "POL-001", "claim_number": "CP-001"},
            {"payout_amount": 5000, "deductible_applied": 500, "settlement_amount": 5500},
        )
        assert "APPROVED" in letter or "approved" in letter.lower()

    def test_generate_reject_letter(self):
        from tools.pdf_generator import generate_settlement_letter
        letter = generate_settlement_letter(
            "REJECT",
            {"name": "Jane Smith", "policy": "POL-002", "claim_number": "CP-002"},
            {"reasoning": "Policy exclusion applies"},
        )
        assert "REJECTED" in letter or "rejected" in letter.lower()
