"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import CaseSummaryPanel from "@/components/CaseSummaryPanel";
import EvidenceTimeline from "@/components/EvidenceTimeline";
import FraudScoreCard from "@/components/FraudScoreCard";
import DecisionPanel from "@/components/DecisionPanel";
import ReasoningChain from "@/components/ReasoningChain";

interface ClaimDetail {
  claim_id: string;
  claim_number: string;
  claim_payload: Record<string, unknown>;
  validation_result: Record<string, unknown>;
  investigation_bundle: Record<string, unknown>;
  fraud_assessment: Record<string, unknown>;
  settlement_decision: Record<string, unknown>;
  reasoning_chain: Record<string, unknown>[];
  current_status: string;
  current_agent: string;
  error_log: string[];
  pipeline_started_at: string;
  pipeline_completed_at: string;
}

export default function ClaimDetail() {
  const params = useParams();
  const [claim, setClaim] = useState<ClaimDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("summary");

  const claimId = params?.id as string;

  useEffect(() => {
    if (!claimId) return;
    const fetchClaim = async () => {
      try {
        const res = await fetch(`/api/v1/claims/${claimId}`);
        if (res.ok) {
          const data = await res.json();
          setClaim(data);
        }
      } catch (err) {
        console.error("Failed to fetch claim:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchClaim();
    const interval = setInterval(fetchClaim, 3000);
    return () => clearInterval(interval);
  }, [claimId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="text-4xl">Claim not found</div>
        <Link href="/dashboard" className="text-blue-400 hover:text-blue-300">
          &larr; Back to Dashboard
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: "summary", label: "Summary" },
    { id: "evidence", label: "Evidence" },
    { id: "fraud", label: "Fraud Analysis" },
    { id: "decision", label: "Decision" },
    { id: "audit", label: "Audit Trail" },
  ];

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/dashboard" className="text-blue-400 hover:text-blue-300 text-sm">
              &larr; Dashboard
            </Link>
            <h1 className="text-2xl font-bold mt-1">{claim.claim_number}</h1>
            <p className="text-gray-400 text-sm">
              {claim.claim_payload?.claimant_name as string} &middot;{" "}
              {(claim.claim_payload?.claim_type as string)?.toUpperCase()} &middot;{" "}
              {claim.claim_payload?.event_date as string}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              claim.current_status === "APPROVED"
                ? "bg-green-900/30 text-green-400"
                : claim.current_status === "REJECTED"
                ? "bg-red-900/30 text-red-400"
                : claim.current_status === "HUMAN_REVIEW" || claim.current_status === "ESCALATED"
                ? "bg-orange-900/30 text-orange-400"
                : "bg-blue-900/30 text-blue-400"
            }`}
          >
            {claim.current_status?.replace(/_/g, " ")}
          </span>
        </div>

        <div className="flex gap-1 bg-gray-800/50 rounded-lg p-1 border border-gray-700">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "summary" && <CaseSummaryPanel claim={claim} />}
        {activeTab === "evidence" && <EvidenceTimeline bundle={claim.investigation_bundle} />}
        {activeTab === "fraud" && <FraudScoreCard assessment={claim.fraud_assessment} />}
        {activeTab === "decision" && (
          <DecisionPanel
            decision={claim.settlement_decision}
            claimId={claim.claim_id}
            status={claim.current_status}
          />
        )}
        {activeTab === "audit" && <ReasoningChain chain={claim.reasoning_chain} />}
      </div>
    </div>
  );
}
