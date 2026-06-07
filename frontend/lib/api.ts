const API_BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API ${res.status}: ${error}`);
  }

  return res.json();
}

export interface ClaimSummary {
  claim_id: string;
  claim_number: string;
  claimant_name: string;
  claim_type: string;
  status: string;
  current_agent: string;
  created_at: string;
}

export interface ClaimDetail {
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

export const api = {
  listClaims: (status?: string) => {
    const query = status ? `?status=${status}` : "";
    return request<{ claims: ClaimSummary[]; total: number }>(`/claims${query}`);
  },

  getClaim: (claimId: string) => {
    return request<ClaimDetail>(`/claims/${claimId}`);
  },

  getReasoningChain: (claimId: string) => {
    return request<{ claim_id: string; reasoning_chain: Record<string, unknown>[] }>(
      `/claims/${claimId}/reasoning-chain`
    );
  },

  submitClaim: async (formData: FormData) => {
    const res = await fetch(`${API_BASE}/claims/submit`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const error = await res.text();
      throw new Error(`Submit failed: ${error}`);
    }
    return res.json();
  },

  humanDecision: async (claimId: string, decision: string, adjusterNotes: string = "") => {
    const body = new URLSearchParams();
    body.append("decision", decision);
    body.append("adjuster_notes", adjusterNotes);

    const res = await fetch(`${API_BASE}/claims/${claimId}/human-decision`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    if (!res.ok) {
      const error = await res.text();
      throw new Error(`Decision failed: ${error}`);
    }
    return res.json();
  },
};

export default api;
