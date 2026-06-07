"""Generate synthetic FHIR patient records and write to mock_data/fhir_patients.json"""
import json
import os
from datetime import datetime, timedelta
import random


def generate_fhir_data():
    patients = []
    names = [
        ("John", "Doe", "1985-03-15", "male"),
        ("Jane", "Smith", "1990-07-22", "female"),
        ("Robert", "Johnson", "1972-11-08", "male"),
        ("Maria", "Garcia", "1988-04-30", "female"),
        ("James", "Wilson", "1995-09-12", "male"),
        ("Sarah", "Brown", "1982-01-25", "female"),
        ("Michael", "Davis", "1978-06-14", "male"),
        ("Emily", "Martinez", "1993-12-03", "female"),
        ("David", "Anderson", "1969-08-19", "male"),
        ("Lisa", "Taylor", "1987-05-27", "female"),
        ("Kevin", "Thomas", "1991-02-08", "male"),
        ("Amanda", "Jackson", "1984-10-16", "female"),
        ("Christopher", "White", "1975-07-31", "male"),
        ("Jessica", "Harris", "1997-04-11", "female"),
        ("Daniel", "Martin", "1980-09-05", "male"),
        ("Michelle", "Thompson", "1992-11-20", "female"),
        ("Andrew", "Moore", "1970-03-28", "male"),
        ("Stephanie", "Clark", "1986-08-07", "female"),
        ("William", "Lewis", "1965-12-15", "male"),
        ("Nicole", "Walker", "1994-06-01", "female"),
    ]

    conditions = [
        ("J00", "Acute nasopharyngitis [common cold]", "Respiratory"),
        ("M54.5", "Low back pain", "Musculoskeletal"),
        ("R07.9", "Chest pain, unspecified", "Symptoms"),
        ("S13.4XXA", "Sprain of ligaments of cervical spine", "Injury"),
        ("S80.11XA", "Contusion of right lower leg", "Injury"),
        ("S93.401A", "Unspecified sprain of right ankle", "Injury"),
        ("Z00.00", "Encounter for general adult medical examination", "Health services"),
        ("I10", "Essential (primary) hypertension", "Cardiovascular"),
        ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine"),
        ("F41.9", "Anxiety disorder, unspecified", "Mental Health"),
    ]

    for idx, (first, last, dob, gender) in enumerate(names):
        patient_id = f"patient-{idx+1:03d}"
        encounter_count = random.randint(1, 5)
        encounters = []
        for e in range(encounter_count):
            enc_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
            condition = random.choice(conditions)
            encounters.append({
                "id": f"enc-{patient_id}-{e+1}",
                "period": {"start": enc_date.strftime("%Y-%m-%d"), "end": (enc_date + timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d")},
                "reason": f"Patient presented with {condition[1].lower()}",
                "diagnosis": [{"code": condition[0], "display": condition[1]}],
                "provider": random.choice(["Springfield General Hospital", "Downtown Medical Clinic", "Memorial Hospital", "City Emergency Care", "Orthopedic Center of Excellence"]),
            })

        patients.append({
            "id": patient_id,
            "name": [{"given": [first], "family": last}],
            "gender": gender,
            "birthDate": dob,
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Maple', 'Cedar', 'Pine', 'Washington'])} St, {random.choice(['Springfield', 'Portland', 'Denver', 'Miami', 'Chicago'])}, {random.choice(['IL', 'OR', 'CO', 'FL', 'IL'])} {random.randint(10000, 99999)}",
            "phone": f"({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "encounters": encounters,
        })

    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock_claims")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fhir_patients.json")
    with open(output_path, "w") as f:
        json.dump({"resourceType": "Bundle", "type": "collection", "entry": patients}, f, indent=2)
    print(f"Generated {len(patients)} FHIR patient records -> {output_path}")
    return patients


if __name__ == "__main__":
    generate_fhir_data()
