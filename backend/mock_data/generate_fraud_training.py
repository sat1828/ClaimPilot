"""Generate 10,000 synthetic claim records for fraud detection model training"""
import json
import random
import os
from datetime import datetime, timedelta


def generate_training_data(n_samples: int = 10000, fraud_ratio: float = 0.01):
    random.seed(42)
    records = []
    n_fraud = int(n_samples * fraud_ratio)

    for i in range(n_samples):
        is_fraud = i < n_fraud

        days_since_policy = random.randint(1, 365)
        if is_fraud:
            days_since_policy = random.choice([
                random.randint(1, 15),
                random.randint(350, 365),
                random.randint(30, 60),
            ])

        claim_amount = random.uniform(500, 75000)
        if is_fraud:
            claim_amount = random.uniform(25000, 95000)

        prior_claims = random.choices([0, 1, 2, 3, 4, 5], weights=[40, 25, 15, 10, 7, 3])[0]
        if is_fraud:
            prior_claims = random.choices([0, 1, 2, 3, 4, 5], weights=[10, 15, 20, 25, 20, 10])[0]

        submission_delay = random.randint(0, 90)
        if is_fraud:
            submission_delay = random.choices([
                random.randint(0, 1),
                random.randint(180, 365),
            ], weights=[3, 1])[0]

        incident_hour = random.randint(6, 23)
        if is_fraud:
            incident_hour = random.choices([
                random.randint(0, 5),
                random.randint(1, 4),
            ], weights=[2, 1])[0]

        provider_freq = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                        weights=[30, 25, 15, 10, 8, 5, 3, 2, 1, 1])[0]
        if is_fraud:
            provider_freq = random.randint(5, 15)

        claim_vs_limit = claim_amount / random.uniform(25000, 100000)
        if is_fraud:
            claim_vs_limit = random.uniform(0.8, 1.2)

        record = {
            "id": f"TRAIN-{i+1:05d}",
            "is_fraud": is_fraud,
            "features": {
                "days_since_policy_start": days_since_policy,
                "claim_amount": round(claim_amount, 2),
                "num_prior_claims_12mo": prior_claims,
                "submission_delay_days": submission_delay,
                "incident_time_of_day": incident_hour,
                "provider_claim_frequency": provider_freq,
                "claim_vs_policy_limit_ratio": round(claim_vs_limit, 3),
            },
        }
        records.append(record)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fraud_training")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "fraud_training_data.json")
    with open(output_path, "w") as f:
        json.dump({"total": len(records), "fraud_count": n_fraud, "legitimate_count": n_samples - n_fraud, "records": records}, f, indent=2)

    print(f"Generated {len(records)} training records ({n_fraud} fraud, {n_samples - n_fraud} legitimate) -> {output_path}")

    csv_path = os.path.join(output_dir, "fraud_training_data.csv")
    with open(csv_path, "w") as f:
        headers = ["id", "is_fraud", "days_since_policy_start", "claim_amount", "num_prior_claims_12mo",
                    "submission_delay_days", "incident_time_of_day", "provider_claim_frequency", "claim_vs_policy_limit_ratio"]
        f.write(",".join(headers) + "\n")
        for r in records:
            feat = r["features"]
            row = [r["id"], str(r["is_fraud"]), str(feat["days_since_policy_start"]), str(feat["claim_amount"]),
                   str(feat["num_prior_claims_12mo"]), str(feat["submission_delay_days"]),
                   str(feat["incident_time_of_day"]), str(feat["provider_claim_frequency"]),
                   str(feat["claim_vs_policy_limit_ratio"])]
            f.write(",".join(row) + "\n")

    print(f"CSV training data -> {csv_path}")
    return records


if __name__ == "__main__":
    generate_training_data(10000, 0.01)
