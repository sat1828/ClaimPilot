import logging
import json
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

# In-memory mock for development without Pinecone
_mock_policy_chunks = {}


def _load_mock_chunks():
    global _mock_policy_chunks
    if _mock_policy_chunks:
        return
    _mock_policy_chunks = {
        "POL-AUTO-001": [
            {
                "text": "COVERAGE A - LIABILITY: We will pay damages for bodily injury or property damage for which any covered person becomes legally responsible because of an auto accident. Covered persons include you, your family members, and any person using your covered auto with your permission.",
                "metadata": {"policy": "POL-AUTO-001", "section": "COVERAGE_A", "page": 2},
                "score": 0.95,
            },
            {
                "text": "COVERAGE B - COMPREHENSIVE: We will pay for loss to your covered auto, minus any applicable deductible, caused by other than collision. This includes fire, theft, vandalism, flood, hail, windstorm, earthquake, or hitting an animal. Comprehensive deductible: $500.",
                "metadata": {"policy": "POL-AUTO-001", "section": "COVERAGE_B", "page": 4},
                "score": 0.92,
            },
            {
                "text": "COVERAGE C - COLLISION: We will pay for loss to your covered auto, minus any applicable deductible, caused by collision with another object or overturn. Collision deductible: $1,000.",
                "metadata": {"policy": "POL-AUTO-001", "section": "COVERAGE_C", "page": 4},
                "score": 0.91,
            },
            {
                "text": "EXCLUSIONS - We do not provide Coverage for: (1) Intentional loss; (2) Wear and tear, freezing, mechanical breakdown; (3) Radioactive contamination; (4) War or insurrection; (5) Using a vehicle without reasonable belief of permission; (6) Racing or speed contests; (7) Using the vehicle for carrying persons or property for a fee.",
                "metadata": {"policy": "POL-AUTO-001", "section": "EXCLUSIONS", "page": 7},
                "score": 0.88,
            },
            {
                "text": "POLICY PERIOD: This policy applies only to accidents and losses occurring during the policy period shown in the Declarations. Policy effective: 2024-01-01. Policy expiration: 2025-01-01.",
                "metadata": {"policy": "POL-AUTO-001", "section": "DECLARATIONS", "page": 1},
                "score": 0.85,
            },
        ],
        "POL-HOME-001": [
            {
                "text": "COVERAGE A - DWELLING: We cover your dwelling and other structures on the residence premises. Coverage A limit: $350,000. Deductible: $2,500.",
                "metadata": {"policy": "POL-HOME-001", "section": "COVERAGE_A", "page": 2},
                "score": 0.94,
            },
            {
                "text": "EXCLUSIONS - We do not insure for loss caused directly or indirectly by: (1) Flood, including storm surge, tidal wave, tsunami; (2) Earth movement, including earthquake, landslide, sinkhole; (3) Water damage from continuous or repeated seepage; (4) Neglect; (5) War; (6) Nuclear hazard; (7) Intentional loss.",
                "metadata": {"policy": "POL-HOME-001", "section": "EXCLUSIONS", "page": 5},
                "score": 0.93,
            },
            {
                "text": "FLOOD INSURANCE: This policy does NOT cover flood damage. Flood insurance is available through the National Flood Insurance Program (NFIP) and requires a separate policy and premium.",
                "metadata": {"policy": "POL-HOME-001", "section": "FLOOD_EXCLUSION", "page": 6},
                "score": 0.97,
            },
        ],
        "POL-HEALTH-001": [
            {
                "text": "COVERED SERVICES: This policy covers medically necessary services including: hospitalization, surgery, physician services, diagnostic tests, emergency care, prescription drugs, and mental health services.",
                "metadata": {"policy": "POL-HEALTH-001", "section": "COVERED_SERVICES", "page": 3},
                "score": 0.93,
            },
            {
                "text": "PRE-EXISTING CONDITIONS: This policy does not cover pre-existing conditions for the first 12 months after the policy effective date. A pre-existing condition is any condition for which medical advice, diagnosis, care, or treatment was recommended or received within the 6 months before the policy effective date.",
                "metadata": {"policy": "POL-HEALTH-001", "section": "PRE_EXISTING", "page": 8},
                "score": 0.95,
            },
        ],
        "POL-TRAVEL-001": [
            {
                "text": "TRIP CANCELLATION: We will reimburse you for prepaid, non-refundable trip payments if you must cancel your trip due to: sickness, injury, or death of you or a family member; severe weather that makes your destination uninhabitable; terrorist incident in your destination city; jury duty or subpoena; or military deployment.",
                "metadata": {"policy": "POL-TRAVEL-001", "section": "TRIP_CANCELLATION", "page": 2},
                "score": 0.96,
            },
            {
                "text": "FOOD SPOILAGE: We cover loss of refrigerated food up to $500 per occurrence due to mechanical failure of the refrigerator, power outage off-premises, or accidental damage to the refrigerator.",
                "metadata": {"policy": "POL-TRAVEL-001", "section": "FOOD_SPOILAGE", "page": 4},
                "score": 0.94,
            },
        ],
    }


def retrieve_policy_chunks(policy_number: str, query: str, top_k: int = 5) -> list[dict]:
    _load_mock_chunks()
    chunks = _mock_policy_chunks.get(policy_number, [])
    if not chunks:
        all_chunks = []
        for policy_chunks in _mock_policy_chunks.values():
            all_chunks.extend(policy_chunks)
        scored = []
        query_lower = query.lower()
        for c in all_chunks:
            text_lower = c["text"].lower()
            score = 0
            for word in query_lower.split():
                if word in text_lower:
                    score += 1
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        chunks = [c for _, c in scored[:top_k]]
    else:
        scored = []
        query_lower = query.lower()
        for c in chunks:
            text_lower = c["text"].lower()
            score = 0
            for word in query_lower.split():
                if word in text_lower:
                    score += 1
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        chunks = [c for _, c in scored[:top_k]]

    logger.info(f"Retrieved {len(chunks)} chunks for policy {policy_number} query '{query[:50]}'")
    return chunks


def get_policy_metadata(policy_number: str) -> Optional[dict]:
    _load_mock_chunks()
    chunks = _mock_policy_chunks.get(policy_number)
    if not chunks:
        return None
    return {
        "policy_number": policy_number,
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "is_active": True,
        "policy_type": "AUTO" if "AUTO" in policy_number else "HOME" if "HOME" in policy_number else "HEALTH" if "HEALTH" in policy_number else "TRAVEL",
    }
