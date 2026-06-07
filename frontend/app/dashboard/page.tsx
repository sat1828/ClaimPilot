"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";

interface ClaimSummary {
  claim_id: string;
  claim_number: string;
  claimant_name: string;
  claim_type: string;
  status: string;
  current_agent: string;
  created_at: string;
}

export default function Dashboard() {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [wsConnected, setWsConnected] = useState(false);

  const fetchClaims = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/claims");
      const data = await res.json();
      setClaims(data.claims || []);
    } catch (err) {
      console.error("Failed to fetch claims:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClaims();
    const interval = setInterval(fetchClaims, 5000);
    return () => clearInterval(interval);
  }, [fetchClaims]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket("ws://localhost:8000/ws/adjuster/default-adjuster");
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "ESCALATION") {
          fetchClaims();
        }
      };
    } catch {
      setWsConnected(false);
    }
    return () => ws?.close();
  }, [fetchClaims]);

  const filteredClaims = filter === "all" ? claims : claims.filter((c) => c.status === filter.toUpperCase());

  const statusColors: Record<string, string> = {
    SUBMITTED: "text-blue-400 bg-blue-900/30",
    INTAKE_COMPLETE: "text-blue-400 bg-blue-900/30",
    VALIDATION_PASSED: "text-green-400 bg-green-900/30",
    VALIDATION_FAILED: "text-red-400 bg-red-900/30",
    INVESTIGATION_COMPLETE: "text-yellow-400 bg-yellow-900/30",
    FRAUD_ASSESSMENT_COMPLETE: "text-orange-400 bg-orange-900/30",
    APPROVED: "text-green-400 bg-green-900/30",
    REJECTED: "text-red-400 bg-red-900/30",
    ESCALATED: "text-orange-400 bg-orange-900/30",
    HUMAN_REVIEW: "text-purple-400 bg-purple-900/30",
    CLOSED: "text-gray-400 bg-gray-800/30",
    FAILED: "text-red-400 bg-red-900/30",
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/" className="text-blue-400 hover:text-blue-300 text-sm">
              &larr; Home
            </Link>
            <h1 className="text-2xl font-bold mt-1">Adjuster Dashboard</h1>
            <p className="text-gray-400 text-sm">Escalated claims requiring human review</p>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs ${
                wsConnected ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-green-400" : "bg-red-400"}`} />
              {wsConnected ? "Live" : "Offline"}
            </span>
          </div>
        </div>

        <div className="flex gap-2 flex-wrap">
          {["all", "escalated", "human_review", "approved", "rejected"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                filter === f
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {f === "human_review" ? "Human Review" : f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== "all" && (
                <span className="ml-1.5 opacity-60">
                  ({claims.filter((c) => c.status === f.toUpperCase()).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full" />
          </div>
        ) : filteredClaims.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <div className="text-4xl mb-4">No claims found</div>
            <p className="text-sm">Submit a claim via the API to see it appear here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredClaims.map((claim) => (
              <Link
                key={claim.claim_id}
                href={`/claims/${claim.claim_id}`}
                className="block p-4 bg-gray-800/50 rounded-lg border border-gray-700 hover:border-blue-700/50 transition-all hover:bg-gray-800"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold ${
                        claim.claim_type === "auto"
                          ? "bg-blue-900/50 text-blue-400"
                          : claim.claim_type === "medical"
                          ? "bg-green-900/50 text-green-400"
                          : claim.claim_type === "property"
                          ? "bg-yellow-900/50 text-yellow-400"
                          : "bg-gray-700 text-gray-400"
                      }`}
                    >
                      {claim.claim_type?.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium">{claim.claim_number}</div>
                      <div className="text-sm text-gray-400">{claim.claimant_name}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        statusColors[claim.status] || "text-gray-400 bg-gray-800"
                      }`}
                    >
                      {claim.status?.replace(/_/g, " ")}
                    </span>
                    <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
