"use client";

import { useEffect, useState } from "react";
import {
  Bot,
  Activity,
  Cpu,
  Clock,
  CheckCircle2,
  Terminal,
  RefreshCw,
  Layers
} from "lucide-react";
import { fetchAgentStats, fetchAgentRuns, AgentRun } from "@/lib/api";

export default function AgentControlCenter() {
  const [stats, setStats] = useState<any>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = () => {
    setLoading(true);
    fetchAgentStats().then(setStats).catch(console.error);
    fetchAgentRuns()
      .then(setRuns)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#262626] pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <Bot className="w-3.5 h-3.5 text-[#A3A3A3]" />
            <span>Agent Control Center // Real-Time Multi-Agent Orchestration</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Specialist AI Agent Fleet</h2>
          <p className="text-xs text-[#A3A3A3] mt-0.5">
            Monitoring live execution telemetry, latency, token throughput, and decision events across autonomous agents.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="px-3.5 py-2 text-xs font-mono rounded border border-[#404040] bg-[#171717] text-[#FFFFFF] hover:bg-[#262626] transition-colors flex items-center space-x-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>REFRESH TELEMETRY</span>
        </button>
      </div>

      {/* Fleet Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats?.active_specialist_agents?.map((agent: any) => {
          const runCount = stats?.execution_distribution?.[agent.name] || 0;
          return (
            <div
              key={agent.name}
              className="p-4 rounded-lg border border-[#262626] bg-[#121212] flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-[#FFFFFF] animate-pulse" />
                    <span className="text-xs font-bold text-[#FFFFFF]">{agent.name}</span>
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded border border-[#404040] bg-[#171717] text-[#FFFFFF]">
                    {agent.status}
                  </span>
                </div>
                <p className="text-xs text-[#A3A3A3] mt-1">{agent.role}</p>
              </div>

              <div className="pt-2 border-t border-[#262626] flex items-center justify-between text-[11px] font-mono text-[#737373]">
                <span>Telemetry Invocations:</span>
                <span className="text-[#FFFFFF] font-bold">{runCount}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Event Execution Stream */}
      <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
        <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#0A0A0A]">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-[#A3A3A3]" />
            <h3 className="text-xs font-semibold text-[#FFFFFF]">Live Agent Execution Stream (Database Persisted)</h3>
          </div>
          <span className="text-[10px] font-mono text-[#737373]">Actual Engine Runs ({runs.length})</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0A0A0A] border-b border-[#262626] text-[#737373] font-mono uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Agent</th>
                <th className="py-2.5 px-4">Task Description</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Latency</th>
                <th className="py-2.5 px-4">Input Context</th>
                <th className="py-2.5 px-4">Result Summary</th>
                <th className="py-2.5 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#262626]">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-[#737373]">
                    No agent runs recorded yet. Execute an analysis in Content Intelligence or ClaimDNA to observe live telemetry.
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.id} className="hover:bg-[#171717] transition-colors font-mono">
                    <td className="py-3 px-4 font-bold text-[#FFFFFF] text-[11px]">{run.agent_name}</td>
                    <td className="py-3 px-4 text-[#A3A3A3] text-[11px] max-w-xs truncate">{run.task_name}</td>
                    <td className="py-3 px-4">
                      <span className="text-[9px] px-1.5 py-0.5 rounded border border-[#404040] bg-[#171717] text-[#FFFFFF]">
                        {run.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#FFFFFF] text-[11px]">{run.execution_time_ms} ms</td>
                    <td className="py-3 px-4 text-[#737373] text-[10px] max-w-xs truncate">"{run.input_preview}"</td>
                    <td className="py-3 px-4 text-[#A3A3A3] text-[11px] max-w-xs truncate">{run.output_preview}</td>
                    <td className="py-3 px-4 text-[#737373] text-[10px] text-right">
                      {new Date(run.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
