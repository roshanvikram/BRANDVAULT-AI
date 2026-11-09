"use client";

import { Bot as BotHdr } from "lucide-react";
import { PageHeader } from "@/components/engines/ui";
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
      <PageHeader
        eyebrow="Agent Control"
        icon={<BotHdr />}
        title="Agent activity"
        description="Every agent run is recorded with its task, timing and result, so any automated step can be inspected."
        actions={<>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-200 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Fleet</span>
        </button>
        </>}
      />

      {/* Fleet Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats?.active_specialist_agents?.map((agent: any) => {
          const runCount = stats?.execution_distribution?.[agent.name] || 0;
          return (
            <div
              key={agent.name}
              className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-soft flex flex-col justify-between space-y-3 hover:border-indigo-200 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-xs font-bold text-slate-900">{agent.name}</span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {agent.status}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{agent.role}</p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>Invocations:</span>
                <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">{runCount}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Event Execution Stream */}
      <div className="border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-indigo-600" />
            <h3 className="text-xs font-bold text-slate-900">Live Agent Execution Stream (Database Persisted)</h3>
          </div>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">Actual Engine Runs ({runs.length})</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200/80 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              <tr>
                <th className="py-3 px-4">Agent</th>
                <th className="py-3 px-4">Task Description</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Input Context</th>
                <th className="py-3 px-4">Result Summary</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-slate-400">
                    No agent runs recorded yet. Execute an analysis in Content Intelligence or ClaimDNA to observe live telemetry.
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900 text-xs flex items-center space-x-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                      <span>{run.agent_name}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-700 text-xs max-w-xs truncate">{run.task_name}</td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {run.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {run.execution_time_ms}ms
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-xs max-w-xs truncate">{run.input_preview}</td>
                    <td className="py-3 px-4 text-slate-700 text-xs max-w-xs truncate">{run.output_preview}</td>
                    <td className="py-3 px-4 text-right text-slate-400 text-xs">{new Date(run.created_at).toLocaleTimeString()}</td>
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
