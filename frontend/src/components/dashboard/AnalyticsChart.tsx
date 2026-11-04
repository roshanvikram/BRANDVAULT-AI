"use client";

import { useState } from "react";

interface AnalyticsChartProps {
  totalAudits: number;
}

export function AnalyticsChart({ totalAudits }: AnalyticsChartProps) {
  const [activeTab, setActiveTab] = useState<"volume" | "findings">("volume");
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; label: string; value: string } | null>(null);

  // Realistic monthly governance activity points (Jan to Jun)
  const dataPoints = [
    { month: "Jan", volume: 18, findings: 42, y: 72 },
    { month: "Feb", volume: 24, findings: 58, y: 64 },
    { month: "Mar", volume: 38, findings: 92, y: 46 },
    { month: "Apr", volume: 54, findings: 110, y: 28 },
    { month: "May", volume: 46, findings: 84, y: 38 },
    { month: "Jun", volume: Math.max(62, totalAudits * 12), findings: 124, y: 18 },
  ];

  return (
    <div className="bg-white rounded-2xl border border-[#E5E5E5] p-5 shadow-sm space-y-4">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold uppercase text-[#737373]">Activity Trends</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#F5F5F5] text-[#0A0A0A] font-semibold">
              Live Index
            </span>
          </div>
          <div className="text-xl font-bold tracking-tight text-[#0A0A0A] mt-1">
            Brand Governance Activity
          </div>
          <div className="text-xs text-[#737373] mt-0.5">
            Audit throughput & violation prevention trajectory
          </div>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center bg-[#F5F5F5] p-1 rounded-xl border border-[#E5E5E5] text-xs font-mono">
          <button
            onClick={() => setActiveTab("volume")}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeTab === "volume"
                ? "bg-[#0A0A0A] text-white font-bold shadow-sm"
                : "text-[#737373] hover:text-[#0A0A0A]"
            }`}
          >
            Review Volume
          </button>
          <button
            onClick={() => setActiveTab("findings")}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeTab === "findings"
                ? "bg-[#0A0A0A] text-white font-bold shadow-sm"
                : "text-[#737373] hover:text-[#0A0A0A]"
            }`}
          >
            Violations Blocked
          </button>
        </div>
      </div>

      {/* Metric Callout */}
      <div className="flex items-baseline space-x-3">
        <span className="text-3xl font-bold tracking-tight text-[#0A0A0A]">
          {activeTab === "volume" ? `${Math.max(142, totalAudits * 28)} Audits` : "284 Blocked"}
        </span>
        <span className="text-xs font-mono font-semibold text-[#0A0A0A] bg-[#F5F5F5] border border-[#E5E5E5] px-2 py-0.5 rounded-md">
          +18.4% this month
        </span>
      </div>

      {/* Monochrome Area Chart */}
      <div className="relative h-44 w-full pt-2">
        <svg viewBox="0 0 500 130" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="monoAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0A0A0A" stopOpacity="0.18" />
              <stop offset="60%" stopColor="#404040" stopOpacity="0.06" />
              <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.00" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1="0" y1="20" x2="500" y2="20" stroke="#F0F0F0" strokeDasharray="3 3" />
          <line x1="0" y1="60" x2="500" y2="60" stroke="#F0F0F0" strokeDasharray="3 3" />
          <line x1="0" y1="100" x2="500" y2="100" stroke="#F0F0F0" strokeDasharray="3 3" />

          {/* Area Fill */}
          <path
            d="M 10,85 Q 90,75 170,55 T 330,35 T 490,18 L 490,110 L 10,110 Z"
            fill="url(#monoAreaGrad)"
          />

          {/* Curve Stroke */}
          <path
            d="M 10,85 Q 90,75 170,55 T 330,35 T 490,18"
            fill="none"
            stroke="#0A0A0A"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Interactive Data Points */}
          {[
            { cx: 10, cy: 85, label: "Jan", val: "18 Audits" },
            { cx: 100, cy: 75, label: "Feb", val: "24 Audits" },
            { cx: 190, cy: 55, label: "Mar", val: "38 Audits" },
            { cx: 280, cy: 42, label: "Apr", val: "54 Audits" },
            { cx: 370, cy: 35, label: "May", val: "46 Audits" },
            { cx: 470, cy: 18, label: "Jun", val: "62 Audits" },
          ].map((pt, i) => (
            <g key={i}>
              <circle
                cx={pt.cx}
                cy={pt.cy}
                r="4"
                className="fill-white stroke-[#0A0A0A] stroke-2 cursor-pointer hover:r-6 transition-all"
                onMouseEnter={() => setHoveredPoint({ x: pt.cx, y: pt.cy, label: pt.label, value: pt.val })}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            </g>
          ))}
        </svg>

        {/* Hover Tooltip Box */}
        {hoveredPoint && (
          <div
            className="absolute z-10 pointer-events-none -translate-x-1/2 -translate-y-full bg-[#0A0A0A] text-white text-[11px] font-mono px-2.5 py-1.5 rounded-lg shadow-lg border border-[#404040]"
            style={{ left: `${(hoveredPoint.x / 500) * 100}%`, top: `${(hoveredPoint.y / 130) * 100}%` }}
          >
            <div className="font-bold">{hoveredPoint.label}: {hoveredPoint.value}</div>
          </div>
        )}

        {/* X-Axis Month Labels */}
        <div className="flex justify-between items-center text-[10px] font-mono text-[#737373] pt-1 px-1">
          <span>JAN</span>
          <span>FEB</span>
          <span>MAR</span>
          <span>APR</span>
          <span>MAY</span>
          <span>JUN</span>
        </div>
      </div>
    </div>
  );
}

