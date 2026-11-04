"use client";

import { useEffect, useState } from "react";
import {
  Radar,
  TrendingDown,
  AlertTriangle,
  Clock,
  ShieldAlert,
  BarChart2,
  RefreshCw
} from "lucide-react";
import { fetchRiskRadar } from "@/lib/api";

export default function RiskRadar() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadData = () => {
    setLoading(true);
    fetchRiskRadar()
      .then(setMetrics)
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
            <Radar className="w-3.5 h-3.5 text-[#A3A3A3]" />
            <span>Brand Risk Radar // Continuous Threat & Drift Analytics</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Brand Vulnerability & Drift Radar</h2>
          <p className="text-xs text-[#A3A3A3] mt-0.5">
            Real-time aggregation of terminology violations, pricing mismatches, and unsupported promotional claims.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="px-3.5 py-2 text-xs font-mono rounded border border-[#404040] bg-[#171717] text-[#FFFFFF] hover:bg-[#262626] transition-colors flex items-center space-x-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>REFRESH RADAR</span>
        </button>
      </div>

      {/* Top 3 Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>AGGREGATE RISK LEVEL</span>
            <ShieldAlert className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">
            {metrics?.risk_level || "EVALUATING"}
          </div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">Based on critical claim & price violations</div>
        </div>

        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>BRAND HEALTH INDEX</span>
            <BarChart2 className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">
            {metrics?.brand_health_index || 100}
            <span className="text-sm font-normal text-[#737373]">/100</span>
          </div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">
            Across {metrics?.total_campaign_submissions || 0} audited campaigns
          </div>
        </div>

        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>UNSUPPORTED / CONTRADICTED CLAIMS</span>
            <AlertTriangle className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">
            {(metrics?.claims_risk_breakdown?.Unsupported || 0) +
              (metrics?.claims_risk_breakdown?.Contradicted || 0)}
          </div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">Blocked prior to public campaign launch</div>
        </div>
      </div>

      {/* Two Column Detail: Repeated Violations vs Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Repeated Terminology & Claim Violations */}
        <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
          <div className="p-4 border-b border-[#262626] bg-[#0A0A0A] flex items-center justify-between">
            <span className="text-xs font-semibold text-[#FFFFFF]">Top Recurring Brand Violations</span>
            <span className="text-[10px] font-mono text-[#737373]">Lexicon & Claim Drift</span>
          </div>

          <div className="p-4 space-y-3">
            {metrics?.top_repeated_violations?.length === 0 ? (
              <div className="py-8 text-center text-xs text-[#737373] font-mono">
                No repeated violations recorded in current sample.
              </div>
            ) : (
              metrics?.top_repeated_violations?.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className="p-3 rounded bg-[#0A0A0A] border border-[#262626] flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-mono font-medium text-[#FFFFFF]">"{item.phrase}"</span>
                    <div className="text-[10px] text-[#737373] font-mono mt-0.5">Recurring Copy Drift</div>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded border border-[#404040] bg-[#171717] text-[#FFFFFF]">
                    {item.occurrences}x detected
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: ClaimDNA Truth Status Breakdown */}
        <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
          <div className="p-4 border-b border-[#262626] bg-[#0A0A0A] flex items-center justify-between">
            <span className="text-xs font-semibold text-[#FFFFFF]">ClaimDNA Truth Distribution</span>
            <span className="text-[10px] font-mono text-[#737373]">Live Status Counts</span>
          </div>

          <div className="p-4 space-y-3 font-mono text-xs">
            {Object.entries(metrics?.claims_risk_breakdown || {}).map(([status, count]: [string, any]) => (
              <div
                key={status}
                className="p-3 rounded bg-[#0A0A0A] border border-[#262626] flex items-center justify-between"
              >
                <span className="text-[#A3A3A3]">{status}</span>
                <span className="font-bold text-[#FFFFFF]">{count} Claims</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
