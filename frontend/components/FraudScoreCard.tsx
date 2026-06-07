"use client";

interface Props {
  assessment?: Record<string, unknown>;
}

export default function FraudScoreCard({ assessment }: Props) {
  if (!assessment || Object.keys(assessment).length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Fraud assessment not yet available
      </div>
    );
  }

  const probability = (assessment.fraud_probability_score as number) || 0;
  const riskTier = (assessment.risk_tier as string) || "UNKNOWN";
  const flags = (assessment.cited_flags as Array<Record<string, unknown>>) || [];
  const mlScore = (assessment.ml_score as number) || 0;
  const ruleScore = (assessment.rule_based_score as number) || 0;

  const tierColors: Record<string, string> = {
    LOW: "text-green-400 bg-green-900/30 border-green-800",
    MEDIUM: "text-yellow-400 bg-yellow-900/30 border-yellow-800",
    HIGH: "text-red-400 bg-red-900/30 border-red-800",
  };

  const tierColor = tierColors[riskTier] || "text-gray-400 bg-gray-800/30 border-gray-700";

  const severityColors: Record<string, string> = {
    LOW: "bg-blue-900/30 text-blue-400",
    MEDIUM: "bg-yellow-900/30 text-yellow-400",
    HIGH: "bg-red-900/30 text-red-400",
  };

  const gaugeColor =
    probability < 0.3 ? "stroke-green-500" : probability < 0.6 ? "stroke-yellow-500" : "stroke-red-500";

  const circumference = 2 * Math.PI * 54;
  const offset = circumference - probability * circumference;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-6 bg-gray-800/50 rounded-lg border border-gray-700 flex flex-col items-center">
          <svg width="140" height="140" viewBox="0 0 120 120" className="mb-3">
            <circle cx="60" cy="60" r="54" fill="none" stroke="#1e293b" strokeWidth="8" />
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              className={gaugeColor}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              transform="rotate(-90 60 60)"
            />
            <text x="60" y="55" textAnchor="middle" fill="#f1f5f9" fontSize="28" fontWeight="bold">
              {(probability * 100).toFixed(0)}
            </text>
            <text x="60" y="75" textAnchor="middle" fill="#94a3b8" fontSize="11">
              Fraud Score
            </text>
          </svg>
          <span className={`text-sm font-medium px-3 py-1 rounded-full border ${tierColor}`}>
            {riskTier} RISK
          </span>
        </div>

        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Score Breakdown</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">ML Anomaly Score</span>
                <span className="text-blue-400 font-medium">{(mlScore * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${mlScore * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Rule-Based Score</span>
                <span className="text-purple-400 font-medium">{(ruleScore * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-500 rounded-full"
                  style={{ width: `${ruleScore * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Signal Status</h3>
          <div className="space-y-2 text-sm">
            <SignalRow label="Duplicate Check" checked={assessment.duplicate_claim_check} />
            <SignalRow label="Timing Analysis" checked={assessment.timing_anomaly_check} />
            <SignalRow label="Inconsistency Check" checked={assessment.inconsistency_check} />
            <SignalRow label="Network Analysis" checked={assessment.network_analysis} />
          </div>
        </div>
      </div>

      {flags.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3">
            Flagged Anomalies ({flags.length})
          </h3>
          <div className="space-y-3">
            {flags.map((flag, i) => (
              <div
                key={i}
                className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        severityColors[flag.severity as string] || "bg-gray-700 text-gray-400"
                      }`}
                    >
                      {flag.severity as string}
                    </span>
                    <span className="text-sm font-medium text-red-400">
                      {flag.flag_type as string}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-300">
                  {(flag.description as string) || ""}
                </p>
                {flag.source && (
                  <p className="text-xs text-gray-500 mt-1">
                    Source: {flag.source as string}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {assessment.reasoning && (
        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Reasoning</h3>
          <p className="text-sm text-gray-300">{assessment.reasoning as string}</p>
        </div>
      )}
    </div>
  );
}

function SignalRow({ label, checked }: { label: string; checked: unknown }) {
  const isChecked =
    checked && typeof checked === "object" && (checked as Record<string, unknown>).checked === true;

  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400">{label}</span>
      <span className={isChecked ? "text-green-400" : "text-gray-600"}>
        {isChecked ? "✓ Ran" : "○ Pending"}
      </span>
    </div>
  );
}
