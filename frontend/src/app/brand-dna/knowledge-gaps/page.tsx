"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { SearchCheck, RefreshCw, FileUp, ArrowRight, FileText } from "lucide-react";
import { fetchKnowledgeGaps, KnowledgeGaps, GapStatus } from "@/lib/api";
import { CARD, Badge, Tone, PageHeader, ErrorNote, Loading, BTN_SECONDARY } from "@/components/engines/ui";

const STATUS: Record<GapStatus, { label: string; tone: Tone; dot: string }> = {
  conflict: { label: "Conflict", tone: "bad", dot: "bg-rose-500" },
  missing: { label: "Missing", tone: "warn", dot: "bg-amber-500" },
  stale: { label: "Outdated", tone: "neutral", dot: "bg-slate-400" },
  weak: { label: "Weak source", tone: "info", dot: "bg-sky-500" },
  ok: { label: "Covered", tone: "good", dot: "bg-emerald-500" },
};
const PRIORITY_TONE: Record<string, Tone> = { high: "bad", medium: "warn", low: "neutral" };
const FILTERS: (GapStatus | "all")[] = ["all", "conflict", "missing", "stale", "weak", "ok"];

function Ring({ value }: { value: number }) {
  const r = 46, c = 2 * Math.PI * r;
  const color = value >= 80 ? "#10b981" : value >= 50 ? "#f59e0b" : "#f43f5e";
  return (
    <svg viewBox="0 0 120 120" className="w-32 h-32" role="img" aria-label={`Knowledge completeness ${value}%`}>
      <circle cx="60" cy="60" r={r} fill="none" stroke="#eef2f7" strokeWidth="12" />
      <circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
              strokeDasharray={`${(value / 100) * c} ${c}`} transform="rotate(-90 60 60)" />
      <text x="60" y="58" textAnchor="middle" className="fill-slate-900" style={{ fontSize: 26, fontWeight: 700 }}>{value}%</text>
      <text x="60" y="78" textAnchor="middle" className="fill-slate-500" style={{ fontSize: 10 }}>complete</text>
    </svg>
  );
}

export default function KnowledgeGapsPage() {
  const [data, setData] = useState<KnowledgeGaps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState<GapStatus | "all">("all");

  const load = () => {
    setBusy(true);
    fetchKnowledgeGaps().then((d) => { setData(d); setError(null); }).catch((e) => setError(e.message)).finally(() => setBusy(false));
  };
  useEffect(load, []);

  const items = useMemo(() => (data?.items || []).filter((i) => filter === "all" || i.status === filter), [data, filter]);
  const attrs = data?.products[0]?.attributes.map((a) => a.label) || [];

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/brand-dna", label: "Brand DNA Studio" }}
        eyebrow="Knowledge Gap Detector" icon={<SearchCheck className="w-3.5 h-3.5" />}
        title="What your Brand DNA is still missing"
        description="BrandVault can only verify what it knows. This report inspects products, facts, rules, documents, assets and past claims, then lists missing, conflicting, outdated and weakly-sourced knowledge. Gaps are never filled with guesses — an administrator has to supply them."
        actions={<button onClick={load} disabled={busy} className={BTN_SECONDARY}><RefreshCw className={`w-3.5 h-3.5 ${busy ? "animate-spin" : ""}`} /> Re-analyse</button>}
      />
      <ErrorNote message={error} />
      {!data ? <Loading label="Inspecting Brand DNA…" /> : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className={`${CARD} p-5 lg:col-span-4 flex items-center gap-5`}>
              <Ring value={data.completeness} />
              <div className="space-y-1.5">
                <div className="text-sm font-bold text-slate-900">{data.org.name}</div>
                {(["conflict", "missing", "stale", "weak", "ok"] as GapStatus[]).map((s) => (
                  <div key={s} className="flex items-center gap-2 text-xs text-slate-600">
                    <span className={`w-2 h-2 rounded-full ${STATUS[s].dot}`} /> {STATUS[s].label}
                    <span className="font-semibold text-slate-900 tabular-nums">{data.counts[s] || 0}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className={`${CARD} p-5 lg:col-span-8`}>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><FileUp className="w-4 h-4 text-slate-400" /> Recommended documents to upload</h3>
              {data.recommended_documents.length === 0 ? (
                <p className="mt-2 text-[13px] text-slate-500">Nothing major is missing.</p>
              ) : (
                <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {data.recommended_documents.map((d) => (
                    <li key={d} className="flex items-center gap-2 text-[13px] text-slate-700 rounded-xl bg-slate-50 border border-slate-200 px-3 py-2">
                      <FileText className="w-3.5 h-3.5 text-indigo-500 shrink-0" /> {d}
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-3 text-[11px] text-slate-400">{data.basis}</p>
            </div>
          </div>

          {data.products.length > 0 && (
            <div className={`${CARD} overflow-hidden`}>
              <div className="px-5 pt-4 pb-2 flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900">Product knowledge coverage</h3>
                <Link href="/brand-dna/products" className="text-xs font-semibold text-indigo-600 hover:underline">Open Product Truth →</Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500 border-y border-slate-100 bg-slate-50/60">
                      <th className="px-5 py-2 text-left font-medium">Product</th>
                      {attrs.map((a) => <th key={a} className="px-2 py-2 font-medium whitespace-nowrap">{a}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {data.products.map((p) => (
                      <tr key={p.product_id} className="border-b border-slate-100 last:border-0">
                        <td className="px-5 py-2.5 font-semibold text-slate-800 whitespace-nowrap">{p.product}</td>
                        {p.attributes.map((a) => (
                          <td key={a.attribute} className="px-2 py-2.5 text-center" title={`${a.label}: ${STATUS[a.status].label}${a.value ? ` — ${a.value}` : ""}${a.pending ? " (proposal pending)" : ""}`}>
                            <span className={`inline-block w-3 h-3 rounded-full ${STATUS[a.status].dot} ${a.pending ? "ring-2 ring-violet-300" : ""}`} />
                            <span className="sr-only">{STATUS[a.status].label}</span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className={`${CARD} p-5`}>
            <div className="flex flex-wrap gap-2" role="tablist" aria-label="Filter gaps">
              {FILTERS.map((f) => (
                <button key={f} role="tab" aria-selected={filter === f} onClick={() => setFilter(f)}
                        className={`h-8 px-3 rounded-lg text-xs font-semibold border transition-colors ${filter === f ? "bg-indigo-50 border-indigo-200 text-indigo-800" : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"}`}>
                  {f === "all" ? `All (${data.items.length})` : `${STATUS[f].label} (${data.counts[f] || 0})`}
                </button>
              ))}
            </div>
            <ul className="mt-4 divide-y divide-slate-100">
              {items.map((i) => (
                <li key={i.key} className="py-3.5 flex flex-col sm:flex-row sm:items-start gap-3">
                  <div className="flex items-center gap-1.5 sm:w-40 shrink-0">
                    <Badge tone={STATUS[i.status].tone}>{STATUS[i.status].label}</Badge>
                    {i.status !== "ok" && <Badge tone={PRIORITY_TONE[i.priority]}>{i.priority}</Badge>}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-semibold text-slate-900">{i.label} <span className="font-normal text-slate-400">· {i.group}</span></div>
                    <p className="text-xs text-slate-600 mt-0.5">{i.detail}</p>
                    {i.evidence && (
                      <p className="text-[11px] text-slate-500 mt-1">
                        {i.evidence.source}{i.evidence.page ? ` · page ${i.evidence.page}` : ""}{i.evidence.excerpt && <> — <i>“{i.evidence.excerpt}”</i></>}
                      </p>
                    )}
                    {i.recommendation && i.status !== "ok" && <p className="text-xs text-indigo-700 mt-1">→ {i.recommendation}</p>}
                  </div>
                  {i.action && i.status !== "ok" && (
                    <Link href={i.action.href} className={BTN_SECONDARY + " shrink-0"}>{i.action.label} <ArrowRight className="w-3.5 h-3.5" /></Link>
                  )}
                </li>
              ))}
              {items.length === 0 && <li className="py-6 text-center text-[13px] text-slate-500">Nothing in this category.</li>}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
