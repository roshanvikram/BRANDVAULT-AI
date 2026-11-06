"use client";

import { useEffect, useState } from "react";
import { Radar, ShieldAlert, RefreshCw, Info, Lightbulb, Loader2 } from "lucide-react";
import { fetchRiskRadar, fetchRiskIntelligence, RiskIntelligence, RiskIndicator } from "@/lib/api";

const GLASS = "bg-white/70 backdrop-blur-xl border border-white/70 shadow-[0_10px_34px_-14px_rgba(10,10,10,0.22)] rounded-2xl";

// Monochrome level styling (no colour per the design system).
function levelStyle(level: string) {
  if (level === "High") return { badge: "bg-[#0A0A0A] text-white", bar: "#0A0A0A" };
  if (level === "Medium") return { badge: "bg-[#404040] text-white", bar: "#404040" };
  return { badge: "bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]", bar: "#A3A3A3" };
}

export default function RiskRadar() {
  const [intel, setIntel] = useState<RiskIntelligence | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([fetchRiskIntelligence().then(setIntel), fetchRiskRadar().then(setMetrics)])
      .catch(console.error)
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/50 pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <Radar className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span className="font-semibold">Brand Risk Radar // Predictive Risk Intelligence</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A]">Explained risk indicators from your history</h2>
          <p className="text-xs text-[#737373] mt-0.5">
            Transparent, rules-based indices over your real governance records — each shows the numbers behind it. Not a forecast.
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className={`px-3.5 py-2 text-xs font-mono font-semibold rounded-lg bg-[#0A0A0A] text-white hover:bg-[#262626] transition-colors flex items-center space-x-2`}>
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {!intel && (
        <div className="flex items-center justify-center py-16 text-[#737373]"><Loader2 className="w-5 h-5 animate-spin" /></div>
      )}

      {intel && (
        <>
          {/* Overall */}
          <div className={`${GLASS} p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4`}>
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 rounded-2xl bg-[#0A0A0A] text-white flex items-center justify-center shrink-0">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#A3A3A3] font-bold">Overall Governance Risk</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold tracking-tight text-[#0A0A0A]">{intel.overall_score}</span>
                  <span className="text-sm font-mono text-[#737373]">/100</span>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${levelStyle(intel.overall_level).badge}`}>{intel.overall_level}</span>
                </div>
                <div className="text-[11px] font-mono text-[#737373] mt-0.5">
                  from {intel.history.submissions} submissions · {intel.history.findings} findings · {intel.history.claims} claims
                </div>
              </div>
            </div>
            <p className="text-[11px] text-[#737373] leading-relaxed max-w-sm flex items-start gap-1.5">
              <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-[#A3A3A3]" />{intel.basis}
            </p>
          </div>

          {/* Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {intel.indicators.map((ind: RiskIndicator) => {
              const s = levelStyle(ind.level);
              return (
                <div key={ind.key} className={`${GLASS} p-5 space-y-3`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-[#0A0A0A]">{ind.label}</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${s.badge}`}>{ind.level} · {ind.score}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-black/10 overflow-hidden">
                    <div className="h-full rounded-full transition-[width] duration-500" style={{ width: `${ind.score}%`, background: s.bar }} />
                  </div>
                  <p className="text-[11px] text-[#404040] leading-relaxed">{ind.rationale}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {ind.drivers.map((d, i) => (
                      <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-white/60 border border-white/70 text-[#404040]">
                        {d.label}: <span className="font-bold text-[#0A0A0A]">{d.value}</span>
                      </span>
                    ))}
                  </div>
                  <div className="flex items-start gap-1.5 text-[11px] text-[#737373] pt-1 border-t border-white/50">
                    <Lightbulb className="w-3.5 h-3.5 mt-0.5 shrink-0 text-[#0A0A0A]" />
                    <span>{ind.recommendation}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Supporting detail from aggregate metrics */}
          {metrics && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className={`${GLASS} overflow-hidden`}>
                <div className="p-4 border-b border-white/50 flex items-center justify-between">
                  <span className="text-sm font-bold text-[#0A0A0A]">Top Recurring Violations</span>
                  <span className="text-[10px] font-mono text-[#737373]">lexicon & claim drift</span>
                </div>
                <div className="p-4 space-y-2">
                  {(metrics.top_repeated_violations || []).length === 0 ? (
                    <div className="py-6 text-center text-xs text-[#737373] font-mono">No repeated violations recorded.</div>
                  ) : metrics.top_repeated_violations.map((item: any, i: number) => (
                    <div key={i} className="p-3 rounded-xl bg-white/50 border border-white/60 flex items-center justify-between">
                      <span className="text-xs font-mono text-[#0A0A0A] truncate pr-2">&ldquo;{item.phrase}&rdquo;</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-white/70 bg-white/70 text-[#0A0A0A] font-bold shrink-0">{item.occurrences}×</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className={`${GLASS} overflow-hidden`}>
                <div className="p-4 border-b border-white/50 flex items-center justify-between">
                  <span className="text-sm font-bold text-[#0A0A0A]">ClaimDNA Truth Distribution</span>
                  <span className="text-[10px] font-mono text-[#737373]">live status counts</span>
                </div>
                <div className="p-4 space-y-2 font-mono text-xs">
                  {Object.entries(metrics.claims_risk_breakdown || {}).map(([status, count]: [string, any]) => (
                    <div key={status} className="p-3 rounded-xl bg-white/50 border border-white/60 flex items-center justify-between">
                      <span className="text-[#404040]">{status}</span>
                      <span className="font-bold text-[#0A0A0A]">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
