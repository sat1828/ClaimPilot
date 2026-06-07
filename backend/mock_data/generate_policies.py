"""Generate synthetic insurance policy documents and embed into mock Pinecone format"""
import json
import os


def generate_policies():
    policies = {
        "POL-AUTO-001": {
            "policy_number": "POL-AUTO-001",
            "policy_type": "AUTO",
            "holder_name": "John Doe",
            "effective_date": "2024-01-01",
            "expiration_date": "2025-01-01",
            "coverage_limit": 100000.00,
            "deductible": 1000.00,
            "premium_amount": 1200.00,
            "document_text": """AUTO INSURANCE POLICY - DECLARATIONS
Policy Number: POL-AUTO-001
Policy Period: 2024-01-01 to 2025-01-01
Named Insured: John Doe
Vehicle: 2022 Toyota Camry VIN: JTDBF4K32C1234567

COVERAGE A - LIABILITY
We will pay damages for bodily injury or property damage for which any covered person becomes legally responsible because of an auto accident. Coverage limit: $100,000 per person, $300,000 per accident.

COVERAGE B - COMPREHENSIVE
We will pay for loss to your covered auto, minus any applicable deductible, caused by other than collision. This includes fire, theft, vandalism, flood, hail, windstorm, earthquake, or hitting an animal. Comprehensive deductible: $500.

COVERAGE C - COLLISION
We will pay for loss to your covered auto, minus any applicable deductible, caused by collision with another object or overturn. Collision deductible: $1,000.

EXCLUSIONS
We do not provide Coverage for:
1. Intentional loss
2. Wear and tear, freezing, mechanical or electrical breakdown
3. Radioactive contamination
4. War or insurrection
5. Using a vehicle without reasonable belief of permission
6. Racing or speed contests
7. Using the vehicle for carrying persons or property for a fee
8. Using the vehicle in the course of business (other than farming or ranching)

CONDITIONS
You must notify us promptly of any accident or loss. Failure to cooperate may void coverage.""",
        },
        "POL-HOME-001": {
            "policy_number": "POL-HOME-001",
            "policy_type": "HOME",
            "holder_name": "Jane Smith",
            "effective_date": "2024-03-01",
            "expiration_date": "2025-03-01",
            "coverage_limit": 350000.00,
            "deductible": 2500.00,
            "premium_amount": 2400.00,
            "document_text": """HOMEOWNERS INSURANCE POLICY - DECLARATIONS
Policy Number: POL-HOME-001
Policy Period: 2024-03-01 to 2025-03-01
Named Insured: Jane Smith
Property Address: 456 Oak Avenue, Springfield, IL 62701

COVERAGE A - DWELLING: $350,000
COVERAGE B - OTHER STRUCTURES: $35,000
COVERAGE C - PERSONAL PROPERTY: $175,000
COVERAGE D - LOSS OF USE: $70,000
COVERAGE E - PERSONAL LIABILITY: $300,000
COVERAGE F - MEDICAL PAYMENTS: $5,000

Deductible: $2,500

EXCLUSIONS
We do not insure for loss caused directly or indirectly by:
1. Flood, including storm surge, tidal wave, tsunami
2. Earth movement, including earthquake, landslide, sinkhole
3. Water damage from continuous or repeated seepage
4. Neglect
5. War
6. Nuclear hazard
7. Intentional loss
8. Ordinance or law

FLOOD INSURANCE: This policy does NOT cover flood damage. Flood insurance requires a separate policy through the National Flood Insurance Program (NFIP).""",
        },
        "POL-HEALTH-001": {
            "policy_number": "POL-HEALTH-001",
            "policy_type": "HEALTH",
            "holder_name": "Robert Johnson",
            "effective_date": "2024-01-01",
            "expiration_date": "2024-12-31",
            "coverage_limit": 1000000.00,
            "deductible": 1500.00,
            "premium_amount": 4500.00,
            "document_text": """HEALTH INSURANCE POLICY - DECLARATIONS
Policy Number: POL-HEALTH-001
Policy Period: 2024-01-01 to 2024-12-31
Named Insured: Robert Johnson

COVERED SERVICES:
- Hospitalization (semi-private room)
- Surgery (inpatient and outpatient)
- Physician services
- Diagnostic tests and imaging
- Emergency room care ($250 copay)
- Prescription drugs ($30 generic/$60 brand)
- Mental health services
- Maternity care
- Preventive care (no copay)

Deductible: $1,500 individual / $3,000 family
Out-of-pocket maximum: $6,000 individual / $12,000 family

PRE-EXISTING CONDITIONS
This policy does not cover pre-existing conditions for the first 12 months after the policy effective date. A pre-existing condition is any condition for which medical advice, diagnosis, care, or treatment was recommended or received within the 6 months before the policy effective date.

EXCLUSIONS
- Cosmetic surgery (unless reconstructive after covered surgery)
- Experimental treatments
- Dental care (unless from accident)
- Vision exams and eyewear
- Hearing aids
- Weight loss programs
- Alternative medicine (acupuncture, chiropractic)
- Services received outside the United States""",
        },
        "POL-TRAVEL-001": {
            "policy_number": "POL-TRAVEL-001",
            "policy_type": "TRAVEL",
            "holder_name": "Maria Garcia",
            "effective_date": "2024-06-01",
            "expiration_date": "2025-06-01",
            "coverage_limit": 50000.00,
            "deductible": 0.00,
            "premium_amount": 350.00,
            "document_text": """TRAVEL INSURANCE POLICY - DECLARATIONS
Policy Number: POL-TRAVEL-001
Policy Period: 2024-06-01 to 2025-06-01
Named Insured: Maria Garcia

COVERAGES:
Trip Cancellation: Up to $50,000 prepaid, non-refundable trip cost
Trip Interruption: Up to $50,000
Trip Delay: $500 per person ($1,000 max) after 6+ hour delay
Baggage Loss: $2,000 per person
Baggage Delay: $500 after 12+ hours
Medical Expense: $100,000
Emergency Evacuation: $500,000
Accidental Death: $25,000
Food Spoilage: Up to $500 per occurrence

TRIP CANCELLATION COVERED REASONS:
- Sickness, injury, or death of you or a family member
- Severe weather making destination uninhabitable
- Terrorist incident in destination city
- Jury duty or subpoena
- Military deployment
- Financial insolvency of travel supplier

TRIP CANCELLATION EXCLUSIONS:
- Pre-existing conditions (unless waiver purchased)
- Fear of travel or pandemic
- Travel advisory or warning issued before purchase
- Suicide or attempted suicide
- Loss of employment
- Change of mind or business reasons""",
        },
        "POL-COMM-001": {
            "policy_number": "POL-COMM-001",
            "policy_type": "COMMERCIAL",
            "holder_name": "Davis Construction LLC",
            "effective_date": "2024-01-01",
            "expiration_date": "2025-01-01",
            "coverage_limit": 2000000.00,
            "deductible": 5000.00,
            "premium_amount": 12000.00,
            "document_text": """COMMERCIAL GENERAL LIABILITY POLICY - DECLARATIONS
Policy Number: POL-COMM-001
Policy Period: 2024-01-01 to 2025-01-01
Named Insured: Davis Construction LLC
Business Type: General Contractor - Commercial & Residential

COVERAGE A - BODILY INJURY AND PROPERTY DAMAGE: $2,000,000 per occurrence
COVERAGE B - PERSONAL AND ADVERTISING INJURY: $2,000,000
COVERAGE C - MEDICAL PAYMENTS: $10,000 per person
Deductible: $5,000 per occurrence

EXCLUSIONS:
- Contractors Pollution Liability
- Professional Liability/Errors & Omissions
- Workers Compensation
- Auto Liability (covered under separate policy)
- Asbestos, lead, mold, silica
- Punitive or exemplary damages
- Breach of contract
- Damage to your work/product
- Recall of products""",
        },
        "POL-AUTO-002": {
            "policy_number": "POL-AUTO-002",
            "policy_type": "AUTO",
            "holder_name": "James Wilson",
            "effective_date": "2024-05-01",
            "expiration_date": "2025-05-01",
            "coverage_limit": 50000.00,
            "deductible": 500.00,
            "premium_amount": 800.00,
            "document_text": """AUTO INSURANCE POLICY - DECLARATIONS
Policy Number: POL-AUTO-002
Policy Period: 2024-05-01 to 2025-05-01
Named Insured: James Wilson
Vehicle: 2020 Honda Civic VIN: 2HGFE2F53CH123456

LIABILITY: $50,000 per person / $100,000 per accident
COMPREHENSIVE: Actual Cash Value minus $500 deductible
COLLISION: Actual Cash Value minus $500 deductible
UNINSURED MOTORIST: $50,000 per person / $100,000 per accident

EXCLUSIONS:
Same as standard auto policy exclusions including intentional loss, racing, business use, and wear and tear.""",
        },
    }

    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock_policies")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "policies.json")
    with open(output_path, "w") as f:
        json.dump(policies, f, indent=2)
    print(f"Generated {len(policies)} policy documents -> {output_path}")

    txt_path = os.path.join(output_dir, "policies_text.json")
    with open(txt_path, "w") as f:
        json.dump({k: {"policy_number": v["policy_number"], "text": v["document_text"]} for k, v in policies.items()}, f, indent=2)

    return policies


if __name__ == "__main__":
    generate_policies()
