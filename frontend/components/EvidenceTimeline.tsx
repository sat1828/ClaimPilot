"use client";

interface Props {
  bundle?: Record<string, unknown>;
}

export default function EvidenceTimeline({ bundle }: Props) {
  if (!bundle || Object.keys(bundle).length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Investigation data not yet available
      </div>
    );
  }

  const evidenceItems = (bundle.evidence_items as Array<Record<string, unknown>>) || [];
  const gaps = (bundle.evidence_gaps as string[]) || [];

  const evidenceTypes: Record<string, { label: string; color: string; icon: string }> = {
    weather: { label: "Weather Report", color: "text-blue-400", icon: "🌤" },
    incident_report: { label: "Incident Report", color: "text-red-400", icon: "📋" },
    fhir_records: { label: "Medical Records", color: "text-green-400", icon: "🏥" },
    icd10_validation: { label: "ICD-10 Validation", color: "text-purple-400", icon: "🔬" },
    geocode: { label: "Geolocation", color: "text-yellow-400", icon: "📍" },
    disaster: { label: "Disaster Records", color: "text-orange-400", icon: "🌊" },
  };

  return (
    <div className="space-y-6">
      <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
        <h3 className="text-sm font-medium text-gray-400 mb-1">Investigation Summary</h3>
        <p className="text-sm">
          {(bundle.investigation_summary as string) || "No summary available"}
        </p>
        {bundle.confidence_score !== undefined && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-500">Confidence:</span>
            <div className="flex-1 max-w-xs h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  (bundle.confidence_score as number) >= 0.6
                    ? "bg-green-500"
                    : (bundle.confidence_score as number) >= 0.4
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${((bundle.confidence_score as number) || 0) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-400">
              {Math.round((bundle.confidence_score as number || 0) * 100)}%
            </span>
          </div>
        )}
      </div>

      {gaps.length > 0 && (
        <div className="p-4 bg-yellow-900/20 rounded-lg border border-yellow-800/50">
          <h3 className="text-sm font-medium text-yellow-400 mb-2">
            Evidence Gaps ({gaps.length})
          </h3>
          {gaps.map((gap, i) => (
            <p key={i} className="text-sm text-yellow-300/80">
              &bull; {gap}
            </p>
          ))}
        </div>
      )}

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-400">
          Evidence Items ({evidenceItems.length})
        </h3>
        {evidenceItems.length === 0 ? (
          <p className="text-sm text-gray-500">No evidence collected yet</p>
        ) : (
          evidenceItems.map((item, i) => {
            const typeInfo = evidenceTypes[item.type as string] || {
              label: (item.type as string) || "Evidence",
              color: "text-gray-400",
              icon: "📄",
            };
            return (
              <div
                key={i}
                className="p-3 bg-gray-800/50 rounded-lg border border-gray-700"
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg">{typeInfo.icon}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${typeInfo.color}`}>
                        {typeInfo.label}
                      </span>
                      {item.source && (
                        <span className="text-xs text-gray-500">
                          &middot; {item.source as string}
                        </span>
                      )}
                    </div>
                    <pre className="text-xs text-gray-400 mt-1 overflow-x-auto max-h-24 overflow-y-auto">
                      {JSON.stringify(item.data, null, 2).slice(0, 500)}
                    </pre>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
