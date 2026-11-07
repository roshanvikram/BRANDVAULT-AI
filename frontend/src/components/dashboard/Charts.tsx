"use client";

import { useId, useState } from "react";

/** Smooth path through points (monotone-ish cubic, no overshoot on flat runs). */
function smoothPath(pts: [number, number][]) {
  if (pts.length === 0) return "";
  if (pts.length === 1) return `M${pts[0][0]},${pts[0][1]}`;
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i];
    const [x1, y1] = pts[i + 1];
    const cx = (x0 + x1) / 2;
    d += ` C${cx},${y0} ${cx},${y1} ${x1},${y1}`;
  }
  return d;
}

const COLORS = {
  indigo: { line: "#4F46E5", fill: "#6366F1" },
  rose: { line: "#E11D48", fill: "#F43F5E" },
  emerald: { line: "#059669", fill: "#10B981" },
  amber: { line: "#D97706", fill: "#F59E0B" },
};
export type ChartColor = keyof typeof COLORS;

/** Small area sparkline for KPI cards. */
export function AreaSpark({ data, color = "indigo", className = "" }: { data: number[]; color?: ChartColor; className?: string }) {
  const id = useId().replace(/:/g, "");
  const W = 120, H = 36;
  const max = Math.max(1, ...data);
  const step = data.length > 1 ? W / (data.length - 1) : W;
  const pts: [number, number][] = data.map((v, i) => [i * step, H - 3 - (v / max) * (H - 6)]);
  const line = smoothPath(pts);
  const c = COLORS[color];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className={`w-full h-9 ${className}`} aria-hidden>
      <defs>
        <linearGradient id={`g${id}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={c.fill} stopOpacity="0.22" />
          <stop offset="100%" stopColor={c.fill} stopOpacity="0" />
        </linearGradient>
      </defs>
      {pts.length > 1 && <path d={`${line} L${W},${H} L0,${H} Z`} fill={`url(#g${id})`} />}
      <path d={line} fill="none" stroke={c.line} strokeWidth="1.75" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

/**
 * Area chart with an optional dashed "prior period" line and a hover readout.
 * Values are drawn exactly as given — callers pass real buckets.
 */
export function TrendChart({
  labels, values, prior, color = "indigo", format = (v) => String(v), height = 220, emptyNote,
}: {
  labels: string[]; values: (number | null)[]; prior?: (number | null)[]; color?: ChartColor;
  format?: (v: number) => string; height?: number; emptyNote?: string;
}) {
  const id = useId().replace(/:/g, "");
  const [hover, setHover] = useState<number | null>(null);
  const W = 640, H = 200, PAD = 10;
  const all = [...values, ...(prior || [])].filter((v): v is number => v !== null);
  const rawMax = Math.max(1, ...all);
  // Round the axis up to a friendly number.
  const mag = Math.pow(10, Math.floor(Math.log10(rawMax)));
  const max = Math.ceil(rawMax / mag) * mag;
  const n = values.length;
  const x = (i: number) => (n > 1 ? (i / (n - 1)) * W : W / 2);
  const y = (v: number) => H - PAD - (v / max) * (H - PAD * 2);
  const toPts = (arr: (number | null)[]) => arr.map((v, i) => (v === null ? null : [x(i), y(v)] as [number, number])).filter(Boolean) as [number, number][];
  const cur = toPts(values);
  const pri = prior ? toPts(prior) : [];
  const line = smoothPath(cur);
  const c = COLORS[color];
  const ticks = [max, max / 2, 0];
  const labelEvery = Math.max(1, Math.ceil(n / 7));
  const hasData = all.some((v) => v > 0);

  return (
    <div className="relative" style={{ height }}>
      <div className="absolute inset-0 grid grid-cols-[auto_1fr] gap-3">
        <div className="flex flex-col justify-between text-[11px] text-slate-400 tabular-nums text-right pb-6" style={{ paddingTop: 2 }}>
          {ticks.map((t) => <span key={t}>{format(t)}</span>)}
        </div>
        <div className="relative flex flex-col">
          <div className="relative flex-1">
            {ticks.map((t, i) => (
              <div key={t} className={`absolute inset-x-0 border-t ${i === ticks.length - 1 ? "border-slate-200" : "border-dashed border-slate-100"}`} style={{ top: `${(i / (ticks.length - 1)) * 100}%` }} />
            ))}
            <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible" aria-hidden>
              <defs>
                <linearGradient id={`t${id}`} x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor={c.fill} stopOpacity="0.20" />
                  <stop offset="100%" stopColor={c.fill} stopOpacity="0" />
                </linearGradient>
              </defs>
              {pri.length > 1 && <path d={smoothPath(pri)} fill="none" stroke="#94A3B8" strokeWidth="1.5" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />}
              {cur.length > 1 && <path d={`${line} L${cur[cur.length - 1][0]},${H} L${cur[0][0]},${H} Z`} fill={`url(#t${id})`} />}
              <path d={line} fill="none" stroke={c.line} strokeWidth="2.25" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
              {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={0} y2={H} stroke="#CBD5E1" strokeWidth="1" vectorEffect="non-scaling-stroke" />}
            </svg>
            {hover !== null && values[hover] !== null && (
              <span className="absolute w-2.5 h-2.5 -ml-[5px] -mt-[5px] rounded-full bg-white ring-2 pointer-events-none"
                    style={{ left: `${(x(hover) / W) * 100}%`, top: `${(y(values[hover] as number) / H) * 100}%`, ["--tw-ring-color" as any]: c.line }} />
            )}
            {/* hover hit areas */}
            <div className="absolute inset-0 flex" onMouseLeave={() => setHover(null)}>
              {values.map((_, i) => <div key={i} className="flex-1 h-full" onMouseEnter={() => setHover(i)} />)}
            </div>
            {hover !== null && (
              <div className="absolute -top-2 z-10 pointer-events-none -translate-x-1/2 -translate-y-full rounded-lg bg-slate-900 text-white text-[11px] px-2.5 py-1.5 shadow-lg whitespace-nowrap"
                   style={{ left: `${Math.min(92, Math.max(8, (x(hover) / W) * 100))}%` }}>
                <div className="font-semibold">{labels[hover]}</div>
                <div className="tabular-nums">{values[hover] === null ? "No data" : format(values[hover] as number)}
                  {prior && prior[hover] !== null && prior[hover] !== undefined && <span className="text-slate-400"> · prior {format(prior[hover] as number)}</span>}
                </div>
              </div>
            )}
            {!hasData && emptyNote && (
              <div className="absolute inset-0 flex items-center justify-center text-[13px] text-slate-400">{emptyNote}</div>
            )}
          </div>
          <div className="h-6 relative text-[11px] text-slate-400">
            {labels.map((l, i) => (i % labelEvery === 0 || i === n - 1) && (
              <span key={i} className="absolute top-1.5 -translate-x-1/2 whitespace-nowrap" style={{ left: `${(x(i) / W) * 100}%` }}>{l}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/** "+12% vs prior" chip. `goodWhenUp` decides the colour; null delta = no comparison possible. */
export function DeltaChip({ delta, goodWhenUp = true, suffix = "%", note }: { delta: number | null; goodWhenUp?: boolean; suffix?: string; note?: string }) {
  if (delta === null) return <span className="text-[11px] text-slate-400">{note || "No earlier data to compare"}</span>;
  const up = delta > 0, flat = delta === 0;
  const good = flat ? null : up === goodWhenUp;
  const cls = good === null ? "bg-slate-100 text-slate-600" : good ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700";
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px]">
      <span className={`inline-flex items-center gap-0.5 font-semibold px-1.5 py-0.5 rounded-md tabular-nums ${cls}`}>
        {flat ? "→" : up ? "↗" : "↘"} {up ? "+" : ""}{delta}{suffix}
      </span>
      <span className="text-slate-400">{note || "vs prior period"}</span>
    </span>
  );
}
