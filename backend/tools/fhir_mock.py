import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_MOCK_PATIENTS = {
    "john.doe.patient": {
        "id": "patient-001",
        "name": [{"given": ["John"], "family": "Doe"}],
        "gender": "male",
        "birthDate": "1985-03-15",
    },
    "jane.smith.patient": {
        "id": "patient-002",
        "name": [{"given": ["Jane"], "family": "Smith"}],
        "gender": "female",
        "birthDate": "1990-07-22",
    },
    "robert.johnson.patient": {
        "id": "patient-003",
        "name": [{"given": ["Robert"], "family": "Johnson"}],
        "gender": "male",
        "birthDate": "1972-11-08",
    },
    "maria.garcia.patient": {
        "id": "patient-004",
        "name": [{"given": ["Maria"], "family": "Garcia"}],
        "gender": "female",
        "birthDate": "1988-04-30",
    },
    "james.wilson.patient": {
        "id": "patient-005",
        "name": [{"given": ["James"], "family": "Wilson"}],
        "gender": "male",
        "birthDate": "1995-09-12",
    },
}

_MOCK_ENCOUNTERS = {
    "patient-001": [
        {"id": "enc-001", "period": {"start": "2024-06-18", "end": "2024-06-18"}, "reason": "Motor vehicle accident - rear end collision", "diagnosis": [{"code": "S13.4XXA", "display": "Sprain of ligaments of cervical spine"}], "provider": "Springfield General Hospital"},
        {"id": "enc-002", "period": {"start": "2024-03-10", "end": "2024-03-10"}, "reason": "Routine physical examination", "diagnosis": [{"code": "Z00.00", "display": "Encounter for general adult medical examination"}], "provider": "Downtown Medical Clinic"},
    ],
    "patient-002": [
        {"id": "enc-003", "period": {"start": "2024-09-08", "end": "2024-09-10"}, "reason": "Chest pain and shortness of breath", "diagnosis": [{"code": "R07.9", "display": "Chest pain, unspecified"}, {"code": "R06.02", "display": "Shortness of breath"}], "provider": "Memorial Hospital"},
        {"id": "enc-004", "period": {"start": "2024-11-15", "end": "2024-11-15"}, "reason": "Follow-up after car accident - whiplash", "diagnosis": [{"code": "S13.4XXA", "display": "Sprain of ligaments of cervical spine"}], "provider": "Springfield General Hospital"},
    ],
    "patient-003": [
        {"id": "enc-005", "period": {"start": "2024-02-20", "end": "2024-02-22"}, "reason": "Hip replacement surgery", "diagnosis": [{"code": "M16.11", "display": "Unilateral primary osteoarthritis, right hip"}], "provider": "Orthopedic Center of Excellence"},
        {"id": "enc-006", "period": {"start": "2024-07-05", "end": "2024-07-05"}, "reason": "Slip and fall in grocery store parking lot", "diagnosis": [{"code": "S80.11XA", "display": "Contusion of right lower leg"}], "provider": "City Emergency Care"},
    ],
    "patient-004": [],
    "patient-005": [
        {"id": "enc-007", "period": {"start": "2024-05-20", "end": "2024-05-20"}, "reason": "Emergency room visit - back pain after lifting", "diagnosis": [{"code": "M54.5", "display": "Low back pain"}], "provider": "City Emergency Care"},
        {"id": "enc-008", "period": {"start": "2024-08-01", "end": "2024-08-01"}, "reason": "Sports injury - ankle sprain", "diagnosis": [{"code": "S93.401A", "display": "Unspecified sprain of right ankle"}], "provider": "Sports Medicine Institute"},
    ],
}

_MOCK_CLAIMS_FHIR = {
    "patient-001": [
        {"id": "fhir-claim-001", "status": "active", "created": "2024-06-20", "diagnosis": [{"diagnosisCodeableConcept": {"coding": [{"code": "S13.4XXA"}]}}], "total": {"value": 3500.00, "currency": "USD"}},
    ],
    "patient-002": [
        {"id": "fhir-claim-002", "status": "active", "created": "2024-11-16", "diagnosis": [{"diagnosisCodeableConcept": {"coding": [{"code": "S13.4XXA"}]}}], "total": {"value": 4200.00, "currency": "USD"}},
    ],
}

_ICD10_DATABASE = {
    "S13.4XXA": {"code": "S13.4XXA", "description": "Sprain of ligaments of cervical spine", "category": "Injury", "valid": True},
    "S06.0X9A": {"code": "S06.0X9A", "description": "Concussion without loss of consciousness", "category": "Injury", "valid": True},
    "M54.5": {"code": "M54.5", "description": "Low back pain", "category": "Musculoskeletal", "valid": True},
    "R07.9": {"code": "R07.9", "description": "Chest pain, unspecified", "category": "Symptoms", "valid": True},
    "Z00.00": {"code": "Z00.00", "description": "Encounter for general adult medical examination", "category": "Health services", "valid": True},
    "M16.11": {"code": "M16.11", "description": "Unilateral primary osteoarthritis, right hip", "category": "Musculoskeletal", "valid": True},
    "S80.11XA": {"code": "S80.11XA", "description": "Contusion of right lower leg", "category": "Injury", "valid": True},
    "S93.401A": {"code": "S93.401A", "description": "Unspecified sprain of right ankle", "category": "Injury", "valid": True},
    "J00": {"code": "J00", "description": "Acute nasopharyngitis [common cold]", "category": "Respiratory", "valid": True},
    "INVALID00": {"code": "INVALID00", "description": "Invalid test code", "category": "Unknown", "valid": False},
}


def query_fhir_records(patient_id: str, date_range: Optional[str] = None) -> dict:
    patient = _MOCK_PATIENTS.get(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found", "resourceType": "OperationOutcome"}

    pid = patient["id"]
    encounters = _MOCK_ENCOUNTERS.get(pid, [])
    fhir_claims = _MOCK_CLAIMS_FHIR.get(pid, [])

    if date_range:
        try:
            if " to " in date_range:
                start_str = date_range.split(" to ")[0]
            else:
                start_str = date_range
        except:
            pass

    return {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient", **patient}},
            {"resource": {"resourceType": "Encounter", "total": len(encounters), "entry": encounters}},
            {"resource": {"resourceType": "Claim", "total": len(fhir_claims), "entry": fhir_claims}},
        ],
        "patient": patient,
        "encounters": encounters,
        "fhir_claims": fhir_claims,
    }


def lookup_icd10_code(code: str) -> Optional[dict]:
    return _ICD10_DATABASE.get(code.upper())
