"use client";

import { useEffect, useState } from "react";
import { MessageSquareWarning, Upload, Loader2, Plus, Trash2, FileDown } from "lucide-react";
import { fetchReputation, uploadFeedback, addFeedback, removeFeedbackBatch, ReputationOverview } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, PageHeader, ErrorNote, Loading, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const TEMPLATE = "text,rating,date,channel,product\n\"Battery lasts all day, impressed\",5,2026-11-01,Amazon,\n\"Stopped working after a week\",1,2026-11-03,Support ticket,\n";

export default function ReputationPage() {
  const { user } = useAuth();
  const canUpload = user?.role === "Administrator" || user?.role === "Reviewer";
  const isAdmin = user?.role === "Administrator";
  const [days, setDays] = useState(90);
  const [data, setData] = useState<ReputationOverview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [manual, setManual] = useState({ text: "", rating: "" });

  const load = () => fetchReputation(days).then((d) => { setData(d); setError(null); }).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [days]);

  const upload = async (f: File) => {
    setBusy(true); setError(null); setNotice(null);
    try {
      const r = await uploadFeedback(f);
      setNotice(`Imported ${r.imported} record(s)${r.skipped ? `, skipped ${r.skipped}` : ""}.`);
      load();
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };
  const template = () => {
    const url = URL.createObjectURL(new Blob([TEMPLATE], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "feedback-template.csv"; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/risk-radar", label: "Risk Radar" }}
        eyebrow="Brand Reputation Early Warning" icon={<MessageSquareWarning className="w-3.5 h-3.5" />}
        title="What customers are telling you"
        description="Upload authorised feedback — review exports, support tickets, surveys — to see sentiment, recurring complaints, affected products and feedback that disputes your campaign claims. Sentiment is an automated estimate, not confirmed customer opinion."
        actions={<select aria-label="Time window" value={days} onChange={(e) => setDays(Number(e.target.value))} className={`${INPUT} h-9 w-36`}>
          {[30, 90, 365, 0].map((d) => <option key={d} value={d}>{d ? `Last ${d} days` : "All time"}</option>)}
        </select>}
      />
      <ErrorNote message={error} />
      {notice && <div className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">{notice}</div>}

      {canUpload && (
        <div className={`${CARD} p-4 flex flex-col lg:flex-row lg:items-center gap-3`}>
          <label className={BTN_PRIMARY + " cursor-pointer"}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Upload CSV / JSON
            <input type="file" accept=".csv,.json,text/csv,application/json" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ""; }} />
          </label>
          <button onClick={template} className={BTN_SECONDARY}><FileDown className="w-3.5 h-3.5" /> Template</button>
          <div className="flex-1 flex flex-col sm:flex-row gap-2">
            <input aria-label="Feedback text" value={manual.text} onChange={(e) => setManual({ ...manual, text: e.target.value })} placeholder="Or add one piece of feedback…" className={`${INPUT} h-10`} />
            <input aria-label="Rating 1 to 5" value={manual.rating} onChange={(e) => setManual({ ...manual, rating: e.target.value.replace(/[^1-5]/g, "").slice(0, 1) })} placeholder="★ 1–5" className={`${INPUT} h-10 w-24`} />
            <button disabled={manual.text.trim().length < 3} onClick={async () => { try { await addFeedback({ text: manual.text.trim(), rating: manual.rating ? Number(manual.rating) : undefined, channel: "manual" }); setManual({ text: "", rating: "" }); load(); } catch (e: any) { setError(e.message); } }} className={BTN_SECONDARY + " h-10"}><Plus className="w-3.5 h-3.5" /> Add</button>
          </div>
        </div>
      )}

      {!data ? <Loading /> : data.records === 0 ? (
        <div className={`${CARD} p-10 text-center`}>
          <MessageSquareWarning className="w-8 h-8 text-indigo-400 mx-auto" />
          <h3 className="mt-3 text-base font-bold text-slate-900">No feedback in this window</h3>
          <p className="mt-1 text-[13px] text-slate-500 max-w-md mx-auto">{canUpload ? "Upload an export with a text column (and optional rating, date, channel, product), or download the template." : "Ask a Reviewer or Administrator to upload authorised feedback."}</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            {[["Records", data.records], ["Positive", data.sentiment.positive], ["Neutral", data.sentiment.neutral], ["Negative", data.sentiment.negative],
              ["Negative share", data.sentiment.negative_share === null ? "—" : `${data.sentiment.negative_share}%`]].map(([k, v]) => (
              <div key={k as string} className={`${CARD} p-3.5`}><div className="text-[11px] text-slate-500">{k}</div><div className="text-xl font-bold text-slate-900 tabular-nums">{v}</div></div>
            ))}
          </div>

          {data.risks.length > 0 && (
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Early warnings</h3>
              <ul className="mt-2 space-y-2">
                {data.risks.map((r, i) => (
                  <li key={i} className={`rounded-xl border p-3.5 ${r.level === "high" ? "border-rose-200 bg-rose-50/40" : "border-amber-200 bg-amber-50/40"}`}>
                    <div className="flex items-center gap-2"><Badge tone={r.level === "high" ? "bad" : "warn"}>{r.level}</Badge><span className="text-[13px] font-semibold text-slate-900">{r.theme}</span></div>
                    <p className="mt-1 text-xs text-slate-600">{r.why}</p>
                    <p className="mt-1 text-xs text-indigo-700">→ {r.investigate}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Complaint categories</h3>
              <ul className="mt-2 space-y-2.5">
                {data.categories.map((c) => (
                  <li key={c.category}>
                    <div className="flex items-center justify-between text-xs"><span className="text-slate-700">{c.category}</span><span className="tabular-nums text-slate-900 font-semibold">{c.negative} negative / {c.mentions}</span></div>
                    <div className="mt-1 h-1.5 rounded-full bg-slate-100 overflow-hidden"><div className="h-full bg-rose-500 rounded-full" style={{ width: `${c.negative_share}%` }} /></div>
                    {c.samples[0] && <p className="mt-1 text-[11px] text-slate-500 italic line-clamp-1">“{c.samples[0]}”</p>}
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-4">
              <div className={`${CARD} p-5`}>
                <h3 className="text-sm font-bold text-slate-900">Feedback disputing campaign claims</h3>
                {data.campaign_related.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">None found.</p> : (
                  <ul className="mt-2 space-y-2">
                    {data.campaign_related.slice(0, 5).map((c) => (
                      <li key={c.submission_id} className="text-xs"><b className="text-slate-800">{c.title}</b> — {c.negative_mentions} negative mention(s) of {c.disputed.join(", ")}<p className="text-slate-500 italic line-clamp-1">“{c.samples[0]}”</p></li>
                    ))}
                  </ul>
                )}
              </div>
              <div className={`${CARD} p-5`}>
                <h3 className="text-sm font-bold text-slate-900">Recurring phrases in negative feedback</h3>
                <div className="mt-2 flex flex-wrap gap-1.5">{data.recurring_phrases.map((p) => <Badge key={p.phrase} tone="neutral">{p.phrase} · {p.count}</Badge>)}{!data.recurring_phrases.length && <span className="text-[13px] text-slate-500">None yet.</span>}</div>
              </div>
              <div className={`${CARD} p-5`}>
                <h3 className="text-sm font-bold text-slate-900">Trend</h3>
                {data.trend_note ? <p className="mt-1 text-[13px] text-amber-700">{data.trend_note}</p> : (
                  <p className="mt-1 text-[13px] text-slate-700">{data.negative_rising ? "Negative share is rising week on week." : "No significant rise in negative share."}</p>
                )}
                <ul className="mt-2 text-xs text-slate-600 space-y-0.5">{data.trend.slice(-6).map((t) => <li key={t.week}>Week of {t.week}: {t.negative}/{t.total} negative ({t.negative_share}%)</li>)}</ul>
              </div>
            </div>
          </div>

          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-bold text-slate-900">Products</h3>
            <ul className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {data.products.map((p) => <li key={p.product} className="text-xs rounded-lg border border-slate-200 px-3 py-2 flex justify-between"><span className="text-slate-800">{p.product}</span><span className="tabular-nums">{p.negative} neg · {p.positive} pos · {p.total} total</span></li>)}
            </ul>
            <div className="mt-4 text-[11px] text-slate-400">Sources: {Object.entries(data.sources).map(([k, v]) => `${k} (${v})`).join(", ")} · engines: {Object.entries(data.engines).map(([k, v]) => `${k} ${v}`).join(", ")}</div>
            {isAdmin && data.batches.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {data.batches.map((b) => (
                  <button key={b.batch_id} onClick={async () => { if (confirm(`Remove ${b.records} record(s) from ${b.source}?`)) { await removeFeedbackBatch(b.batch_id); load(); } }} className={BTN_SECONDARY}>
                    <Trash2 className="w-3.5 h-3.5" /> Remove {b.source} ({b.records})
                  </button>
                ))}
              </div>
            )}
            <p className="mt-3 text-[11px] text-slate-400">{data.note}</p>
          </div>
        </>
      )}
    </div>
  );
}
