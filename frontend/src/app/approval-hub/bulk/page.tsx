"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ListChecks, Search, Loader2, Download, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchQueue, bulkDecide, downloadCsv, QueuePage, QueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, PageHeader, ErrorNote, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const PAGE = 50;
const STATUS_FILTERS = [
  { value: "Pending Review,Analysed", label: "To review" },
  { value: "Revision Requested", label: "Needs revision" },
  { value: "Approved", label: "Approved" },
  { value: "Rejected", label: "Rejected" },
  { value: "", label: "All" },
];
const SORTS = [
  { value: "newest", label: "Newest first" }, { value: "oldest", label: "Oldest first" },
  { value: "score_low", label: "Lowest score first" }, { value: "score_high", label: "Highest score first" },
];
const STATUS_TONE: Record<string, "good" | "bad" | "warn" | "info" | "neutral"> = {
  Approved: "good", Rejected: "bad", "Revision Requested": "warn", "Pending Review": "info", Analysed: "neutral",
};

export default function BulkReviewPage() {
  const { user } = useAuth();
  const canDecide = user?.role === "Administrator" || user?.role === "Reviewer";
  const [status, setStatus] = useState(STATUS_FILTERS[0].value);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("newest");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<QueuePage | null>(null);
  const [selected, setSelected] = useState<Record<string, QueueItem>>({});
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [skipped, setSkipped] = useState<{ title?: string; reason: string }[]>([]);

  const load = (o = offset) => {
    fetchQueue({ status, q: q.trim(), sort, limit: PAGE, offset: o }).then(setPage).catch((e) => setError(e.message));
  };
  useEffect(() => { setOffset(0); load(0); }, [status, sort]);  // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const t = setTimeout(() => { setOffset(0); load(0); }, 300); return () => clearTimeout(t); }, [q]);  // eslint-disable-line react-hooks/exhaustive-deps

  const items = page?.items || [];
  const picked = Object.values(selected);
  const allOnPage = items.length > 0 && items.every((i) => selected[i.id]);
  const withCritical = picked.filter((i) => i.critical > 0).length;
  const toggle = (i: QueueItem) => setSelected((s) => { const n = { ...s }; if (n[i.id]) delete n[i.id]; else n[i.id] = i; return n; });
  const togglePage = () => setSelected((s) => {
    const n = { ...s };
    if (allOnPage) items.forEach((i) => delete n[i.id]); else items.forEach((i) => { n[i.id] = i; });
    return n;
  });
  const selectClean = () => setSelected((s) => { const n = { ...s }; items.filter((i) => i.critical === 0).forEach((i) => { n[i.id] = i; }); return n; });

  const decide = async (decision: "Approved" | "Revision Requested" | "Rejected") => {
    if (!picked.length || comment.trim().length < 3) return;
    setBusy(true); setError(null); setResult(null); setSkipped([]);
    try {
      const r = await bulkDecide(picked.map((i) => ({ submission_id: i.id, expected_version: i.version })), decision, comment.trim());
      setResult(`${decision}: ${r.decided.length} item${r.decided.length === 1 ? "" : "s"}` +
        (decision === "Approved" ? `, ${r.decided.filter((d) => d.passport).length} Brand Passport(s) issued.` : ".") +
        (r.skipped.length ? ` ${r.skipped.length} skipped.` : ""));
      setSkipped(r.skipped);
      setSelected({}); setComment("");
      load();
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };

  const counts = page?.status_counts || {};
  const toReview = (counts["Pending Review"] || 0) + (counts["Analysed"] || 0);
  const pageNo = Math.floor(offset / PAGE) + 1;
  const pages = page ? Math.max(1, Math.ceil(page.total / PAGE)) : 1;
  const go = (o: number) => { setOffset(o); load(o); };
  const stats = useMemo(() => [
    { label: "To review", value: toReview, tone: toReview ? ("warn" as const) : undefined },
    { label: "Approved", value: counts["Approved"] || 0 },
    { label: "Needs revision", value: counts["Revision Requested"] || 0 },
  ], [counts, toReview]);

  return (
    <div className="space-y-6">
      <PageHeader back={{ href: "/approval-hub", label: "Approval Hub" }}
        eyebrow="Bulk Review" icon={<ListChecks className="w-3.5 h-3.5" />}
        title="Review many campaigns at once"
        description="Filter, select and decide in one step. Each decision is still recorded separately under your name, and nothing with an open critical finding can be approved in bulk: those need a look on their own."
        stats={stats}
        actions={<button onClick={() => downloadCsv("/content/export.csv", "brandvault-reviews.csv").catch((e) => setError(e.message))} className={BTN_SECONDARY}><Download className="w-3.5 h-3.5" /> Export all (CSV)</button>} />

      <div className={`${CARD} p-4 flex flex-wrap items-center gap-2`}>
        <div className="flex flex-wrap gap-1.5">
          {STATUS_FILTERS.map((f) => (
            <button key={f.label} onClick={() => setStatus(f.value)} aria-pressed={status === f.value}
                    className={`h-8 px-3 rounded-lg text-xs font-medium ring-1 ${status === f.value ? "bg-indigo-50 text-indigo-700 ring-indigo-200" : "bg-white text-slate-600 ring-slate-200"}`}>{f.label}</button>
          ))}
        </div>
        <div className="relative flex-1 min-w-[180px]">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input aria-label="Search by title or author" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search title or author" className={`${INPUT} h-8 pl-8`} />
        </div>
        <select aria-label="Sort" value={sort} onChange={(e) => setSort(e.target.value)} className={`${INPUT} h-8 w-48`}>
          {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      {canDecide && (
        <div className={`${CARD} p-4 space-y-2 ${picked.length ? "ring-2 ring-indigo-200" : ""}`}>
          <div className="flex flex-wrap items-center gap-2 text-[13px]">
            <b className="text-slate-900">{picked.length} selected</b>
            {withCritical > 0 && <Badge tone="bad">{withCritical} with critical findings: cannot be approved in bulk</Badge>}
            <button onClick={selectClean} className="text-indigo-700 hover:underline text-xs ml-1">Select all without critical findings on this page</button>
            {picked.length > 0 && <button onClick={() => setSelected({})} className="text-slate-500 hover:underline text-xs">Clear</button>}
          </div>
          <div className="flex flex-col md:flex-row gap-2">
            <input aria-label="Reviewer comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Comment recorded with every decision (required)" className={`${INPUT} h-9 flex-1`} />
            <div className="flex gap-2">
              <button disabled={busy || !picked.length || comment.trim().length < 3} onClick={() => decide("Approved")} className={BTN_PRIMARY}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Approve</button>
              <button disabled={busy || !picked.length || comment.trim().length < 3} onClick={() => decide("Revision Requested")} className={BTN_SECONDARY}>Request revision</button>
              <button disabled={busy || !picked.length || comment.trim().length < 3} onClick={() => decide("Rejected")} className={BTN_SECONDARY + " text-rose-700"}>Reject</button>
            </div>
          </div>
          {result && <p className="text-xs text-emerald-700">{result}</p>}
          {skipped.length > 0 && (
            <details className="text-xs text-amber-800"><summary className="cursor-pointer">Why {skipped.length === 1 ? "1 was" : `${skipped.length} were`} skipped</summary>
              <ul className="list-disc pl-5 mt-1">{skipped.map((s, i) => <li key={i}>{s.title || "Item"}: {s.reason}</li>)}</ul></details>
          )}
        </div>
      )}
      <ErrorNote message={error} />

      <div className={`${CARD} overflow-hidden`}>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px] min-w-[720px]">
            <thead className="text-[11px] text-slate-500 bg-slate-50/80">
              <tr>
                {canDecide && <th className="w-10 px-3 py-2"><input type="checkbox" aria-label="Select all on this page" checked={allOnPage} onChange={togglePage} className="accent-indigo-600" /></th>}
                <th className="text-left font-medium py-2 px-2">Campaign</th><th className="font-medium">Status</th><th className="font-medium">Score</th>
                <th className="font-medium">Critical</th><th className="font-medium">Warnings</th><th className="text-left font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {!page ? <tr><td colSpan={7} className="py-8 text-center text-slate-400"><Loader2 className="w-4 h-4 animate-spin inline" /></td></tr>
                : items.length === 0 ? <tr><td colSpan={7} className="py-8 text-center text-slate-500">Nothing here.</td></tr>
                : items.map((i) => (
                  <tr key={i.id} className={selected[i.id] ? "bg-indigo-50/50" : "hover:bg-white/60"}>
                    {canDecide && <td className="px-3"><input type="checkbox" aria-label={`Select ${i.title}`} checked={!!selected[i.id]} onChange={() => toggle(i)} className="accent-indigo-600" /></td>}
                    <td className="py-2 px-2 max-w-0 w-full">
                      <Link href={`/content-intelligence?submissionId=${i.id}`} className="font-medium text-slate-900 hover:text-indigo-700 hover:underline block truncate">{i.title}</Link>
                      <div className="text-[11px] text-slate-500 truncate">{i.author_name}{i.department ? ` · ${i.department}` : ""} · v{i.version}</div>
                    </td>
                    <td className="text-center"><Badge tone={STATUS_TONE[i.status] || "neutral"}>{i.status}</Badge></td>
                    <td className={`text-center tabular-nums font-semibold ${i.score >= 80 ? "text-emerald-600" : i.score >= 50 ? "text-amber-600" : "text-rose-600"}`}>{i.score}</td>
                    <td className="text-center">{i.critical ? <Badge tone="bad">{i.critical}</Badge> : <span className="text-slate-300">0</span>}</td>
                    <td className="text-center tabular-nums">{i.warnings}</td>
                    <td className="text-[12px] text-slate-500 whitespace-nowrap pr-3">{i.updated_at ? new Date(i.updated_at).toLocaleDateString() : ""}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {page && page.total > PAGE && (
          <div className="flex items-center justify-between px-4 py-2 border-t border-slate-100 text-xs text-slate-600">
            <span>{offset + 1}–{Math.min(offset + PAGE, page.total)} of {page.total}</span>
            <div className="flex items-center gap-1">
              <button aria-label="Previous page" disabled={offset === 0} onClick={() => go(Math.max(0, offset - PAGE))} className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
              <span className="tabular-nums">Page {pageNo} of {pages}</span>
              <button aria-label="Next page" disabled={offset + PAGE >= page.total} onClick={() => go(offset + PAGE)} className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
