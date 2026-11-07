"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Rocket, Loader2, CheckCircle2, XCircle, AlertTriangle, Clock, MinusCircle, HelpCircle, Send, Settings2, Search } from "lucide-react";
import {
  fetchSubmissions, runLaunchCheck, fetchLaunchReports, fetchLaunchPolicy, saveLaunchPolicy, sendForReview,
  Submission, LaunchReport, LaunchPolicy, CheckStatus, LaunchState,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, Tone, PageHeader, ErrorNote, Loading, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const STATE_TONE: Record<LaunchState, Tone> = {
  "Approved for Launch": "good", "Ready for Review": "info", "Pending Approval": "ai",
  "Blocked by Critical Issues": "bad", "Expired Approval": "warn", "Requires Reanalysis": "warn",
};
const CHECK: Record<CheckStatus, { Icon: typeof CheckCircle2; cls: string; label: string }> = {
  pass: { Icon: CheckCircle2, cls: "text-emerald-600", label: "Passed" },
  fail: { Icon: XCircle, cls: "text-rose-600", label: "Failed" },
  warn: { Icon: AlertTriangle, cls: "text-amber-600", label: "Warning" },
  pending: { Icon: Clock, cls: "text-violet-600", label: "Pending" },
  not_applicable: { Icon: MinusCircle, cls: "text-slate-400", label: "Not applicable" },
  unavailable: { Icon: HelpCircle, cls: "text-sky-600", label: "Can't check" },
};

export default function LaunchReadinessPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const [subs, setSubs] = useState<Submission[] | null>(null);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<Submission | null>(null);
  const [report, setReport] = useState<LaunchReport | null>(null);
  const [history, setHistory] = useState<{ id: string; state: LaunchState; version: number; created_by: string; created_at: string | null }[]>([]);
  const [policy, setPolicy] = useState<LaunchPolicy | null>(null);
  const [editPolicy, setEditPolicy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadSubs = () => fetchSubmissions().then(setSubs).catch((e) => setError(e.message));
  useEffect(() => { loadSubs(); fetchLaunchPolicy().then(setPolicy).catch(() => {}); }, []);

  const check = async (s: Submission) => {
    setSelected(s); setBusy(true); setError(null); setNotice(null);
    try {
      setReport(await runLaunchCheck(s.id));
      setHistory(await fetchLaunchReports(s.id));
    } catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };

  const submitForReview = async () => {
    if (!selected || !report) return;
    setBusy(true); setError(null);
    try {
      const updated = await sendForReview(selected.id, report.submission.version,
        `Sent for review from Launch Readiness (${report.state}; route: ${report.route_to.join(", ") || "Brand reviewer"}).`);
      setNotice("Sent to the review queue. A reviewer must approve it — nothing was published.");
      await loadSubs();
      await check(updated);
    } catch (e: any) { setError(e.message); setBusy(false); }
  };

  const savePolicy = async (mandatory: string[], days: number) => {
    setError(null);
    try { setPolicy(await saveLaunchPolicy({ mandatory, approval_validity_days: days })); setEditPolicy(false); if (selected) check(selected); }
    catch (e: any) { setError(e.message); }
  };

  const list = useMemo(() => (subs || []).filter((s) => s.title.toLowerCase().includes(filter.toLowerCase())), [subs, filter]);

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/approval-hub", label: "Approval Hub" }}
        eyebrow="Campaign Launch Readiness" icon={<Rocket className="w-3.5 h-3.5" />}
        title="Is this campaign ready to go live?"
        description="Runs the 12-point pre-launch checklist against the campaign's real analysis, product facts, claims, translations, approvals and guideline version. It never publishes or approves — a human approval of the current version is always required."
        actions={isAdmin && <button onClick={() => setEditPolicy((v) => !v)} className={BTN_SECONDARY}><Settings2 className="w-3.5 h-3.5" /> Launch policy</button>}
      />
      <ErrorNote message={error} />
      {notice && <div className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">{notice}</div>}

      {editPolicy && policy && <PolicyEditor policy={policy} onSave={savePolicy} onCancel={() => setEditPolicy(false)} />}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className={`${CARD} xl:col-span-4 p-4`}>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" aria-hidden />
            <input aria-label="Filter campaigns" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter campaigns" className={`${INPUT} h-10 pl-9`} />
          </div>
          {!subs ? <Loading /> : (
            <ul className="mt-3 max-h-[640px] overflow-y-auto divide-y divide-slate-100">
              {list.map((s) => (
                <li key={s.id}>
                  <button onClick={() => check(s)}
                          className={`w-full text-left px-2.5 py-2.5 rounded-lg transition-colors ${selected?.id === s.id ? "bg-indigo-50" : "hover:bg-slate-50"}`}>
                    <div className="text-[13px] font-semibold text-slate-800 truncate">{s.title}</div>
                    <div className="text-[11px] text-slate-500">v{s.version} · {s.status} · score {s.overall_score}</div>
                  </button>
                </li>
              ))}
              {list.length === 0 && <li className="py-6 text-center text-[13px] text-slate-500">No campaigns.</li>}
            </ul>
          )}
        </div>

        <div className="xl:col-span-8 space-y-4">
          {!selected ? (
            <div className={`${CARD} p-10 text-center`}>
              <Rocket className="w-8 h-8 text-indigo-400 mx-auto" />
              <h3 className="mt-3 text-base font-bold text-slate-900">Choose a campaign</h3>
              <p className="mt-1 text-[13px] text-slate-500">Select a campaign on the left to run the launch checklist.</p>
            </div>
          ) : busy && !report ? <Loading label="Running checks…" /> : report && (
            <>
              <div className={`${CARD} p-5`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-xs text-slate-500">v{report.submission.version} · {report.submission.status} · by {report.submission.author}</div>
                    <h3 className="text-lg font-bold text-slate-900 truncate">{report.submission.title}</h3>
                  </div>
                  <Badge tone={STATE_TONE[report.state]} className="text-xs px-3 py-1">{report.state}</Badge>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  {(["pass", "fail", "warn", "pending", "unavailable", "not_applicable"] as CheckStatus[]).map((k) => (
                    <span key={k} className="inline-flex items-center gap-1 text-slate-600">
                      {(() => { const C = CHECK[k]; return <C.Icon className={`w-3.5 h-3.5 ${C.cls}`} aria-hidden />; })()} {CHECK[k].label} {report.counts[k] || 0}
                    </span>
                  ))}
                </div>
                {report.route_to.length > 0 && (
                  <p className="mt-3 text-[13px] text-slate-700">Route to: <b>{report.route_to.join(", ")}</b></p>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  <button onClick={() => check(selected)} disabled={busy} className={BTN_SECONDARY}>
                    {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Rocket className="w-3.5 h-3.5" />} Re-run checks
                  </button>
                  {["Ready for Review", "Requires Reanalysis"].includes(report.state) && report.submission.status !== "Pending Review" && (
                    <button onClick={submitForReview} disabled={busy || report.state === "Requires Reanalysis"} className={BTN_PRIMARY}
                            title={report.state === "Requires Reanalysis" ? "Re-analyse the campaign against the current guideline first" : undefined}>
                      <Send className="w-4 h-4" /> Send for review
                    </button>
                  )}
                  {report.state === "Requires Reanalysis" && (
                    <Link href={`/content-intelligence?submissionId=${report.submission.id}`} className={BTN_SECONDARY}>Re-analyse in Content Intelligence</Link>
                  )}
                </div>
                <p className="mt-3 text-[11px] text-slate-400">{report.note}</p>
              </div>

              <div className={`${CARD} overflow-hidden`}>
                <ul className="divide-y divide-slate-100">
                  {report.checks.map((c) => {
                    const C = CHECK[c.status];
                    return (
                      <li key={c.key} className="px-5 py-3.5 flex items-start gap-3">
                        <C.Icon className={`w-5 h-5 mt-0.5 shrink-0 ${C.cls}`} aria-label={C.label} />
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="text-[13px] font-semibold text-slate-900">{c.label}</span>
                            {c.mandatory && <Badge tone="neutral">mandatory</Badge>}
                            {c.route_to && c.status !== "pass" && c.status !== "not_applicable" && <span className="text-[11px] text-slate-400">· {c.route_to}</span>}
                          </div>
                          <p className="text-xs text-slate-600 mt-0.5">{c.detail}</p>
                          {c.evidence.length > 0 && (
                            <ul className="mt-1 space-y-0.5">{c.evidence.map((e, i) => <li key={i} className="text-[11px] text-slate-500">• {e}</li>)}</ul>
                          )}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>

              {report.unresolved_findings.length > 0 && (
                <div className={`${CARD} p-5`}>
                  <h4 className="text-sm font-bold text-slate-900">Unresolved findings ({report.unresolved_findings.length})</h4>
                  <ul className="mt-2 space-y-1.5">
                    {report.unresolved_findings.slice(0, 10).map((f) => (
                      <li key={f.id} className="text-xs text-slate-700 flex flex-wrap gap-1.5 items-center">
                        <Badge tone={f.severity === "CRITICAL" ? "bad" : f.severity === "WARNING" ? "warn" : "neutral"}>{f.severity}</Badge>
                        <span className="text-slate-500">{f.category}:</span> “{f.text}” <span className="text-indigo-700">→ {f.suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {history.length > 0 && (
                <div className={`${CARD} p-5`}>
                  <h4 className="text-sm font-bold text-slate-900">Readiness history</h4>
                  <ul className="mt-2 divide-y divide-slate-100">
                    {history.map((h) => (
                      <li key={h.id} className="py-2 flex items-center justify-between text-xs">
                        <span className="text-slate-600">v{h.version} · {h.created_by} · {h.created_at ? new Date(h.created_at + "Z").toLocaleString() : ""}</span>
                        <Badge tone={STATE_TONE[h.state]}>{h.state}</Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function PolicyEditor({ policy, onSave, onCancel }: { policy: LaunchPolicy; onSave: (m: string[], d: number) => void; onCancel: () => void }) {
  const [mandatory, setMandatory] = useState<string[]>(policy.checks.filter((c) => c.mandatory).map((c) => c.key));
  const [days, setDays] = useState(policy.approval_validity_days);
  return (
    <div className={`${CARD} p-5 space-y-3`}>
      <h3 className="text-sm font-bold text-slate-900">Launch policy <span className="font-normal text-slate-500">— a failed mandatory check blocks launch</span></h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {policy.checks.map((c) => (
          <label key={c.key} className="flex items-center gap-2 text-[13px] text-slate-700 rounded-lg border border-slate-200 px-3 py-2">
            <input type="checkbox" className="w-4 h-4 accent-indigo-600" checked={mandatory.includes(c.key)}
                   onChange={(e) => setMandatory((m) => (e.target.checked ? [...m, c.key] : m.filter((k) => k !== c.key)))} />
            {c.label}
          </label>
        ))}
      </div>
      <label className="flex items-center gap-2 text-[13px] text-slate-700">
        Approvals stay valid for
        <input type="number" min={1} max={730} value={days} onChange={(e) => setDays(Number(e.target.value))} className={`${INPUT} h-9 w-24`} aria-label="Approval validity in days" />
        days
      </label>
      <div className="flex justify-end gap-2">
        <button onClick={onCancel} className={BTN_SECONDARY}>Cancel</button>
        <button onClick={() => onSave(mandatory, days)} className={BTN_SECONDARY + " text-indigo-700"}>Save policy</button>
      </div>
      {policy.updated_by && <p className="text-[11px] text-slate-400">Last changed by {policy.updated_by}</p>}
    </div>
  );
}
