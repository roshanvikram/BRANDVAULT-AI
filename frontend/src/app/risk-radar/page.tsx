"use client";

import { Radar as RadarHdr } from "lucide-react";
import { PageHeader } from "@/components/engines/ui";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Radar, ShieldAlert, RefreshCw, Info, Lightbulb, Loader2 } from "lucide-react";
import { fetchRiskRadar, fetchRiskIntelligence, RiskIntelligence, RiskIndicator } from "@/lib/api";

const GLASS = "bg-white border border-slate-200/80 shadow-soft rounded-2xl";

// Semantic level styling for risk indicators
function levelStyle(level: string) {
  if (level === "High") return { badge: "bg-rose-50 text-rose-700 border border-rose-200", bar: "#F43F5E" };
  if (level === "Medium") return { badge: "bg-amber-50 text-amber-800 border border-amber-200", bar: "#F59E0B" };
  return { badge: "bg-emerald-50 text-emerald-700 border border-emerald-200", bar: "#10B981" };
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
      <PageHeader
        eyebrow="Risk Radar"
        icon={<RadarHdr />}
        title="Explained risk indicators"
        description="Transparent, rules-based indicators computed from your real governance records — each shows the numbers behind it. Not a forecast."
        actions={<>
          <Link href="/risk-radar/fraud" className="inline-flex items-center h-8 px-3 rounded-lg text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 hover:bg-indigo-100 transition-colors">Brand fraud intelligence →</Link>
          <Link href="/risk-radar/reputation" className="inline-flex items-center h-8 px-3 rounded-lg text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 hover:bg-indigo-100 transition-colors">Reputation early warning →</Link>
        <button onClick={load} disabled={loading}
          className="px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]">
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-200 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Radar</span>
        </button>
        </>}
      />

      {!intel && (
        <div className="flex items-center justify-center py-16 text-slate-400"><Loader2 className="w-6 h-6 animate-spin text-indigo-600" /></div>
      )}

      {intel && (
        <>
          {/* Overall */}
          <div className={`${GLASS} p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4`}>
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 border border-indigo-100 flex items-center justify-center shrink-0 shadow-sm">
                <ShieldAlert className="w-7 h-7" />
              </div>
              <div>
                <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Overall Governance Risk</div>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className="text-3xl font-bold tracking-tight text-slate-900">{intel.overall_score}</span>
                  <span className="text-sm font-medium text-slate-400">/100</span>
                  <span className={`text-[10px] uppercase px-2.5 py-0.5 rounded-full font-bold ${levelStyle(intel.overall_level).badge}`}>{intel.overall_level}</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  from {intel.history.submissions} submissions · {intel.history.findings} findings · {intel.history.claims} claims
                </div>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed max-w-sm flex items-start gap-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <Info className="w-4 h-4 mt-0.5 shrink-0 text-indigo-500" />{intel.basis}
            </p>
          </div>

          {/* Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {intel.indicators.map((ind: RiskIndicator) => {
              const s = levelStyle(ind.level);
              return (
                <div key={ind.key} className={`${GLASS} p-5 space-y-3.5`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900">{ind.label}</span>
                    <span className={`text-[10px] uppercase px-2 py-0.5 rounded-full font-bold ${s.badge}`}>{ind.level} · {ind.score}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full rounded-full transition-[width] duration-500" style={{ width: `${ind.score}%`, background: s.bar }} />
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{ind.rationale}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {ind.drivers.map((d, i) => (
                      <span key={i} className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-600">
                        {d.label}: <strong className="text-slate-900">{d.value}</strong>
                      </span>
                    ))}
                  </div>
                  <div className="flex items-start gap-1.5 text-xs text-slate-500 pt-2 border-t border-slate-100">
                    <Lightbulb className="w-4 h-4 mt-0.5 shrink-0 text-amber-500" />
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
                <div className="p-4 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Top Recurring Violations</span>
                  <span className="text-[11px] text-slate-500 font-medium">lexicon & claim drift</span>
                </div>
                <div className="p-4 space-y-2">
                  {(metrics.top_repeated_violations || []).length === 0 ? (
                    <div className="py-6 text-center text-xs text-slate-400">No repeated violations recorded.</div>
                  ) : metrics.top_repeated_violations.map((item: any, i: number) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-50/70 border border-slate-200/80 flex items-center justify-between">
                      <span className="text-xs text-slate-800 font-medium truncate pr-2">&ldquo;{item.phrase}&rdquo;</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 shrink-0">{item.occurrences}×</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className={`${GLASS} overflow-hidden`}>
                <div className="p-4 border-b border-[#E4E4E7] flex items-center justify-between">
                  <span className="text-sm font-bold text-[#0A0A0A]">ClaimDNA Truth Distribution</span>
                  <span className="text-[11px] font-mono text-[#737373]">live status counts</span>
                </div>
                <div className="p-4 space-y-2 font-mono text-xs">
                  {Object.entries(metrics.claims_risk_breakdown || {}).map(([status, count]: [string, any]) => (
                    <div key={status} className="p-3 rounded-xl bg-white border border-[#E4E4E7] flex items-center justify-between">
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
