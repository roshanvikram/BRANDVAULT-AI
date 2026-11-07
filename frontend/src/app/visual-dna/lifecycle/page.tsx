"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CalendarClock, AlertOctagon, AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";
import { fetchLifecycle, Lifecycle, LifecycleState } from "@/lib/api";
import { CARD, Badge, Tone, PageHeader, ErrorNote, Loading, BTN_SECONDARY } from "@/components/engines/ui";

const STATE_TONE: Record<LifecycleState, Tone> = {
  Draft: "neutral", "Pending Approval": "ai", Approved: "good", Active: "good",
  "Expiring Soon": "warn", Expired: "bad", Superseded: "neutral", Archived: "neutral",
};
const ORDER: LifecycleState[] = ["Active", "Approved", "Expiring Soon", "Expired", "Superseded", "Pending Approval", "Draft", "Archived"];
const KINDS: Record<string, string> = { asset: "Brand assets", product_fact: "Product facts", approved_fact: "Approved facts & offers", guideline: "Guidelines", approval: "Approvals" };

export default function LifecyclePage() {
  const [data, setData] = useState<Lifecycle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<LifecycleState | "all">("all");
  const [kind, setKind] = useState<string>("all");
  const [busy, setBusy] = useState(false);

  const load = () => { setBusy(true); fetchLifecycle().then((d) => { setData(d); setError(null); }).catch((e) => setError(e.message)).finally(() => setBusy(false)); };
  useEffect(load, []);

  const items = useMemo(() => (data?.items || []).filter((i) => (state === "all" || i.state === state) && (kind === "all" || i.kind === kind)), [data, state, kind]);

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/visual-dna/forensics", label: "Asset Library" }}
        eyebrow="Asset Lifecycle & Expiry" icon={<CalendarClock className="w-3.5 h-3.5" />}
        title="Keep outdated brand material out of new campaigns"
        description="Every asset, product fact, offer, guideline and approval with its lifecycle state. Superseded and expired items are kept as history; only approved, currently valid assets are recommended as replacements."
        actions={<button onClick={load} disabled={busy} className={BTN_SECONDARY}><RefreshCw className={`w-3.5 h-3.5 ${busy ? "animate-spin" : ""}`} /> Refresh</button>}
      />
      <ErrorNote message={error} />
      {!data ? <Loading label="Checking lifecycle…" /> : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {ORDER.map((s) => (
              <button key={s} onClick={() => setState(state === s ? "all" : s)}
                      className={`${CARD} p-3 text-left transition-all ${state === s ? "ring-2 ring-indigo-300" : "hover:border-slate-300"}`}>
                <div className="text-[11px] text-slate-500">{s}</div>
                <div className="text-xl font-bold text-slate-900 tabular-nums">{data.counts[s] || 0}</div>
              </button>
            ))}
          </div>

          {data.alerts.length > 0 && (
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Alerts for administrators</h3>
              <ul className="mt-2 space-y-2">
                {data.alerts.map((a, i) => (
                  <li key={i} className={`flex items-start justify-between gap-3 rounded-xl border px-3.5 py-2.5 ${a.level === "critical" ? "border-rose-200 bg-rose-50/50" : "border-amber-200 bg-amber-50/50"}`}>
                    <span className="flex items-start gap-2 text-[13px] text-slate-800">
                      {a.level === "critical" ? <AlertOctagon className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" /> : <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />}
                      {a.text}
                    </span>
                    <Link href={a.href} className="text-xs font-semibold text-indigo-700 shrink-0 inline-flex items-center gap-1">Open <ArrowRight className="w-3 h-3" /></Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.affected_campaigns.length > 0 && (
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Campaigns using outdated information</h3>
              <ul className="mt-2 divide-y divide-slate-100">
                {data.affected_campaigns.map((c) => (
                  <li key={c.submission_id + c.outdated.join()} className="py-2.5 flex flex-wrap items-center justify-between gap-2">
                    <span className="text-[13px] font-medium text-slate-800">{c.title} <span className="text-slate-400 font-normal">· {c.status}</span></span>
                    <span className="text-xs text-rose-700">{c.outdated.join("; ")}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className={`${CARD} overflow-hidden`}>
            <div className="px-5 pt-4 pb-3 flex flex-wrap gap-2">
              {["all", ...Object.keys(KINDS)].map((k) => (
                <button key={k} onClick={() => setKind(k)}
                        className={`h-8 px-3 rounded-lg text-xs font-semibold border ${kind === k ? "bg-indigo-50 border-indigo-200 text-indigo-800" : "bg-white border-slate-200 text-slate-600"}`}>
                  {k === "all" ? "Everything" : KINDS[k]}
                </button>
              ))}
              {state !== "all" && <button onClick={() => setState("all")} className="h-8 px-3 rounded-lg text-xs text-slate-500 hover:underline">Clear “{state}”</button>}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead><tr className="text-left text-xs text-slate-500 bg-slate-50/60 border-y border-slate-100">
                  <th className="px-5 py-2 font-medium">Item</th><th className="px-3 py-2 font-medium">Type</th><th className="px-3 py-2 font-medium">Valid until</th>
                  <th className="px-3 py-2 font-medium">Seen in images</th><th className="px-5 py-2 font-medium text-right">State</th>
                </tr></thead>
                <tbody>
                  {items.map((i) => (
                    <tr key={i.kind + i.id} className="border-b border-slate-100 last:border-0 align-top">
                      <td className="px-5 py-2.5"><Link href={i.href} className="font-medium text-slate-900 hover:text-indigo-700">{i.name}</Link><div className="text-[11px] text-slate-500 truncate max-w-md">{i.detail}</div></td>
                      <td className="px-3 py-2.5 text-xs text-slate-500 whitespace-nowrap">{i.category}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600 whitespace-nowrap">{i.valid_until ? new Date(i.valid_until).toLocaleDateString() : "—"}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{i.usage === null ? "—" : i.usage}</td>
                      <td className="px-5 py-2.5 text-right whitespace-nowrap"><Badge tone={STATE_TONE[i.state]}>{i.state}</Badge></td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={5} className="px-5 py-6 text-center text-slate-500">Nothing here.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
          <p className="text-[11px] text-slate-400">“Expiring soon” means within {data.expiring_window_days} days. Approvals are valid for {data.approval_validity_days} days (set in the Launch policy).</p>
        </>
      )}
    </div>
  );
}
