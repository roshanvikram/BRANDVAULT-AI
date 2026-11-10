"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Layers, Upload, Loader2, Trash2, Play, Download, FileText, ArrowRight } from "lucide-react";
import {
  parseBulkFiles, startBulkCheck, fetchBulkBatch, fetchBulkBatches, downloadCsv,
  BulkItemIn, BulkBatch,
} from "@/lib/api";
import { CARD, Badge, PageHeader, ErrorNote, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const SEP = /^\s*(-{3,}|={3,})\s*$/m;
const MAX = 200;

function splitPasted(text: string): BulkItemIn[] {
  return text.split(SEP).map((p) => p.trim()).filter((p) => p && !/^(-{3,}|={3,})$/.test(p)).map((p, i) => {
    const first = p.split("\n").find((l) => l.trim())?.trim().replace(/^(subject|title|headline)\s*:\s*/i, "") || `Pasted #${i + 1}`;
    return { title: first.slice(0, 80), content: p, source: `Pasted #${i + 1}` };
  });
}

export default function BulkCheckPage() {
  const [pasted, setPasted] = useState("");
  const [items, setItems] = useState<BulkItemIn[]>([]);
  const [readErrors, setReadErrors] = useState<string[]>([]);
  const [batch, setBatch] = useState<BulkBatch | null>(null);
  const [recent, setRecent] = useState<BulkBatch[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadRecent = () => fetchBulkBatches().then(setRecent).catch(() => {});
  useEffect(() => { loadRecent(); return () => { if (timer.current) clearTimeout(timer.current); }; }, []);

  const follow = (id: string) => {
    const tick = async () => {
      try {
        const b = await fetchBulkBatch(id);
        setBatch(b);
        if (b.status === "queued" || b.status === "processing") timer.current = setTimeout(tick, 1500);
        else loadRecent();
      } catch (e: any) { setError(e.message); }
    };
    tick();
  };

  const addFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true); setError(null);
    try {
      const r = await parseBulkFiles(Array.from(files));
      setItems((cur) => [...cur, ...r.items].slice(0, MAX));
      setReadErrors(r.errors);
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };

  const start = async () => {
    const all = [...items, ...splitPasted(pasted)].slice(0, MAX);
    if (!all.length) return;
    setBusy(true); setError(null); setBatch(null);
    try {
      const r = await startBulkCheck(all);
      setItems([]); setPasted("");
      follow(r.job_id);
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };

  const pastedCount = splitPasted(pasted).length;
  const total = items.length + pastedCount;
  const running = batch && (batch.status === "queued" || batch.status === "processing");
  const pct = batch && batch.total ? Math.round((batch.done / batch.total) * 100) : 0;

  return (
    <div className="space-y-6">
      <PageHeader back={{ href: "/content-intelligence", label: "Content Intelligence" }}
        eyebrow="Bulk Check" icon={<Layers className="w-3.5 h-3.5" />}
        title="Check many pieces of copy at once"
        description="Paste several pieces separated by a line of ---, or upload CSV, Excel, Word, PDF or text files. Each piece is checked against your brand rules and facts in the background, exactly like a single check, and appears in the Approval Hub." />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        <div className={`${CARD} p-5 space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900">1. Add copy</h3>
          <label className="block text-xs text-slate-600">Paste (separate pieces with a line containing only ---)
            <textarea value={pasted} onChange={(e) => setPasted(e.target.value)} rows={9} className={`${INPUT} py-2.5 mt-1 resize-y font-[inherit]`}
              placeholder={"Diwali sale: NovaBook Pro now ₹79,999!\n---\nMeet the lightest laptop in its class…"} />
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <label className={BTN_SECONDARY + " cursor-pointer"}><Upload className="w-3.5 h-3.5" /> Upload files
              <input type="file" multiple accept=".csv,.xlsx,.txt,.md,.docx,.pdf,.html,.htm" className="sr-only" onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
            </label>
            <span className="text-[11.5px] text-slate-500">CSV/Excel: one row per piece, with a column named Content, Copy or Text (optional Title and Department).</span>
          </div>
          {readErrors.length > 0 && <ul className="text-[12px] text-amber-800 list-disc pl-4">{readErrors.map((e) => <li key={e}>{e}</li>)}</ul>}
          {items.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">From files ({items.length})
                <button onClick={() => setItems([])} className="ml-auto text-indigo-700 hover:underline">Clear</button></div>
              <ul className="max-h-60 overflow-y-auto divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white/70">
                {items.map((it, i) => (
                  <li key={i} className="flex items-center gap-2 px-3 py-1.5 text-[12.5px]">
                    <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="flex-1 min-w-0 truncate"><b className="text-slate-800">{it.title}</b> <span className="text-slate-400">· {it.content.length} chars{it.department ? ` · ${it.department}` : ""}</span></span>
                    <button aria-label={`Remove ${it.title}`} onClick={() => setItems(items.filter((_, j) => j !== i))} className="p-1 rounded text-slate-400 hover:text-rose-600"><Trash2 className="w-3.5 h-3.5" /></button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex items-center gap-3 pt-1">
            <button onClick={start} disabled={busy || !total || total > MAX || !!running} className={BTN_PRIMARY}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Check {total || ""} piece{total === 1 ? "" : "s"}
            </button>
            <span className={`text-xs ${total > MAX ? "text-rose-700" : "text-slate-500"}`}>Up to {MAX} per batch.</span>
          </div>
          <ErrorNote message={error} />
        </div>

        <div className={`${CARD} p-5`}>
          <h3 className="text-sm font-semibold text-slate-900">2. Results</h3>
          {!batch ? <p className="text-[13px] text-slate-500 mt-2">Start a batch, or open a recent one below.</p> : (
            <div className="mt-2 space-y-3">
              <div>
                <div className="flex items-center justify-between text-xs text-slate-600"><span>{batch.stage}</span><span className="tabular-nums">{batch.done} / {batch.total}</span></div>
                <div className="h-2 rounded-full bg-slate-100 mt-1 overflow-hidden"><div className="h-full bg-indigo-600 transition-all" style={{ width: `${pct}%` }} /></div>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center">
                {[["Checked", batch.summary.checked, ""], ["Clean", batch.summary.clean, "text-emerald-600"], ["Critical", batch.summary.with_critical, batch.summary.with_critical ? "text-rose-600" : ""],
                  ["Avg score", batch.summary.average_score ?? "—", ""]].map(([l, v, c]) => (
                  <div key={l as string} className="rounded-xl bg-white/70 border border-slate-200 py-2"><div className={`text-lg font-semibold tabular-nums ${c}`}>{v}</div><div className="text-[11px] text-slate-500">{l}</div></div>
                ))}
              </div>
              <div className="flex gap-2">
                <button onClick={() => downloadCsv(`/content/bulk/${batch.id}/export.csv`, "batch.csv").catch((e) => setError(e.message))} className={BTN_SECONDARY}><Download className="w-3.5 h-3.5" /> Export CSV</button>
                <Link href="/approval-hub/bulk" className={BTN_SECONDARY}>Review in bulk <ArrowRight className="w-3.5 h-3.5" /></Link>
              </div>
              <div className="max-h-[420px] overflow-y-auto rounded-xl border border-slate-200">
                <table className="w-full text-[12.5px]">
                  <thead className="text-[11px] text-slate-400 bg-slate-50 sticky top-0"><tr><th className="text-left font-medium px-3 py-1.5">Title</th><th className="font-medium">Score</th><th className="font-medium">Critical</th><th className="font-medium">Warnings</th></tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {(batch.results || []).map((r) => (
                      <tr key={r.index}>
                        <td className="px-3 py-1.5 max-w-0 w-full truncate">
                          {r.submission_id ? <Link href={`/content-intelligence?submissionId=${r.submission_id}`} className="text-slate-800 hover:text-indigo-700 hover:underline">{r.title}</Link>
                            : <span className="text-rose-700">{r.title}: {r.error}</span>}
                        </td>
                        <td className="text-center tabular-nums">{r.score ?? ""}</td>
                        <td className="text-center">{r.critical ? <Badge tone="bad">{r.critical}</Badge> : r.submission_id ? <span className="text-slate-300">0</span> : ""}</td>
                        <td className="text-center tabular-nums">{r.warnings ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {recent.length > 0 && (
        <div className={`${CARD} p-5`}>
          <h3 className="text-sm font-semibold text-slate-900">Recent batches</h3>
          <ul className="mt-2 divide-y divide-slate-100">
            {recent.map((b) => (
              <li key={b.id}>
                <button onClick={() => follow(b.id)} className="w-full py-2 flex items-center gap-3 text-left text-[13px] hover:bg-white/60 rounded-lg px-1">
                  <span className="text-slate-500 w-40 shrink-0">{b.created_at ? new Date(b.created_at + "Z").toLocaleString() : ""}</span>
                  <span className="flex-1">{b.done} of {b.total} checked{b.summary.with_critical ? ` · ${b.summary.with_critical} with critical issues` : ""}</span>
                  <Badge tone={b.status === "completed" ? "good" : b.status === "failed" ? "bad" : "info"}>{b.status}</Badge>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
