"use client";

import { useMemo, useState } from "react";
import { Submission } from "@/lib/api";

interface AnalyticsChartProps {
  submissions: Submission[];
}

type Tab = "volume" | "findings";

/**
 * Activity chart computed entirely from real submission data — the last six
 * months bucketed by each submission's created_at. "Review Volume" counts
 * submissions; "Critical Findings" counts CRITICAL findings. No fabricated
 * series: if a month has no activity it reads zero, and the month-over-month
 * delta is derived from the two most recent buckets.
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
    <div className="bg-white rounded-2xl border border-[#E5E5E5] p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold uppercase text-[#737373]">Activity Trends</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#F5F5F5] text-[#0A0A0A] font-semibold">
              Last 6 months
            </span>
          </div>
          <div className="text-xl font-bold tracking-tight text-[#0A0A0A] mt-1">Brand Governance Activity</div>
          <div className="text-xs text-[#737373] mt-0.5">Computed from your submission history</div>
        </div>

        <div className="flex items-center bg-[#F5F5F5] p-1 rounded-xl border border-[#E5E5E5] text-xs font-mono">
          <button
            onClick={() => setTab("volume")}
            className={`px-3 py-1 rounded-lg transition-all ${tab === "volume" ? "bg-[#0A0A0A] text-white font-bold shadow-sm" : "text-[#737373] hover:text-[#0A0A0A]"}`}
          >
            Review Volume
          </button>
          <button
            onClick={() => setTab("findings")}
            className={`px-3 py-1 rounded-lg transition-all ${tab === "findings" ? "bg-[#0A0A0A] text-white font-bold shadow-sm" : "text-[#737373] hover:text-[#0A0A0A]"}`}
          >
            Critical Findings
          </button>
        </div>
      </div>

      {/* Metric callout (real totals) */}
      <div className="flex items-baseline space-x-3">
        <span className="text-3xl font-bold tracking-tight text-[#0A0A0A]">
          {total} {tab === "volume" ? (total === 1 ? "Audit" : "Audits") : "Critical"}
        </span>
        {(last > 0 || prev > 0) && (
          <span className="text-xs font-mono font-semibold text-[#0A0A0A] bg-[#F5F5F5] border border-[#E5E5E5] px-2 py-0.5 rounded-md">
            {delta >= 0 ? "+" : ""}{delta}% vs last month
          </span>
        )}
      </div>

      {/* Chart */}
      <div className="relative h-44 w-full pt-2">
        <svg viewBox="0 0 500 130" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="monoAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0A0A0A" stopOpacity="0.18" />
              <stop offset="60%" stopColor="#404040" stopOpacity="0.06" />
              <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.00" />
            </linearGradient>
          </defs>

          <line x1="0" y1="20" x2="500" y2="20" stroke="#F0F0F0" strokeDasharray="3 3" />
          <line x1="0" y1="60" x2="500" y2="60" stroke="#F0F0F0" strokeDasharray="3 3" />
          <line x1="0" y1="100" x2="500" y2="100" stroke="#F0F0F0" strokeDasharray="3 3" />

          <path d={area} fill="url(#monoAreaGrad)" />
          <path d={line} fill="none" stroke="#0A0A0A" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

          {pts.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="4"
              className="fill-white stroke-[#0A0A0A] stroke-2 cursor-pointer transition-all"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
          ))}
        </svg>

        {hover !== null && (
          <div
            className="absolute z-10 pointer-events-none -translate-x-1/2 -translate-y-full bg-[#0A0A0A] text-white text-[11px] font-mono px-2.5 py-1.5 rounded-lg shadow-lg border border-[#404040]"
            style={{ left: `${(pts[hover].x / 500) * 100}%`, top: `${(pts[hover].y / 130) * 100}%` }}
          >
            <div className="font-bold">
              {buckets[hover].label}: {series[hover]} {tab === "volume" ? "audits" : "critical"}
            </div>
          </div>
        )}

        <div className="flex justify-between items-center text-[10px] font-mono text-[#737373] pt-1 px-1">
          {buckets.map((b) => (
            <span key={b.key}>{b.label}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
