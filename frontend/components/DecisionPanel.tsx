"use client";

import { useState } from "react";

interface Props {
  decision?: Record<string, unknown>;
  claimId: string;
  status: string;
}

export default function DecisionPanel({ decision, claimId, status }: Props) {
  const [humanDecision, setHumanDecision] = useState<string | null>(null);
  const [adjusterNotes, setAdjusterNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!decision || Object.keys(decision).length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Settlement decision not yet available
      </div>
    );
  }

  const verdict = decision.decision as string;
  const payout = decision.payout_amount as number;
  const settlementAmount = decision.settlement_amount as number;
  const deductible = decision.deductible_applied as number;
  const confidence = decision.confidence_score as number;

  const handleSubmitDecision = async (d: string) => {
    setSubmitting(true);
    try {
      const formData = new URLSearchParams();
      formData.append("decision", d);
      formData.append("adjuster_notes", adjusterNotes);

      const res = await fetch(`/api/v1/claims/${claimId}/human-decision`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (res.ok) {
        setHumanDecision(d);
        setSubmitted(true);
      }
    } catch (err) {
      console.error("Failed to submit decision:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const verdictColors: Record<string, string> = {
    APPROVE: "text-green-400 bg-green-900/30 border-green-800",
    REJECT: "text-red-400 bg-red-900/30 border-red-800",
    ESCALATE: "text-orange-400 bg-orange-900/30 border-orange-800",
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-6 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Settlement Calculation</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Total Claim Amount</span>
              <span className="text-white font-medium">
                ${settlementAmount?.toLocaleString() || "0"}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Deductible Applied</span>
              <span className="text-red-400 font-medium">
                -${deductible?.toLocaleString() || "0"}
              </span>
            </div>
            <div className="border-t border-gray-700 pt-3 flex justify-between text-sm">
              <span className="text-gray-200 font-medium">Payout Amount</span>
              <span className="text-green-400 text-lg font-bold">
                ${payout?.toLocaleString() || "0"}
              </span>
            </div>
          </div>
        </div>

        <div className="p-6 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-4">AI Recommendation</h3>
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-lg font-bold ${
              verdictColors[verdict] || "text-gray-400 bg-gray-800 border-gray-700"
            }`}
          >
            {verdict}
          </div>
          {confidence !== undefined && (
            <div className="mt-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Confidence</span>
                <span className="text-blue-400 font-medium">
                  {(confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    confidence >= 0.6
                      ? "bg-green-500"
                      : confidence >= 0.4
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
        <h3 className="text-sm font-medium text-gray-400 mb-2">Reasoning</h3>
        <div className="space-y-2">
          {((decision.reasoning_chain as Array<Record<string, unknown>>) || []).map(
            (step: Record<string, unknown>, i: number) => (
              <div key={i} className="flex gap-2 text-sm">
                <span className="text-blue-400 shrink-0">{step.step as string}</span>
                <span className="text-gray-500">&rarr;</span>
                <span className="text-gray-300">{(step.result as string) || ""}</span>
                {step.source && (
                  <span className="text-xs text-gray-500 ml-auto">
                    [{step.source as string}]
                  </span>
                )}
              </div>
            )
          )}
        </div>
      </div>

      {(status === "HUMAN_REVIEW" || status === "ESCALATED") && (
        <div className="p-6 bg-orange-900/20 rounded-lg border border-orange-800/50">
          <h3 className="text-lg font-medium text-orange-400 mb-4">
            Human Adjuster Decision Required
          </h3>

          {submitted ? (
            <div className="text-center py-4">
              <div className="text-green-400 text-lg font-medium mb-2">
                Decision Submitted: {humanDecision}
              </div>
              <p className="text-gray-400 text-sm">
                Thank you. The claim has been updated.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <textarea
                value={adjusterNotes}
                onChange={(e) => setAdjusterNotes(e.target.value)}
                placeholder="Enter your notes and reasoning for this decision..."
                className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                rows={3}
              />

              <div className="flex gap-3">
                <button
                  onClick={() => handleSubmitDecision("APPROVED")}
                  disabled={submitting}
                  className="px-6 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-green-800/50 text-white rounded-lg font-medium transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleSubmitDecision("REJECTED")}
                  disabled={submitting}
                  className="px-6 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-red-800/50 text-white rounded-lg font-medium transition-colors"
                >
                  Reject
                </button>
                <button
                  onClick={() => handleSubmitDecision("REQUEST_MORE_INFO")}
                  disabled={submitting}
                  className="px-6 py-2.5 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800/50 text-white rounded-lg font-medium transition-colors"
                >
                  Request Info
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {decision.decision_letter_text && (
        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Decision Letter</h3>
          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
            {decision.decision_letter_text as string}
          </pre>
        </div>
      )}
    </div>
  );
}
