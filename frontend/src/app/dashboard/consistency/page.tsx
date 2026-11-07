"use client";

import { useEffect, useState } from "react";
import { Grid3x3, Filter, X } from "lucide-react";
import { fetchConsistency, Consistency, ConsistencyFilters, Heatmap } from "@/lib/api";
import { CARD, Badge, PageHeader, ErrorNote, Loading, INPUT, BTN_SECONDARY } from "@/components/engines/ui";

function HeatGrid({ data, rowLabel }: { data: Heatmap; rowLabel: string }) {
  if (!data.rows.length) return <p className="text-[13px] text-slate-500 py-4">No findings for these filters.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-separate border-spacing-1">
        <thead>
          <tr>
            <th className="text-left font-medium text-slate-500 px-2">{rowLabel}</th>
            {data.columns.map((c) => <th key={c} className="font-medium text-slate-500 px-1 min-w-[84px]">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r, i) => (
            <tr key={r}>
              <td className="pr-3 text-slate-800 font-medium whitespace-nowrap">{r}</td>
              {data.cells[i].map((v, j) => {
                const t = data.max ? v / data.max : 0;
                return (
                  <td key={j} title={`${r} · ${data.columns[j]}: ${v}`}
                      className="text-center rounded-md h-9 tabular-nums font-semibold"
                      style={{ background: v ? `rgba(225, 29, 72, ${0.08 + 0.72 * t})` : "#f8fafc", color: t > 0.55 ? "#fff" : "#334155" }}>
                    {v || ""}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Bars({ rows }: { rows: { label: string; value: number; max: number; sub?: string }[] }) {
  return (
    <ul className="space-y-2">
      {rows.map((r) => (
        <li key={r.label}>
          <div className="flex items-center justify-between text-xs"><span className="text-slate-700 truncate pr-2">{r.label}</span><span className="font-semibold tabular-nums text-slate-900">{r.value}{r.sub ? <span className="text-slate-400 font-normal"> {r.sub}</span> : null}</span></div>
          <div className="mt-1 h-1.5 rounded-full bg-slate-100 overflow-hidden"><div className="h-full rounded-full bg-indigo-500" style={{ width: `${r.max ? (100 * r.value) / r.max : 0}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}

export default function ConsistencyPage() {
  const [filters, setFilters] = useState<ConsistencyFilters>({});
  const [data, setData] = useState<Consistency | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"product" | "department" | "month">("product");

  useEffect(() => { fetchConsistency(filters).then((d) => { setData(d); setError(null); }).catch((e) => setError(e.message)); }, [filters]);
  const set = (k: keyof ConsistencyFilters, v: string) => setFilters((f) => ({ ...f, [k]: v || undefined }));
  const active = Object.values(filters).some(Boolean);

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/dashboard", label: "Command Center" }}
        eyebrow="Brand Consistency Heatmap" icon={<Grid3x3 className="w-3.5 h-3.5" />}
        title="Where brand consistency breaks down"
        description="Violations by product, department and month, compliance by campaign, repeated mistakes and approval trends. Every number is calculated from stored records."
      />
      <div className={`${CARD} p-4 flex flex-wrap items-end gap-2`}>
        <Filter className="w-4 h-4 text-slate-400 mb-2.5" aria-hidden />
        <label className="text-[11px] text-slate-500">From<input type="date" value={filters.date_from || ""} onChange={(e) => set("date_from", e.target.value)} className={`${INPUT} h-9 mt-0.5`} /></label>
        <label className="text-[11px] text-slate-500">To<input type="date" value={filters.date_to || ""} onChange={(e) => set("date_to", e.target.value)} className={`${INPUT} h-9 mt-0.5`} /></label>
        {([["product", "Product", data?.options.products], ["department", "Department", data?.options.departments],
           ["category", "Violation", data?.options.categories], ["severity", "Severity", data?.options.severities]] as const).map(([k, label, opts]) => (
          <label key={k} className="text-[11px] text-slate-500">{label}
            <select value={filters[k] || ""} onChange={(e) => set(k, e.target.value)} className={`${INPUT} h-9 mt-0.5 min-w-[140px]`}>
              <option value="">All</option>
              {(opts || []).map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </label>
        ))}
        {active && <button onClick={() => setFilters({})} className={BTN_SECONDARY}><X className="w-3.5 h-3.5" /> Clear</button>}
      </div>
      <ErrorNote message={error} />
      {!data ? <Loading label="Calculating…" /> : (
        <>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {data.basis.demonstration_data && <Badge tone="warn">Demonstration data</Badge>}
            <span className="text-slate-500">{data.basis.note}</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[["Campaigns", data.kpis.campaigns], ["Avg compliance", data.kpis.avg_score ?? "—"], ["Findings", data.kpis.findings],
              ["Critical", data.kpis.critical], ["Unresolved", data.kpis.unresolved], ["Approval rate", data.kpis.approval_rate === null ? "—" : `${data.kpis.approval_rate}%`]].map(([k, v]) => (
              <div key={k as string} className={`${CARD} p-3.5`}><div className="text-[11px] text-slate-500">{k}</div><div className="text-xl font-bold text-slate-900 tabular-nums">{v}</div></div>
            ))}
          </div>

          <div className={`${CARD} p-5`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-bold text-slate-900">Violation heatmap</h3>
              <div className="flex gap-1.5" role="tablist">
                {(["product", "department", "month"] as const).map((t) => (
                  <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
                          className={`h-8 px-3 rounded-lg text-xs font-semibold border capitalize ${tab === t ? "bg-indigo-50 border-indigo-200 text-indigo-800" : "bg-white border-slate-200 text-slate-600"}`}>
                    by {t}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-3"><HeatGrid data={data.heatmaps[tab]} rowLabel={tab === "month" ? "Month" : tab === "product" ? "Product" : "Department"} /></div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 mb-3">Compliance by product</h3>
              <Bars rows={data.compliance.products.map((p) => ({ label: p.name, value: p.avg_score, max: 100, sub: `· ${p.campaigns} campaigns` }))} />
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 mb-3">Repeated terminology mistakes</h3>
              {data.terminology_repeats.length === 0 ? <p className="text-[13px] text-slate-500">None.</p> :
                <Bars rows={data.terminology_repeats.map((t) => ({ label: `“${t.term}”`, value: t.count, max: data.terminology_repeats[0].count }))} />}
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 mb-3">Unresolved violations</h3>
              {data.unresolved.length === 0 ? <p className="text-[13px] text-slate-500">None.</p> : (
                <ul className="space-y-1.5 text-xs">
                  {data.unresolved.map((u) => (
                    <li key={String(u.category)} className="flex items-center justify-between gap-2">
                      <span className="text-slate-700">{String(u.category)}</span>
                      <span className="flex gap-1">
                        {["CRITICAL", "WARNING", "SUGGESTION"].map((s) => u[s] ? <Badge key={s} tone={s === "CRITICAL" ? "bad" : s === "WARNING" ? "warn" : "neutral"}>{String(u[s])}</Badge> : null)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 mb-3">Logo & colour signals</h3>
              <p className="text-xs text-slate-500 mb-2">From {data.visual.investigations} asset investigation(s) and visual findings.</p>
              {Object.keys(data.visual.logo_misuse).length === 0 && !data.visual.colour_deviations ? <p className="text-[13px] text-slate-500">None recorded.</p> : (
                <Bars rows={[...Object.entries(data.visual.logo_misuse).map(([k, v]) => ({ label: k.replace("_", " "), value: v, max: Math.max(...Object.values(data.visual.logo_misuse), data.visual.colour_deviations) })),
                  { label: "colour deviations", value: data.visual.colour_deviations, max: Math.max(1, ...Object.values(data.visual.logo_misuse), data.visual.colour_deviations) }]} />
              )}
            </div>
            <div className={`${CARD} p-5 lg:col-span-2`}>
              <h3 className="text-sm font-bold text-slate-900 mb-3">Monthly trends</h3>
              {data.trends.months.length === 0 ? <p className="text-[13px] text-slate-500">No data in range.</p> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="text-left text-slate-500 border-b border-slate-100"><th className="py-1.5 font-medium">Month</th><th className="font-medium">Avg score</th><th className="font-medium">Claims (supported / other)</th><th className="font-medium">Decisions</th><th className="font-medium">Visual findings</th></tr></thead>
                    <tbody>
                      {data.trends.months.map((m) => {
                        const c = data.trends.claims.find((x) => x.month === m) || {};
                        const a = data.trends.approvals.find((x) => x.month === m) || {};
                        const sup = Number(c["Supported"] || 0);
                        const other = Object.entries(c).filter(([k]) => k !== "month" && k !== "Supported").reduce((n, [, v]) => n + Number(v), 0);
                        return (
                          <tr key={m} className="border-b border-slate-100 last:border-0">
                            <td className="py-2 font-medium text-slate-800">{m}</td>
                            <td className="tabular-nums">{data.trends.score.find((x) => x.month === m)?.avg_score ?? "—"}</td>
                            <td className="tabular-nums">{sup} / {other}</td>
                            <td>{Object.entries(a).filter(([k]) => k !== "month").map(([k, v]) => `${k} ${v}`).join(" · ") || "—"}</td>
                            <td className="tabular-nums">{data.trends.visual_findings.find((x) => x.month === m)?.count ?? 0}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <div className={`${CARD} overflow-hidden`}>
            <div className="px-5 pt-4 pb-2 text-sm font-bold text-slate-900">Compliance by campaign <span className="font-normal text-slate-400">(lowest first)</span></div>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead><tr className="text-left text-xs text-slate-500 bg-slate-50/60 border-y border-slate-100">
                  <th className="px-5 py-2 font-medium">Campaign</th><th className="px-3 py-2 font-medium">Product</th><th className="px-3 py-2 font-medium">Department</th>
                  <th className="px-3 py-2 font-medium">Findings</th><th className="px-5 py-2 font-medium text-right">Score</th>
                </tr></thead>
                <tbody>
                  {data.compliance.campaigns.slice(0, 25).map((c) => (
                    <tr key={c.id} className="border-b border-slate-100 last:border-0">
                      <td className="px-5 py-2.5 font-medium text-slate-900 max-w-xs truncate">{c.title}<div className="text-[11px] text-slate-500 font-normal">{c.status} · v{c.version}</div></td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{c.products.join(", ")}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{c.department}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600 tabular-nums">{c.findings} ({c.critical} critical)</td>
                      <td className="px-5 py-2.5 text-right"><Badge tone={c.score >= 80 ? "good" : c.score >= 50 ? "warn" : "bad"}>{c.score}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
