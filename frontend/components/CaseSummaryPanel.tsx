"use client";

interface Props {
  claim: {
    claim_payload?: Record<string, unknown>;
    validation_result?: Record<string, unknown>;
    investigation_bundle?: Record<string, unknown>;
    fraud_assessment?: Record<string, unknown>;
    settlement_decision?: Record<string, unknown>;
    reasoning_chain?: Record<string, unknown>[];
    current_status: string;
    current_agent: string;
    pipeline_started_at?: string;
    pipeline_completed_at?: string;
  };
}

export default function CaseSummaryPanel({ claim }: Props) {
  const payload = claim.claim_payload || {};
  const validation = claim.validation_result || {};
  const settlement = claim.settlement_decision || {};

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <InfoCard label="Claimant" value={payload.claimant_name as string} />
        <InfoCard label="Policy" value={payload.policy_number as string} />
        <InfoCard label="Type" value={(payload.claim_type as string)?.toUpperCase()} />
        <InfoCard label="Amount" value={`$${(payload.claim_amount as number)?.toLocaleString() || "0"}`} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Event Details</h3>
          <p className="text-sm">{payload.event_description as string}</p>
          {payload.incident_location && (
            <p className="text-sm text-gray-400 mt-2">
              Location: {payload.incident_location as string}
            </p>
          )}
          {payload.event_date && (
            <p className="text-sm text-gray-400">
              Date: {payload.event_date as string}
            </p>
          )}
        </div>

        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Validation Result</h3>
          <div className="flex items-center gap-2">
            <span
              className={`text-sm font-medium ${
                validation.coverage_status === "COVERED"
                  ? "text-green-400"
                  : validation.coverage_status === "NOT_COVERED"
                  ? "text-red-400"
                  : "text-yellow-400"
              }`}
            >
              {validation.coverage_status as string || "PENDING"}
            </span>
          </div>
          {validation.coverage_type && (
            <p className="text-sm text-gray-400 mt-1">
              Coverage: {validation.coverage_type as string}
            </p>
          )}
          {Array.isArray(validation.missing_fields) && validation.missing_fields.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-red-400">Missing fields:</p>
              {(validation.missing_fields as string[]).map((f: string) => (
                <span key={f} className="text-xs text-red-400/80 block">
                  &bull; {f}
                </span>
              ))}
            </div>
          )}
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  (validation.confidence_score as number || 0) >= 0.6
                    ? "bg-green-500"
                    : (validation.confidence_score as number || 0) >= 0.4
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${((validation.confidence_score as number) || 0) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-400">
              {Math.round((validation.confidence_score as number || 0) * 100)}%
            </span>
          </div>
        </div>
      </div>

      <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
        <h3 className="text-sm font-medium text-gray-400 mb-2">Pipeline Status</h3>
        <div className="flex items-center gap-4 text-sm">
          <span className={`${claim.current_status === "SUBMITTED" || claim.current_status === "INTAKE_COMPLETE" ? "text-blue-400" : "text-green-400"}`}>
            Intake {claim.pipeline_started_at ? "✓" : "○"}
          </span>
          <span className="text-gray-600">&rarr;</span>
          <span className={`${claim.current_status === "VALIDATION_PASSED" || claim.current_status === "VALIDATION_FAILED" ? "text-blue-400" : claim.pipeline_started_at ? "text-green-400" : "text-gray-500"}`}>
            Validation
          </span>
          <span className="text-gray-600">&rarr;</span>
          <span className={`${claim.current_status === "INVESTIGATION_COMPLETE" ? "text-blue-400" : claim.current_status === "FRAUD_ASSESSMENT_COMPLETE" ? "text-green-400" : "text-gray-500"}`}>
            Investigation
          </span>
          <span className="text-gray-600">&rarr;</span>
          <span className={`${claim.current_status === "FRAUD_ASSESSMENT_COMPLETE" ? "text-blue-400" : claim.current_status === "APPROVED" || claim.current_status === "REJECTED" || claim.current_status === "ESCALATED" ? "text-green-400" : "text-gray-500"}`}>
            Settlement
          </span>
          <span className="text-gray-600">&rarr;</span>
          <span className={`${claim.current_status === "CLOSED" ? "text-green-400" : claim.current_status === "HUMAN_REVIEW" ? "text-orange-400 animate-pulse" : "text-gray-500"}`}>
            {claim.current_status === "HUMAN_REVIEW" ? "Human Review" : "Finalized"}
          </span>
        </div>
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-lg font-semibold mt-1">{value || "N/A"}</p>
    </div>
  );
}
