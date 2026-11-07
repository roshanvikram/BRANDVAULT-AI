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

const GLASS = "bg-white border border-slate-200/90 shadow-[0_1px_3px_rgba(15,23,42,0.03),0_8px_24px_-12px_rgba(79,70,229,0.05)] rounded-2xl";

/* ------------------------------ small widgets ----------------------------- */
function Sparkline({ data, color = "indigo" }: { data: number[]; color?: "indigo" | "rose" }) {
  const max = Math.max(1, ...data);
  const last = data.length - 1;
  const isRose = color === "rose";

  return (
    <div className="h-9 flex flex-col justify-end gap-1.5">
      <div className="flex items-end gap-1 h-6" aria-hidden>
        {data.map((v, i) => (
          <div
            key={i}
            className={`flex-1 rounded-[2px] transition-all ${
              i === last 
                ? (isRose ? "bg-rose-500" : "bg-indigo-600") 
                : (isRose ? "bg-rose-200" : "bg-indigo-200")
            }`}
            style={{ height: `${v === 0 ? 8 : Math.max(16, (v / max) * 100)}%` }}
          />
        ))}
      </div>
      <div className="text-[11px] font-medium text-slate-400">Last 6 months</div>
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
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#E2E8F0" strokeWidth={stroke} strokeLinecap="round"
                strokeDasharray={`${arcLen} ${circ}`} transform={`rotate(135 ${cx} ${cy})`} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#4F46E5" strokeWidth={stroke} strokeLinecap="round"
                strokeDasharray={`${valLen} ${circ}`} transform={`rotate(135 ${cx} ${cy})`} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-3xl font-extrabold tracking-tight text-slate-900">{value}%</div>
        <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 mt-0.5">{label}</div>
        {sublabel && <div className="text-[11px] text-slate-500 mt-0.5 max-w-[120px]">{sublabel}</div>}
      </div>
    </div>
  );
}

const CLAIM_STATUSES: { key: string; label: string; shade: string; badge: string }[] = [
  { key: "Supported", label: "Supported", shade: "#10B981", badge: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  { key: "Needs Human Review", label: "Needs Review", shade: "#F59E0B", badge: "bg-amber-50 text-amber-700 border-amber-200" },
  { key: "Outdated", label: "Outdated", shade: "#8B5CF6", badge: "bg-purple-50 text-purple-700 border-purple-200" },
  { key: "Unsupported", label: "Unsupported", shade: "#64748B", badge: "bg-slate-100 text-slate-700 border-slate-200" },
  { key: "Contradicted", label: "Contradicted", shade: "#F43F5E", badge: "bg-rose-50 text-rose-700 border-rose-200" },
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

    // Six-month sparkline data derived from submissions created_at.
    const now = new Date();
    const subBuckets = [0, 0, 0, 0, 0, 0];
    const critBuckets = [0, 0, 0, 0, 0, 0];
    submissions.forEach((s) => {
      const dt = new Date(s.created_at);
      const monthsAgo = (now.getFullYear() - dt.getFullYear()) * 12 + (now.getMonth() - dt.getMonth());
      if (monthsAgo >= 0 && monthsAgo < 6) {
        const slot = 5 - monthsAgo;
        subBuckets[slot] += 1;
        critBuckets[slot] += s.findings.filter((f) => f.severity === "CRITICAL").length;
      }
    });

    // Claim distribution across all submissions
    const dist = new Map<string, number>();
    submissions.forEach((s) => {
      (s.claim_verifications || []).forEach((c) => {
        dist.set(c.status, (dist.get(c.status) || 0) + 1);
      });
    });
    const claimTotal = Array.from(dist.values()).reduce((a, b) => a + b, 0);

    return {
      pending,
      critical,
      confirmed,
      coverage,
      subsSpark: subBuckets,
      critSpark: critBuckets,
      dist,
      claimTotal,
    };
  }, [submissions, rules]);

  return (
    <div className="space-y-6 select-none">
      {/* Welcome header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Welcome back, {firstName} 👋</h2>
          <p className="text-[13px] text-slate-500 mt-1">Brand intelligence, real-time claim verification and governance telemetry.</p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link href="/content-intelligence" className="h-9 px-4 text-[13px] font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white shadow-sm shadow-indigo-200 transition-all flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5" /><span>New Content Review</span>
          </Link>
          <button onClick={handleRunSampleTest} disabled={isTesting}
                  className="h-9 px-4 text-[13px] font-semibold rounded-xl bg-white border border-slate-200 text-slate-700 hover:text-indigo-600 hover:bg-slate-50 hover:border-slate-300 transition-all flex items-center gap-2 disabled:opacity-60 shadow-sm">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" /><span>{isTesting ? "Auditing…" : "Verify Sample"}</span>
          </button>
        </div>
      </div>

      {/* Sample test result callout */}
      {testResult && (
        <div className={`${GLASS} p-5 space-y-3 border-indigo-200 bg-gradient-to-br from-indigo-50/40 via-white to-sky-50/30`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-ping" />
              <span className="text-xs font-bold text-slate-900">AUDIT COMPLETE: {testResult.title}</span>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
              Health Score: {testResult.overall_score}/100
            </span>
          </div>
          <p className="text-xs text-slate-800 bg-white/90 p-3.5 rounded-xl border border-indigo-100 italic">&ldquo;{testResult.content}&rdquo;</p>
          <div className="flex justify-end pt-1">
            <Link href={`/content-intelligence?submissionId=${testResult.id}`} className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1.5">
              <span>Inspect Findings in Content Intelligence Studio</span><ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Getting Started + Governance pulse */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className={`lg:col-span-7 ${GLASS} p-5 flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2.5">
                <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100 flex items-center justify-center">
                  <Rocket className="w-4 h-4" />
                </div>
                <span className="text-sm font-bold text-slate-900">Getting Started</span>
              </div>
              {onboarding && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                  {onboarding.completion}% complete
                </span>
              )}
            </div>
            {onboarding ? (
              <>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden mb-4">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-violet-600 rounded-full transition-[width] duration-500" style={{ width: `${onboarding.completion}%` }} />
                </div>
                <div className="space-y-1.5">
                  {onboarding.steps.slice(0, 5).map((s) => (
                    <Link key={s.key} href={s.href} className="flex items-center justify-between px-3 py-2 rounded-xl hover:bg-slate-50 transition-colors group border border-transparent hover:border-slate-100">
                      <div className="flex items-center space-x-3 min-w-0">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                          s.done ? "bg-emerald-100 text-emerald-700 border border-emerald-300" : "border-2 border-slate-300 text-transparent"
                        }`}>
                          <Check className="w-3 h-3 stroke-[2.5]" />
                        </span>
                        <span className={`text-xs truncate ${s.done ? "text-slate-600" : "text-slate-900 font-bold"}`}>{s.label}</span>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all shrink-0" />
                    </Link>
                  ))}
                </div>
              </>
            ) : <div className="h-24" />}
          </div>
          <Link href="/onboarding" className="mt-4 inline-flex items-center text-xs font-bold text-indigo-600 hover:text-indigo-800">
            Open full setup guide <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>

        <div className={`lg:col-span-5 ${GLASS} p-5 flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-slate-900">Governance Pulse</span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Policy Coverage</span>
            </div>
            <div className="flex items-center gap-4 mt-2">
              <Gauge value={d.coverage} label="Active" sublabel={`${d.confirmed}/${rules.length} rules active`} />
              <div className="flex-1 space-y-2 min-w-0">
                {rules.slice(0, 4).map((r) => (
                  <div key={r.id} className="flex items-center justify-between text-xs p-1.5 rounded-lg bg-slate-50/70 border border-slate-100">
                    <span className="text-slate-700 truncate pr-2 font-medium">{r.title}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md shrink-0 border ${
                      r.is_confirmed 
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200" 
                        : "bg-amber-50 text-amber-700 border-amber-200"
                    }`}>
                      {r.is_confirmed ? "Active" : "Draft"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="text-[11px] text-slate-500 pt-3 border-t border-slate-100 flex items-center justify-between">
            <span>Ground Truth Facts</span>
            <span className="font-bold text-slate-900">{rules.length} Active Rules</span>
          </div>
        </div>
      </div>

      {/* KPI cards with colorful light badges */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={FileSearch}
          iconTheme="blue"
          label="Content Reviews"
          value={submissions.length}
          footer={<Sparkline data={d.subsSpark} color="indigo" />}
        />
        <KpiCard
          icon={Clock}
          iconTheme="amber"
          label="Pending Approvals"
          value={d.pending}
          footer={<ThinBar part={d.pending} total={submissions.length} caption={`${submissions.length ? Math.round((d.pending / submissions.length) * 100) : 0}% of reviews queue`} />}
        />
        <KpiCard
          icon={AlertTriangle}
          iconTheme="rose"
          label="Critical Findings"
          value={d.critical}
          footer={<Sparkline data={d.critSpark} color="rose" />}
        />
        <KpiCard
          icon={Award}
          iconTheme="emerald"
          label="Brand Passports"
          value={passports.length}
          footer={<div className="text-xs text-slate-500 h-9 flex items-end font-medium">Cryptographically certified</div>}
        />
      </div>

      {/* Claim distribution + live runs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className={`lg:col-span-5 ${GLASS} p-5 flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold text-slate-900">ClaimDNA Distribution</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">{d.claimTotal} total claims</span>
            </div>
            <div className="h-3 w-full rounded-full overflow-hidden flex bg-slate-100 gap-0.5 p-0.5">
              {CLAIM_STATUSES.map((st) => {
                const n = d.dist.get(st.key) || 0;
                const pct = d.claimTotal ? (n / d.claimTotal) * 100 : 0;
                return pct > 0 ? (
                  <div key={st.key} style={{ width: `${pct}%`, background: st.shade }} className="h-full rounded-sm transition-all" title={`${st.label}: ${n}`} />
                ) : null;
              })}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {CLAIM_STATUSES.map((st) => {
                const n = d.dist.get(st.key) || 0;
                return (
                  <div key={st.key} className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50/70 border border-slate-100">
                    <div className="flex items-center space-x-2 min-w-0">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: st.shade }} />
                      <span className="text-slate-700 truncate font-medium">{st.label}</span>
                    </div>
                    <span className="font-bold text-slate-900 tabular-nums">{n}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="pt-3 text-[11px] text-slate-500 border-t border-slate-100">
            Automated verification against approved facts and marketing rules.
          </div>
        </div>

        {/* Live Agent Runs */}
        <div className={`lg:col-span-7 ${GLASS} overflow-hidden flex flex-col`}>
          <div className="p-4 flex items-center justify-between border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-bold text-slate-900">Live Agent Telemetry</span>
            </div>
            <Link href="/agent-control" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
              View all fleet →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider bg-slate-50/50 border-b border-slate-100">
                <tr>
                  <th className="py-2.5 px-4">Agent</th>
                  <th className="py-2.5 px-3">Task</th>
                  <th className="py-2.5 px-3">Latency</th>
                  <th className="py-2.5 px-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {runs.length === 0 ? (
                  <tr><td colSpan={4} className="py-6 text-center text-slate-400">Agents standing by.</td></tr>
                ) : runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900 whitespace-nowrap flex items-center gap-2">
                      <Bot className="w-3.5 h-3.5 text-indigo-600" />
                      <span>{r.agent_name}</span>
                    </td>
                    <td className="py-3 px-3 text-slate-600 truncate max-w-[180px]">{r.task_name}</td>
                    <td className="py-3 px-3 font-semibold text-slate-700">{r.execution_time_ms}ms</td>
                    <td className="py-3 px-4 text-right">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                        r.status === "FAILED"
                          ? "bg-rose-50 text-rose-700 border-rose-200"
                          : r.status === "RUNNING"
                          ? "bg-indigo-50 text-indigo-700 border-indigo-200 animate-pulse"
                          : "bg-emerald-50 text-emerald-700 border-emerald-200"
                      }`}>
                        {r.status === "COMPLETED" ? "Success" : r.status === "RUNNING" ? "Live" : r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent submissions table */}
      <div className={`${GLASS} overflow-hidden`}>
        <div className="p-4 flex items-center justify-between border-b border-slate-100">
          <div>
            <div className="text-sm font-bold text-slate-900">Recent Content Submissions</div>
            <div className="text-xs text-slate-500">Audited campaigns across your brand workspace</div>
          </div>
          <Link href="/content-intelligence" className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1">
            <span>View all</span><ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider bg-slate-50/50 border-b border-slate-100">
              <tr>
                <th className="py-3 px-4">Campaign Content</th>
                <th className="py-3 px-3">Submitted By</th>
                <th className="py-3 px-3">Risk Level</th>
                <th className="py-3 px-3">Review Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {submissions.slice(0, 6).map((s) => {
                const isCritical = s.overall_score < 50;
                return (
                  <tr key={s.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4 text-indigo-600" />
                        </div>
                        <div className="truncate max-w-[240px]">
                          <div className="font-bold text-slate-900 truncate">{s.title}</div>
                          <div className="text-[11px] text-slate-500 truncate mt-0.5">&ldquo;{s.content}&rdquo;</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-3 text-slate-700 font-medium">{s.author_name}</td>
                    <td className="py-3.5 px-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        isCritical 
                          ? "bg-rose-50 text-rose-700 border-rose-200" 
                          : "bg-emerald-50 text-emerald-700 border-emerald-200"
                      }`}>
                        {isCritical ? "HIGH RISK" : "COMPLIANT"}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md border border-slate-200 bg-slate-50 text-slate-700">
                        {s.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/content-intelligence?submissionId=${s.id}`}
                        className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs border border-indigo-200 transition-colors inline-flex items-center space-x-1"
                      >
                        <span>Inspect</span><ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {submissions.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-xs text-slate-500">
                    No submissions recorded yet. Click &quot;Verify Sample&quot; above to run an instant audit.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------- KPI pieces ------------------------------- */
function KpiCard({
  icon: Icon,
  iconTheme = "blue",
  label,
  value,
  footer,
}: {
  icon: any;
  iconTheme?: "blue" | "amber" | "rose" | "emerald";
  label: string;
  value: number;
  footer: React.ReactNode;
}) {
  const themeClasses = {
    blue: "bg-blue-50 text-blue-600 border-blue-100",
    amber: "bg-amber-50 text-amber-600 border-amber-100",
    rose: "bg-rose-50 text-rose-600 border-rose-100",
    emerald: "bg-emerald-50 text-emerald-600 border-emerald-100",
  }[iconTheme];

  return (
    <div className={`${GLASS} p-5 flex flex-col justify-between hover:shadow-md transition-shadow`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500">{label}</span>
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${themeClasses}`}>
          <Icon className="w-4 h-4" strokeWidth={2} aria-hidden />
        </div>
      </div>
      <div className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900 tabular-nums">{value}</div>
      <div className="mt-4">{footer}</div>
    </div>
  );
}

function ThinBar({ part, total, caption }: { part: number; total: number; caption: string }) {
  const pct = total ? (part / total) * 100 : 0;
  return (
    <div className="h-9 flex flex-col justify-end">
      <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
        <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
      <div className="text-[11px] font-medium text-slate-500 mt-2">{caption}</div>
    </div>
  );
}
