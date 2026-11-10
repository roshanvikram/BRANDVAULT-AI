"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Sparkles, ArrowRight, ArrowUpRight, Check, Rocket, Bot, ChevronRight, ShieldCheck,
  FileSearch, Gauge as GaugeIcon, AlertTriangle, Clock, LayoutGrid,
} from "lucide-react";
import {
  fetchSubmissions, fetchRules, fetchAgentRuns, fetchOnboardingStatus, fetchPassports,
  runSampleNovaTest,
  Submission, BrandRule, AgentRun, OnboardingStatus, BrandPassport,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Segmented } from "@/components/engines/ui";
import { AreaSpark, TrendChart, DeltaChip, ChartColor } from "@/components/dashboard/Charts";

/* ------------------------------- time helpers ------------------------------ */
const DAY = 86_400_000;
const toDate = (iso: string) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z");
const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const fmtDay = (d: Date) => d.toLocaleDateString(undefined, { month: "short", day: "numeric" });

type Period = 7 | 30 | 90 | 0;
const PERIODS: { value: Period; label: string }[] = [
  { value: 7, label: "7D" }, { value: 30, label: "30D" }, { value: 90, label: "90D" }, { value: 0, label: "All" },
];

interface Bucket { start: number; end: number; label: string }

/** Buckets for the chosen period: daily up to 30 days, weekly beyond. */
function buildBuckets(period: Period, earliest: number | null): { cur: Bucket[]; prior: Bucket[] | null } {
  const today = startOfDay(new Date()).getTime() + DAY; // end of today
  const days = period || Math.max(28, Math.ceil((today - (earliest ?? today - 28 * DAY)) / DAY));
  const size = days <= 30 ? DAY : 7 * DAY;
  const count = Math.ceil(days / (size / DAY));
  const mk = (offset: number) => Array.from({ length: count }, (_, i) => {
    const end = today - offset - (count - 1 - i) * size;
    const start = end - size;
    return { start, end, label: fmtDay(new Date(size === DAY ? start : start)) };
  });
  return { cur: mk(0), prior: period ? mk(count * size) : null };
}

function series(subs: Submission[], buckets: Bucket[]) {
  return buckets.map((b) => {
    const inB = subs.filter((s) => { const t = toDate(s.created_at).getTime(); return t >= b.start && t < b.end; });
    const crit = inB.reduce((a, s) => a + s.findings.filter((f) => f.severity === "CRITICAL").length, 0);
    const avg = inB.length ? Math.round(inB.reduce((a, s) => a + s.overall_score, 0) / inB.length) : null;
    return { count: inB.length, crit, avg, subs: inB };
  });
}

const pct = (cur: number, prev: number) => (prev > 0 ? Math.round(((cur - prev) / prev) * 100) : null);

/* --------------------------------- widgets --------------------------------- */
function Gauge({ value, size = 150 }: { value: number; size?: number }) {
  const stroke = 12, r = (size - stroke) / 2 - 2, c = size / 2;
  const circ = 2 * Math.PI * r, arc = (circ * 270) / 360, val = arc * Math.min(1, Math.max(0, value / 100));
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full">
        <defs>
          <linearGradient id="gauge" x1="0" x2="1" y1="1" y2="0">
            <stop offset="0%" stopColor="#3B6FEF" /><stop offset="100%" stopColor="#3F5B8F" />
          </linearGradient>
        </defs>
        <circle cx={c} cy={c} r={r} fill="none" stroke="#EFF5FF" strokeWidth={stroke} strokeLinecap="round" strokeDasharray={`${arc} ${circ}`} transform={`rotate(135 ${c} ${c})`} />
        <circle cx={c} cy={c} r={r} fill="none" stroke="url(#gauge)" strokeWidth={stroke} strokeLinecap="round" strokeDasharray={`${val} ${circ}`} transform={`rotate(135 ${c} ${c})`} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-[28px] font-semibold tracking-tight text-slate-900 tabular-nums">{value}%</div>
        <div className="text-[11px] text-slate-500 -mt-0.5">rules active</div>
      </div>
    </div>
  );
}

const CLAIM_STATUSES = [
  { key: "Supported", label: "Supported", shade: "#10B981" },
  { key: "Needs Human Review", label: "Needs review", shade: "#F59E0B" },
  { key: "Outdated", label: "Outdated", shade: "#3F5B8F" },
  { key: "Unsupported", label: "Unsupported", shade: "#9AA1AA" },
  { key: "Contradicted", label: "Contradicted", shade: "#F43F5E" },
];

function scoreTone(score: number) {
  return score >= 80 ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : score >= 50 ? "bg-amber-50 text-amber-700 ring-amber-200" : "bg-rose-50 text-rose-700 ring-rose-200";
}
const STATUS_TONE: Record<string, string> = {
  Approved: "bg-emerald-50 text-emerald-700", "Revision Requested": "bg-amber-50 text-amber-700",
  Rejected: "bg-rose-50 text-rose-700", Analysed: "bg-indigo-50 text-indigo-700", "Pending Review": "bg-sky-50 text-sky-700",
};

function Kpi({ icon: Icon, label, value, delta, chip, spark, color }: {
  icon: any; label: string; value: string; delta: React.ReactNode; chip?: React.ReactNode; spark?: number[]; color: ChartColor;
}) {
  return (
    <div className={`${CARD} p-5 flex flex-col gap-3 hover:border-slate-300/80 transition-colors`}>
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-slate-500">{label}</span>
        <span className="w-7 h-7 rounded-lg bg-slate-50 ring-1 ring-slate-200/80 flex items-center justify-center text-slate-500"><Icon className="w-3.5 h-3.5" aria-hidden /></span>
      </div>
      <div className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[30px] leading-none font-semibold tracking-tight text-slate-900 tabular-nums">{value}</div>
          <div className="mt-2.5">{delta}</div>
        </div>
        {spark ? <div className="w-24 shrink-0"><AreaSpark data={spark} color={color} /></div> : chip}
      </div>
    </div>
  );
}

/* ---------------------------------- page ----------------------------------- */
type Metric = "reviews" | "score" | "critical";

export default function Dashboard() {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [rules, setRules] = useState<BrandRule[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<Submission | null>(null);
  const [period, setPeriod] = useState<Period>(7);
  const [metric, setMetric] = useState<Metric>("reviews");

  const loadData = () => {
    fetchSubmissions().then(setSubmissions).catch(console.error).finally(() => setLoaded(true));
    fetchRules().then(setRules).catch(console.error);
    fetchAgentRuns().then((r) => setRuns(r.slice(0, 5))).catch(console.error);
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
    const earliest = submissions.length ? Math.min(...submissions.map((s) => toDate(s.created_at).getTime())) : null;
    const { cur, prior } = buildBuckets(period, earliest);
    const sc = series(submissions, cur);
    const sp = prior ? series(submissions, prior) : null;
    const flat = (x: ReturnType<typeof series>) => x.flatMap((b) => b.subs);
    const curSubs = flat(sc), priorSubs = sp ? flat(sp) : [];
    const avg = (xs: Submission[]) => (xs.length ? Math.round(xs.reduce((a, s) => a + s.overall_score, 0) / xs.length) : null);
    const crit = (xs: Submission[]) => xs.reduce((a, s) => a + s.findings.filter((f) => f.severity === "CRITICAL").length, 0);
    const pending = submissions.filter((s) => s.status === "Pending Review" || s.status === "Analysed").length;
    const confirmed = rules.filter((r) => r.is_confirmed).length;
    const dist = new Map<string, number>();
    submissions.forEach((s) => (s.claim_verifications || []).forEach((c) => dist.set(c.status, (dist.get(c.status) || 0) + 1)));
    const hasPrior = priorSubs.length > 0;
    return {
      labels: cur.map((b) => b.label),
      sc, sp, hasPrior,
      reviews: curSubs.length, reviewsDelta: sp ? pct(curSubs.length, priorSubs.length) : null,
      score: avg(curSubs), scoreDelta: hasPrior && avg(curSubs) !== null ? (avg(curSubs) as number) - (avg(priorSubs) as number) : null,
      critical: crit(curSubs), criticalDelta: sp ? pct(crit(curSubs), crit(priorSubs)) : null,
      pending, confirmed, coverage: rules.length ? Math.round((confirmed / rules.length) * 100) : 0,
      dist, claimTotal: Array.from(dist.values()).reduce((a, b) => a + b, 0),
    };
  }, [submissions, rules, period]);

  const periodText = period ? `Last ${period} days` : "All time";
  const compareNote = period === 0 ? "All recorded history" : undefined;
  const chart = {
    reviews: { values: d.sc.map((b) => b.count), prior: d.sp?.map((b) => b.count), color: "indigo" as ChartColor, title: "Content reviews", big: String(d.reviews), fmt: (v: number) => String(Math.round(v)) },
    score: { values: d.sc.map((b) => b.avg), prior: d.sp?.map((b) => b.avg), color: "emerald" as ChartColor, title: "Average compliance score", big: d.score === null ? "—" : String(d.score), fmt: (v: number) => String(Math.round(v)) },
    critical: { values: d.sc.map((b) => b.crit), prior: d.sp?.map((b) => b.crit), color: "rose" as ChartColor, title: "Critical findings", big: String(d.critical), fmt: (v: number) => String(Math.round(v)) },
  }[metric];
  const setupDone = onboarding ? onboarding.completion >= 100 : true;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <div className="text-[13px] text-slate-500">Welcome back, {firstName}</div>
          <h2 className="text-[28px] leading-tight font-semibold tracking-tight text-slate-900 mt-0.5">Overview</h2>
          <p className="text-[13px] text-slate-500 mt-1">
            {periodText}{period ? " · compared with the previous period" : ""}
            {onboarding && setupDone && (
              <Link href="/onboarding" className="ml-2 inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 ring-1 ring-emerald-200 rounded-full px-2 py-0.5 align-middle"><Check className="w-3 h-3" /> Setup complete</Link>
            )}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Segmented label="Time period" value={period} options={PERIODS} onChange={setPeriod} />
          <Link href="/dashboard/consistency" className="h-9 px-3 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-colors">
            <LayoutGrid className="w-3.5 h-3.5 text-slate-400" /> Heatmap
          </Link>
          <button onClick={handleRunSampleTest} disabled={isTesting}
                  className="h-9 px-3 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-colors disabled:opacity-60">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" /> {isTesting ? "Checking…" : "Verify sample"}
          </button>
          <Link href="/content-intelligence" className="h-9 px-3.5 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-600/25 transition-colors">
            <Sparkles className="w-3.5 h-3.5" /> New review
          </Link>
        </div>
      </div>

      {/* Sample test result */}
      {testResult && (
        <div className={`${CARD} p-4 flex flex-col md:flex-row md:items-center gap-3 border-indigo-200`}>
          <span className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-lg ring-1 tabular-nums ${scoreTone(testResult.overall_score)}`}>Score {testResult.overall_score}/100</span>
          <p className="flex-1 text-[13px] text-slate-700 truncate"><b className="text-slate-900">{testResult.title}</b> · “{testResult.content}”</p>
          <Link href={`/content-intelligence?submissionId=${testResult.id}`} className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1 shrink-0">
            View findings <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Getting started — only while setup is incomplete */}
      {onboarding && !setupDone && (
        <div className={`${CARD} p-5`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100 flex items-center justify-center"><Rocket className="w-4 h-4" /></span>
              <div>
                <div className="text-sm font-semibold text-slate-900">Finish setting up</div>
                <div className="text-xs text-slate-500">{onboarding.completion}% complete</div>
              </div>
            </div>
            <Link href="/onboarding" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1">Setup guide <ArrowUpRight className="w-3.5 h-3.5" /></Link>
          </div>
          <div className="mt-3 h-1.5 rounded-full bg-slate-100 overflow-hidden"><div className="h-full bg-indigo-500 rounded-full" style={{ width: `${onboarding.completion}%` }} /></div>
          <div className="mt-3 flex flex-wrap gap-2">
            {onboarding.steps.filter((s) => !s.done).slice(0, 4).map((s) => (
              <Link key={s.key} href={s.href} className="text-xs font-medium text-slate-700 bg-slate-50 ring-1 ring-slate-200 rounded-lg px-2.5 py-1.5 hover:ring-indigo-300 hover:text-indigo-700 inline-flex items-center gap-1">{s.label} <ChevronRight className="w-3 h-3" /></Link>
            ))}
          </div>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <Kpi icon={FileSearch} label="Content reviews" value={String(d.reviews)} color="indigo" spark={d.sc.map((b) => b.count)}
             delta={<DeltaChip delta={d.reviewsDelta} note={compareNote} />} />
        <Kpi icon={GaugeIcon} label="Avg. compliance score" value={d.score === null ? "—" : String(d.score)} color="emerald" spark={d.sc.map((b) => b.avg ?? 0)}
             delta={<DeltaChip delta={d.scoreDelta} suffix=" pts" note={compareNote} />} />
        <Kpi icon={AlertTriangle} label="Critical findings" value={String(d.critical)} color="rose" spark={d.sc.map((b) => b.crit)}
             delta={<DeltaChip delta={d.criticalDelta} goodWhenUp={false} note={compareNote} />} />
        <Kpi icon={Clock} label="Awaiting decision" value={String(d.pending)} color="amber"
             delta={<span className="text-[11px] text-slate-400">{submissions.length ? `${Math.round((d.pending / submissions.length) * 100)}% of all reviews · now` : "Nothing submitted yet"}</span>}
             chip={<Link href="/approval-hub" className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-0.5 shrink-0">Open hub <ArrowUpRight className="w-3 h-3" /></Link>} />
      </div>

      {/* Trend + governance */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className={`xl:col-span-8 ${CARD} p-5`}>
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-3 mb-4">
            <div>
              <div className="text-sm font-semibold text-slate-900">{chart.title}</div>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">{chart.big}</span>
                <span className="text-xs text-slate-400">{periodText.toLowerCase()}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-3 text-[11px] text-slate-500">
                <span className="inline-flex items-center gap-1.5"><span className="w-3 h-0.5 rounded bg-indigo-500" style={{ background: chart.color === "emerald" ? "#059669" : chart.color === "rose" ? "#E11D48" : "#2554D9" }} /> This period</span>
                {d.hasPrior && <span className="inline-flex items-center gap-1.5"><span className="w-3 border-t border-dashed border-slate-400" /> Prior period</span>}
              </div>
              <Segmented label="Chart metric" value={metric} onChange={setMetric}
                options={[{ value: "reviews", label: "Reviews" }, { value: "score", label: "Score" }, { value: "critical", label: "Critical" }]} />
            </div>
          </div>
          <TrendChart labels={d.labels} values={chart.values} prior={d.hasPrior ? chart.prior : undefined} color={chart.color} format={chart.fmt}
                      emptyNote={loaded ? "No reviews in this period" : "Loading…"} />
          {period !== 0 && !d.hasPrior && loaded && (
            <p className="mt-3 text-[11px] text-slate-400">No reviews in the previous {period} days, so there is no prior-period line to compare with.</p>
          )}
        </div>

        <div className={`xl:col-span-4 ${CARD} p-5 flex flex-col`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-900">Governance pulse</span>
            <Link href="/brand-dna" className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800">Brand DNA →</Link>
          </div>
          <div className="flex items-center gap-4 mt-3">
            <Gauge value={d.coverage} />
            <dl className="space-y-2.5 text-xs min-w-0 flex-1">
              <div><dt className="text-slate-500">Confirmed rules</dt><dd className="font-semibold text-slate-900 tabular-nums">{d.confirmed} of {rules.length}</dd></div>
              <div><dt className="text-slate-500">Brand passports</dt><dd className="font-semibold text-slate-900 tabular-nums">{passports.length} issued</dd></div>
              <div><dt className="text-slate-500">Reviews all time</dt><dd className="font-semibold text-slate-900 tabular-nums">{submissions.length}</dd></div>
            </dl>
          </div>
          <ul className="mt-4 pt-4 border-t border-slate-100 space-y-1.5 flex-1">
            {rules.slice(0, 4).map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-2 text-xs">
                <span className="text-slate-700 truncate">{r.title}</span>
                <span className={`shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded-md ${r.is_confirmed ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{r.is_confirmed ? "Active" : "Draft"}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recent reviews + claims + agents */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className={`xl:col-span-8 ${CARD} overflow-hidden`}>
          <div className="px-5 py-4 flex items-center justify-between border-b border-slate-100">
            <div>
              <div className="text-sm font-semibold text-slate-900">Recent reviews</div>
              <div className="text-xs text-slate-500">Latest campaigns checked against your Brand DNA</div>
            </div>
            <Link href="/content-intelligence" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-0.5">View all <ChevronRight className="w-3.5 h-3.5" /></Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead className="text-[11px] text-slate-400 font-medium border-b border-slate-100">
                <tr><th className="py-2.5 px-5 font-medium">Campaign</th><th className="py-2.5 px-3 font-medium">Author</th><th className="py-2.5 px-3 font-medium">Score</th><th className="py-2.5 px-3 font-medium">Status</th><th className="py-2.5 px-5" /></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.slice(0, 6).map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/70 transition-colors group">
                    <td className="py-3 px-5 max-w-[280px]">
                      <div className="font-medium text-slate-900 truncate">{s.title}</div>
                      <div className="text-[11px] text-slate-500 truncate">{s.content}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-600 whitespace-nowrap">{s.author_name}</td>
                    <td className="py-3 px-3"><span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md ring-1 tabular-nums ${scoreTone(s.overall_score)}`}>{s.overall_score}</span></td>
                    <td className="py-3 px-3"><span className={`text-[11px] font-medium px-2 py-0.5 rounded-md whitespace-nowrap ${STATUS_TONE[s.status] || "bg-slate-100 text-slate-600"}`}>{s.status}</span></td>
                    <td className="py-3 px-5 text-right">
                      <Link href={`/content-intelligence?submissionId=${s.id}`} aria-label={`Open ${s.title}`} className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 group-hover:text-indigo-600">Open <ArrowRight className="w-3 h-3" /></Link>
                    </td>
                  </tr>
                ))}
                {loaded && submissions.length === 0 && (
                  <tr><td colSpan={5} className="py-10 text-center text-[13px] text-slate-500">No reviews yet. Use “Verify sample” to run a first check.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="xl:col-span-4 space-y-4">
          <div className={`${CARD} p-5`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-slate-900">Claim verification</span>
              <span className="text-[11px] text-slate-500 tabular-nums">{d.claimTotal} claims</span>
            </div>
            <div className="h-2 w-full rounded-full overflow-hidden flex bg-slate-100 gap-px">
              {CLAIM_STATUSES.map((st) => {
                const n = d.dist.get(st.key) || 0;
                return n ? <div key={st.key} style={{ width: `${(n / d.claimTotal) * 100}%`, background: st.shade }} title={`${st.label}: ${n}`} /> : null;
              })}
            </div>
            <ul className="mt-3 space-y-1.5">
              {CLAIM_STATUSES.map((st) => (
                <li key={st.key} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-2 text-slate-600"><span className="w-2 h-2 rounded-full" style={{ background: st.shade }} />{st.label}</span>
                  <span className="font-semibold text-slate-900 tabular-nums">{d.dist.get(st.key) || 0}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className={`${CARD} p-5`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-slate-900">Agent activity</span>
              <Link href="/agent-control" className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800">All runs →</Link>
            </div>
            <ul className="divide-y divide-slate-100">
              {runs.length === 0 && <li className="py-3 text-xs text-slate-400">No agent runs yet.</li>}
              {runs.map((r) => (
                <li key={r.id} className="py-2 flex items-center gap-2.5 text-xs">
                  <span className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0"><Bot className="w-3.5 h-3.5" /></span>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-slate-800 truncate">{r.agent_name}</div>
                    <div className="text-[11px] text-slate-400 truncate">{r.task_name}</div>
                  </div>
                  <span className="text-[11px] text-slate-500 tabular-nums">{r.execution_time_ms}ms</span>
                  <span className={`w-1.5 h-1.5 rounded-full ${r.status === "FAILED" ? "bg-rose-500" : r.status === "RUNNING" ? "bg-indigo-500 animate-pulse" : "bg-emerald-500"}`} title={r.status} />
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
