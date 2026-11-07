"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  FileSearch, AlertTriangle, Clock, Award, Sparkles, ArrowRight, ArrowUpRight,
  Check, Rocket, Bot, FileText, ChevronRight, ShieldCheck,
} from "lucide-react";
import {
  fetchSubmissions, fetchRules, fetchAgentRuns, fetchOnboardingStatus, fetchPassports,
  runSampleNovaTest,
  Submission, BrandRule, AgentRun, OnboardingStatus, BrandPassport,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

const GLASS = "bg-white border border-[#E4E4E7] shadow-[0_1px_2px_rgba(10,10,10,0.04)] rounded-xl";

/* ------------------------------ small widgets ----------------------------- */
function Sparkline({ data }: { data: number[] }) {
  const max = Math.max(1, ...data);
  const last = data.length - 1;
  return (
    <div className="h-9 flex flex-col justify-end gap-1.5">
      <div className="flex items-end gap-1 h-6" aria-hidden>
        {data.map((v, i) => (
          <div
            key={i}
            className={`flex-1 rounded-[2px] ${i === last ? "bg-[#0A0A0A]" : "bg-[#D4D4D8]"}`}
            style={{ height: `${v === 0 ? 8 : Math.max(16, (v / max) * 100)}%` }}
          />
        ))}
      </div>
      <div className="text-[11px] text-[#71717A]">Last 6 months</div>
    </div>
  );
}

function Gauge({ value, label, sublabel }: { value: number; label: string; sublabel?: string }) {
  const size = 188, stroke = 16, r = (size - stroke) / 2 - 2, cx = size / 2, cy = size / 2;
  const circ = 2 * Math.PI * r;
  const SWEEP = 270; // leave a 90° gap at the bottom
  const arcLen = (circ * SWEEP) / 360;
  const valLen = arcLen * Math.min(1, Math.max(0, value / 100));
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#E6E6E8" strokeWidth={stroke} strokeLinecap="round"
                strokeDasharray={`${arcLen} ${circ}`} transform={`rotate(135 ${cx} ${cy})`} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#0A0A0A" strokeWidth={stroke} strokeLinecap="round"
                strokeDasharray={`${valLen} ${circ}`} transform={`rotate(135 ${cx} ${cy})`} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-3xl font-bold tracking-tight text-[#0A0A0A]">{value}%</div>
        <div className="text-[11px] font-mono uppercase tracking-wider text-[#737373] mt-0.5">{label}</div>
        {sublabel && <div className="text-[11px] font-mono text-[#A3A3A3] mt-0.5 max-w-[120px]">{sublabel}</div>}
      </div>
    </div>
  );
}

const CLAIM_STATUSES: { key: string; label: string; shade: string }[] = [
  { key: "Supported", label: "Supported", shade: "#0A0A0A" },
  { key: "Needs Human Review", label: "Needs Review", shade: "#404040" },
  { key: "Outdated", label: "Outdated", shade: "#737373" },
  { key: "Unsupported", label: "Unsupported", shade: "#A3A3A3" },
  { key: "Contradicted", label: "Contradicted", shade: "#D4D4D4" },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [rules, setRules] = useState<BrandRule[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<Submission | null>(null);

  const loadData = () => {
    fetchSubmissions().then(setSubmissions).catch(console.error);
    fetchRules().then(setRules).catch(console.error);
    fetchAgentRuns().then((r) => setRuns(r.slice(0, 6))).catch(console.error);
    fetchPassports().then(setPassports).catch(console.error);
    fetchOnboardingStatus().then(setOnboarding).catch(console.error);
  };
  useEffect(() => { loadData(); }, []);

  const handleRunSampleTest = async () => {
    setIsTesting(true);
    try { setTestResult(await runSampleNovaTest()); loadData(); }
    catch (e) { console.error(e); }
    finally { setIsTesting(false); }
  };

  const firstName = (user?.full_name || "there").split(/\s+/)[0];

  const d = useMemo(() => {
    const pending = submissions.filter((s) => s.status === "Pending Review" || s.status === "Analysed").length;
    const critical = submissions.reduce((a, s) => a + s.findings.filter((f) => f.severity === "CRITICAL").length, 0);
    const confirmed = rules.filter((r) => r.is_confirmed).length;
    const coverage = rules.length ? Math.round((confirmed / rules.length) * 100) : 0;

    // last 6 months buckets
    const now = new Date();
    const months = Array.from({ length: 6 }, (_, i) => {
      const dt = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1);
      return { key: `${dt.getFullYear()}-${dt.getMonth()}`, subs: 0, crit: 0 };
    });
    const idx = new Map(months.map((m, i) => [m.key, i]));
    submissions.forEach((s) => {
      const dt = new Date(s.created_at);
      const i = idx.get(`${dt.getFullYear()}-${dt.getMonth()}`);
      if (i === undefined) return;
      months[i].subs += 1;
      months[i].crit += s.findings.filter((f) => f.severity === "CRITICAL").length;
    });

    // claim distribution
    const dist = new Map<string, number>();
    let claimTotal = 0;
    submissions.forEach((s) => s.claim_verifications.forEach((c) => {
      dist.set(c.status, (dist.get(c.status) || 0) + 1); claimTotal += 1;
    }));

    return {
      pending, critical, confirmed, coverage,
      subsSpark: months.map((m) => m.subs),
      critSpark: months.map((m) => m.crit),
      dist, claimTotal,
    };
  }, [submissions, rules]);

  return (
    <div className="space-y-6 select-none">
      {/* Welcome header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">Welcome back, {firstName}</h2>
          <p className="text-[13px] text-[#71717A] mt-1">Brand intelligence, governance and compliance across your workspace.</p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link href="/content-intelligence" className="h-9 px-3.5 text-[13px] font-medium rounded-lg bg-[#0A0A0A] text-white hover:bg-[#27272A] transition-colors flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5" /><span>New Content Review</span>
          </Link>
          <button onClick={handleRunSampleTest} disabled={isTesting}
                  className="h-9 px-3.5 text-[13px] font-medium rounded-lg bg-white border border-[#E4E4E7] text-[#0A0A0A] hover:bg-[#F4F4F5] transition-colors flex items-center gap-2 disabled:opacity-60">
            <ShieldCheck className="w-3.5 h-3.5" /><span>{isTesting ? "Auditing…" : "Verify sample"}</span>
          </button>
        </div>
      </div>

      {/* Sample test result */}
      {testResult && (
        <div className={`${GLASS} p-5 space-y-2`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-[#0A0A0A]">AUDIT COMPLETE: {testResult.title}</span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#0A0A0A] text-white font-medium">Score {testResult.overall_score}/100</span>
          </div>
          <p className="text-xs text-[#0A0A0A] font-mono bg-white p-3 rounded-xl border border-[#E4E4E7]">&ldquo;{testResult.content}&rdquo;</p>
          <Link href={`/content-intelligence?submissionId=${testResult.id}`} className="text-xs font-mono font-bold text-[#0A0A0A] hover:underline flex items-center space-x-1">
            <span>Inspect in Content Intelligence</span><ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Getting Started + Governance pulse */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className={`lg:col-span-7 ${GLASS} p-5`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Rocket className="w-4 h-4 text-[#0A0A0A]" />
              <span className="text-sm font-bold text-[#0A0A0A]">Getting Started</span>
            </div>
            {onboarding && <span className="text-[11px] font-mono text-[#737373]">{onboarding.completion}% complete</span>}
          </div>
          {onboarding ? (
            <>
              <div className="h-2 w-full rounded-full bg-black/10 overflow-hidden mb-4">
                <div className="h-full bg-[#0A0A0A] rounded-full transition-[width] duration-500" style={{ width: `${onboarding.completion}%` }} />
              </div>
              <div className="space-y-1.5">
                {onboarding.steps.slice(0, 5).map((s) => (
                  <Link key={s.key} href={s.href} className="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-white transition-colors group">
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${s.done ? "bg-[#0A0A0A] text-white" : "border border-[#A3A3A3] text-transparent"}`}>
                        <Check className="w-3 h-3" />
                      </span>
                      <span className={`text-xs truncate ${s.done ? "text-[#404040]" : "text-[#0A0A0A] font-semibold"}`}>{s.label}</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-[#A3A3A3] group-hover:translate-x-0.5 transition-transform shrink-0" />
                  </Link>
                ))}
              </div>
              <Link href="/onboarding" className="mt-3 inline-flex items-center text-[11px] font-mono font-bold text-[#0A0A0A] hover:underline">
                Open full setup guide <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
              </Link>
            </>
          ) : <div className="h-24" />}
        </div>

        <div className={`lg:col-span-5 ${GLASS} p-5`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold text-[#0A0A0A]">Governance Pulse</span>
            <span className="text-[11px] font-mono text-[#A3A3A3] uppercase">Policy coverage</span>
          </div>
          <div className="flex items-center gap-4">
            <Gauge value={d.coverage} label="Coverage" sublabel={`${d.confirmed}/${rules.length} rules active`} />
            <div className="flex-1 space-y-1.5 min-w-0">
              {rules.slice(0, 4).map((r) => (
                <div key={r.id} className="flex items-center justify-between text-[11px]">
                  <span className="text-[#404040] truncate pr-2">{r.title}</span>
                  <span className={`font-mono text-[11px] px-1.5 py-0.5 rounded shrink-0 ${r.is_confirmed ? "bg-[#0A0A0A] text-white" : "bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]"}`}>
                    {r.is_confirmed ? "Active" : "Draft"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={FileSearch} label="Content Reviews" value={submissions.length} footer={<Sparkline data={d.subsSpark} />} />
        <KpiCard icon={Clock} label="Pending Approvals" value={d.pending}
                 footer={<ThinBar part={d.pending} total={submissions.length} caption={`${submissions.length ? Math.round((d.pending / submissions.length) * 100) : 0}% of reviews`} />} />
        <KpiCard icon={AlertTriangle} label="Critical Findings" value={d.critical} footer={<Sparkline data={d.critSpark} />} />
        <KpiCard icon={Award} label="Brand Passports" value={passports.length}
                 footer={<div className="text-[11px] text-[#71717A] h-9 flex items-end">Certified governance records</div>} />
      </div>

      {/* Claim distribution + live runs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className={`lg:col-span-5 ${GLASS} p-5`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-bold text-[#0A0A0A]">Claim Verification Distribution</span>
            <span className="text-[11px] font-mono text-[#737373]">{d.claimTotal} claims</span>
          </div>
          <div className="h-3 w-full rounded-full overflow-hidden flex bg-black/5">
            {CLAIM_STATUSES.map((st) => {
              const n = d.dist.get(st.key) || 0;
              const pct = d.claimTotal ? (n / d.claimTotal) * 100 : 0;
              return pct > 0 ? <div key={st.key} style={{ width: `${pct}%`, background: st.shade }} title={`${st.label}: ${n}`} /> : null;
            })}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2">
            {CLAIM_STATUSES.map((st) => {
              const n = d.dist.get(st.key) || 0;
              return (
                <div key={st.key} className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center space-x-2 min-w-0">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: st.shade }} />
                    <span className="text-[#404040] truncate">{st.label}</span>
                  </div>
                  <span className="font-mono font-bold text-[#0A0A0A]">{n}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className={`lg:col-span-7 ${GLASS} overflow-hidden flex flex-col`}>
          <div className="p-4 flex items-center justify-between border-b border-[#E4E4E7]">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#0A0A0A] animate-pulse" />
              <span className="text-sm font-bold text-[#0A0A0A]">Live Agent Runs</span>
            </div>
            <Link href="/agent-control" className="text-[11px] font-mono text-[#737373] hover:text-[#0A0A0A]">View all →</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[#737373] font-mono uppercase text-[11px] border-b border-[#E4E4E7]">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Agent</th>
                  <th className="py-2.5 px-3 font-semibold">Task</th>
                  <th className="py-2.5 px-3 font-semibold">Latency</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/50">
                {runs.length === 0 ? (
                  <tr><td colSpan={4} className="py-6 text-center text-[#737373] font-mono text-[11px]">Agents on standby.</td></tr>
                ) : runs.map((r) => (
                  <tr key={r.id} className="hover:bg-white transition-colors">
                    <td className="py-2.5 px-4 font-bold text-[#0A0A0A] whitespace-nowrap">{r.agent_name}</td>
                    <td className="py-2.5 px-3 text-[#737373] truncate max-w-[180px]">{r.task_name}</td>
                    <td className="py-2.5 px-3 font-mono text-[#404040]">{r.execution_time_ms}ms</td>
                    <td className="py-2.5 px-4 text-right">
                      <span className={`font-mono text-[11px] px-2 py-0.5 rounded-full font-bold ${r.status === "FAILED" ? "bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]" : "bg-[#0A0A0A] text-white"}`}>
                        {r.status === "COMPLETED" ? "Done" : r.status === "RUNNING" ? "Live" : r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent submissions */}
      <div className={`${GLASS} overflow-hidden`}>
        <div className="p-4 flex items-center justify-between border-b border-[#E4E4E7]">
          <div className="text-sm font-bold text-[#0A0A0A]">Recent Content Submissions</div>
          <Link href="/content-intelligence" className="text-[11px] font-mono font-bold text-[#0A0A0A] hover:underline flex items-center space-x-1">
            <span>View all</span><ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[#737373] font-mono uppercase text-[11px] border-b border-[#E4E4E7]">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Content</th>
                <th className="py-2.5 px-3 font-semibold">Author</th>
                <th className="py-2.5 px-3 font-semibold">Risk</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/50">
              {submissions.slice(0, 6).map((s) => {
                const risk = s.overall_score < 50;
                return (
                  <tr key={s.id} className="hover:bg-white transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-7 h-7 rounded-lg bg-white border border-[#E4E4E7] flex items-center justify-center shrink-0"><FileText className="w-3.5 h-3.5 text-[#0A0A0A]" /></div>
                        <div className="truncate max-w-[220px]"><div className="font-bold text-[#0A0A0A] truncate">{s.title}</div><div className="text-[11px] font-mono text-[#737373] truncate">&ldquo;{s.content}&rdquo;</div></div>
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono text-[#404040]">{s.author_name}</td>
                    <td className="py-3 px-3"><span className={`text-[11px] font-mono px-2 py-0.5 rounded-full font-bold ${risk ? "bg-[#0A0A0A] text-white" : "bg-white text-[#0A0A0A] border border-[#E4E4E7]"}`}>{risk ? "High" : "OK"}</span></td>
                    <td className="py-3 px-3"><span className="font-mono text-[11px] px-2 py-0.5 rounded-md border border-[#E4E4E7] bg-white text-[#0A0A0A] font-semibold">{s.status}</span></td>
                    <td className="py-3 px-4 text-right">
                      <Link href={`/content-intelligence?submissionId=${s.id}`} className="px-3 py-1 rounded-lg bg-[#0A0A0A] hover:bg-[#27272A] text-white text-[11px] font-medium inline-flex items-center space-x-1">
                        <span>Inspect</span><ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {submissions.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-xs text-[#737373] font-mono">No submissions yet — run a content review to get started.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------- KPI pieces ------------------------------- */
function KpiCard({ icon: Icon, label, value, footer }: { icon: any; label: string; value: number; footer: React.ReactNode }) {
  return (
    <div className={`${GLASS} p-5 flex flex-col justify-between`}>
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-[#52525B]">{label}</span>
        <Icon className="w-4 h-4 text-[#A1A1AA]" strokeWidth={1.75} aria-hidden />
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight text-[#0A0A0A] tabular-nums">{value}</div>
      <div className="mt-4">{footer}</div>
    </div>
  );
}

function ThinBar({ part, total, caption }: { part: number; total: number; caption: string }) {
  const pct = total ? (part / total) * 100 : 0;
  return (
    <div className="h-9 flex flex-col justify-end">
      <div className="h-1.5 w-full rounded-full bg-[#E4E4E7] overflow-hidden"><div className="h-full bg-[#0A0A0A] rounded-full" style={{ width: `${pct}%` }} /></div>
      <div className="text-[11px] text-[#71717A] mt-2">{caption}</div>
    </div>
  );
}
