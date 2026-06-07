"use client";

interface Props {
  chain?: Record<string, unknown>[];
}

export default function ReasoningChain({ chain }: Props) {
  if (!chain || chain.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No reasoning chain available
      </div>
    );
  }

  const groupedByAgent: Record<string, Record<string, unknown>[]> = {};
  for (const entry of chain) {
    const agent = (entry.agent as string) || (entry.action as string) || "unknown";
    if (!groupedByAgent[agent]) groupedByAgent[agent] = [];
    groupedByAgent[agent].push(entry);
  }

  const agentColors: Record<string, string> = {
    intake_agent: "border-l-blue-500 bg-blue-900/10",
    validation_agent: "border-l-yellow-500 bg-yellow-900/10",
    investigation_agent: "border-l-purple-500 bg-purple-900/10",
    fraud_agent: "border-l-red-500 bg-red-900/10",
    settlement_agent: "border-l-green-500 bg-green-900/10",
    human_loop_agent: "border-l-orange-500 bg-orange-900/10",
    finalize: "border-l-gray-500 bg-gray-800/30",
  };

  const agentIcons: Record<string, string> = {
    intake_agent: "📥",
    validation_agent: "🛡",
    investigation_agent: "🔍",
    fraud_agent: "⚠️",
    settlement_agent: "💰",
    human_loop_agent: "👤",
    finalize: "✅",
  };

  const agentLabels: Record<string, string> = {
    intake_agent: "Intake Agent",
    validation_agent: "Validation Agent",
    investigation_agent: "Investigation Agent",
    fraud_agent: "Fraud Detection Agent",
    settlement_agent: "Settlement Agent",
    human_loop_agent: "Human-in-the-Loop",
    finalize: "Finalize",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
        <div className="w-2 h-2 rounded-full bg-green-400" />
        <span>{chain.length} events recorded</span>
      </div>
      {Object.entries(groupedByAgent).map(([agent, entries]) => (
        <div
          key={agent}
          className={`border-l-2 pl-4 py-3 rounded-r-lg ${
            agentColors[agent] || "border-l-gray-600 bg-gray-800/30"
          }`}
        >
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">{agentIcons[agent] || "🤖"}</span>
            <span className="font-medium text-sm">
              {agentLabels[agent] || agent.replace(/_/g, " ")}
            </span>
            <span className="text-xs text-gray-500 ml-auto">
              {entries.length} action{entries.length > 1 ? "s" : ""}
            </span>
          </div>

          <div className="space-y-2">
            {entries.map((entry, i) => {
              const action = (entry.action as string) || "";
              const reasoning = entry.reasoning as string;
              const toolCall = action.startsWith("tool_call:");
              const confidence = entry.confidence as number;
              const success = entry.success as boolean | undefined;

              return (
                <div
                  key={i}
                  className="flex gap-3 text-sm bg-gray-800/50 p-3 rounded-lg border border-gray-700/50"
                >
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        success === false ? "bg-red-500" : "bg-blue-500"
                      }`}
                    />
                    <div className="w-px flex-1 bg-gray-700" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-medium text-xs ${
                          toolCall ? "text-purple-400" : "text-gray-300"
                        }`}
                      >
                        {toolCall ? action.replace("tool_call: ", "") : action}
                      </span>
                      {confidence !== undefined && (
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded ${
                            confidence >= 0.6
                              ? "bg-green-900/30 text-green-400"
                              : confidence >= 0.4
                              ? "bg-yellow-900/30 text-yellow-400"
                              : "bg-red-900/30 text-red-400"
                          }`}
                        >
                          {(confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>

                    {reasoning && (
                      <p className="text-gray-400 mt-1 text-xs">{reasoning}</p>
                    )}

                    {entry.input && (
                      <details className="mt-1">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                          Input
                        </summary>
                        <pre className="text-xs text-gray-500 mt-1 p-2 bg-gray-900 rounded overflow-x-auto max-h-20">
                          {JSON.stringify(entry.input, null, 2).slice(0, 300)}
                        </pre>
                      </details>
                    )}

                    {entry.output && (
                      <details className="mt-1">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                          Output
                        </summary>
                        <pre className="text-xs text-gray-500 mt-1 p-2 bg-gray-900 rounded overflow-x-auto max-h-20">
                          {JSON.stringify(entry.output, null, 2).slice(0, 300)}
                        </pre>
                      </details>
                    )}

                    {entry.timestamp && (
                      <p className="text-xs text-gray-600 mt-1">
                        {new Date(entry.timestamp as string).toLocaleString()}
                      </p>
                    )}

                    {success === false && entry.error && (
                      <p className="text-xs text-red-400 mt-1">
                        Error: {entry.error as string}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
