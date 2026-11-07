"use client";

import { useMemo, useState } from "react";
import { Submission } from "@/lib/api";

interface AnalyticsChartProps {
  submissions: Submission[];
}

type Tab = "volume" | "findings";

/**
 * Activity chart computed entirely from real submission data — the last six
 * months bucketed by each submission's created_at.
 */
export function AnalyticsChart({ submissions }: AnalyticsChartProps) {
  const [tab, setTab] = useState<Tab>("volume");
  const [hover, setHover] = useState<number | null>(null);

  const buckets = useMemo(() => {
    const now = new Date();
    const months: { key: string; label: string; volume: number; findings: number }[] = [];
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push({
        key: `${d.getFullYear()}-${d.getMonth()}`,
        label: d.toLocaleString(undefined, { month: "short" }).toUpperCase(),
        volume: 0,
        findings: 0,
      });
    }
    const index = new Map(months.map((m, i) => [m.key, i]));
    submissions.forEach((s) => {
      const d = new Date(s.created_at);
      const k = `${d.getFullYear()}-${d.getMonth()}`;
      const i = index.get(k);
      if (i === undefined) return;
      months[i].volume += 1;
      months[i].findings += (s.findings || []).filter((f) => f.severity === "CRITICAL").length;
    });
    return months;
  }, [submissions]);

  const series = buckets.map((b) => (tab === "volume" ? b.volume : b.findings));
  const total = series.reduce((a, b) => a + b, 0);
  const max = Math.max(1, ...series);

  // Month-over-month delta from the two most recent real buckets.
  const last = series[series.length - 1];
  const prev = series[series.length - 2] ?? 0;
  const delta = prev === 0 ? (last > 0 ? 100 : 0) : Math.round(((last - prev) / prev) * 100);

  // Geometry (viewBox 0..500 x, 0..130 y; plot band y:18..110).
  const n = series.length;
  const pts = series.map((v, i) => ({
    x: n === 1 ? 250 : (i / (n - 1)) * 480 + 10,
    y: 110 - (v / max) * 92,
  }));
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const area = `${line} L ${pts[pts.length - 1].x.toFixed(1)},110 L ${pts[0].x.toFixed(1)},110 Z`;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-[0_1px_3px_rgba(15,23,42,0.04),0_8px_20px_-8px_rgba(79,70,229,0.06)] space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Activity Trends</span>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
              Last 6 months
            </span>
          </div>
          <div className="text-lg font-bold tracking-tight text-slate-900 mt-1">Brand Governance Activity</div>
          <div className="text-xs text-slate-500">Live analytics across marketing reviews & verified claims</div>
        </div>

        {/* Tab switch */}
        <div className="flex items-center bg-slate-100/80 p-1 rounded-xl border border-slate-200 text-xs self-start sm:self-auto">
          <button
            onClick={() => setTab("volume")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              tab === "volume"
                ? "bg-white text-indigo-700 font-semibold shadow-sm ring-1 ring-slate-200/60"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Review Volume
          </button>
          <button
            onClick={() => setTab("findings")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              tab === "findings"
                ? "bg-white text-rose-700 font-semibold shadow-sm ring-1 ring-slate-200/60"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Critical Findings
          </button>
        </div>
      </div>

      {/* Metric callout */}
      <div className="flex items-baseline space-x-3 pt-1">
        <span className="text-3xl font-extrabold tracking-tight text-slate-900">
          {total} <span className="text-xl font-medium text-slate-600">{tab === "volume" ? (total === 1 ? "Audit" : "Audits") : "Issues"}</span>
        </span>
        {(last > 0 || prev > 0) && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-md flex items-center gap-1 border ${
            delta >= 0 
              ? "bg-emerald-50 text-emerald-700 border-emerald-200" 
              : "bg-slate-100 text-slate-700 border-slate-200"
          }`}>
            <span>{delta >= 0 ? "+" : ""}{delta}%</span>
            <span className="text-[10px] text-slate-500 font-normal">vs last month</span>
          </span>
        )}
      </div>

      {/* Chart SVG */}
      <div className="relative h-44 w-full pt-2">
        <svg viewBox="0 0 500 130" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="chartIndigoGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4F46E5" stopOpacity="0.22" />
              <stop offset="60%" stopColor="#818CF8" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#EEF2FF" stopOpacity="0.00" />
            </linearGradient>
            <linearGradient id="chartRoseGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F43F5E" stopOpacity="0.22" />
              <stop offset="60%" stopColor="#FB7185" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#FFF1F2" stopOpacity="0.00" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1="0" y1="20" x2="500" y2="20" stroke="#E2E8F0" strokeDasharray="3 3" />
          <line x1="0" y1="60" x2="500" y2="60" stroke="#E2E8F0" strokeDasharray="3 3" />
          <line x1="0" y1="100" x2="500" y2="100" stroke="#E2E8F0" strokeDasharray="3 3" />

          {/* Area fill */}
          <path d={area} fill={tab === "volume" ? "url(#chartIndigoGrad)" : "url(#chartRoseGrad)"} />

          {/* Line */}
          <path
            d={line}
            fill="none"
            stroke={tab === "volume" ? "#4F46E5" : "#F43F5E"}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Dots */}
          {pts.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="4.5"
              className={`fill-white stroke-2 cursor-pointer transition-all hover:scale-125 ${
                tab === "volume" ? "stroke-[#4F46E5]" : "stroke-[#F43F5E]"
              }`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
          ))}
        </svg>

        {hover !== null && (
          <div
            className="absolute z-10 pointer-events-none -translate-x-1/2 -translate-y-full bg-white text-slate-900 text-xs px-3 py-1.5 rounded-lg shadow-lg border border-slate-200"
            style={{ left: `${(pts[hover].x / 500) * 100}%`, top: `${(pts[hover].y / 130) * 100}%` }}
          >
            <div className="font-bold flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${tab === "volume" ? "bg-indigo-600" : "bg-rose-500"}`} />
              <span>{buckets[hover].label}:</span>
              <span className="font-extrabold">{series[hover]}</span>
              <span className="text-slate-500 font-normal">{tab === "volume" ? "audits" : "critical"}</span>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center text-[11px] font-medium text-slate-500 pt-1 px-1">
          {buckets.map((b) => (
            <span key={b.key}>{b.label}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
