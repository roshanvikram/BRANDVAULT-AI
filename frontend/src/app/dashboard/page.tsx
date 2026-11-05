"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileSearch,
  Dna,
  ArrowRight,
  AlertTriangle,
  Clock,
  Sparkles,
  FileText,
  ChevronRight,
  Rocket,
} from "lucide-react";
import {
  fetchSubmissions,
  fetchPassports,
  fetchRules,
  fetchFacts,
  fetchOnboardingStatus,
  runSampleNovaTest,
  Submission,
  BrandPassport,
  OnboardingStatus,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AnalyticsChart } from "@/components/dashboard/AnalyticsChart";
import { RightActivityPanel } from "@/components/layout/RightActivityPanel";
import { EmptyState } from "@/components/ui/EmptyState";

export default function Dashboard() {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const [rulesCount, setRulesCount] = useState<number>(5);
  const [factsCount, setFactsCount] = useState<number>(4);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<Submission | null>(null);
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);

  const loadData = () => {
    fetchSubmissions().then(setSubmissions).catch(console.error);
    fetchPassports().then(setPassports).catch(console.error);
    fetchRules().then((r) => setRulesCount(r.length)).catch(console.error);
    fetchFacts().then((f) => setFactsCount(f.length)).catch(console.error);
    fetchOnboardingStatus().then(setOnboarding).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunSampleTest = async () => {
    setIsTesting(true);
    try {
      const res = await runSampleNovaTest();
      setTestResult(res);
      loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsTesting(false);
    }
  };

  const pendingApprovalsCount = submissions.filter(
    (s) => s.status === "Pending Review" || s.status === "Analysed"
  ).length;

  const criticalFindingsCount = submissions.reduce(
    (acc, s) => acc + s.findings.filter((f) => f.severity === "CRITICAL").length,
    0
  );

  const firstName = (user?.full_name || "there").split(/\s+/)[0];

  return (
    <div className="flex flex-col xl:flex-row gap-6 items-start select-none">
      <div className="flex-1 w-full space-y-6">
        {/* Header greeting */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-[#0A0A0A] flex items-center space-x-2">
              <span>Welcome back, {firstName}</span>
              <span className="text-xl">👋</span>
            </h2>
            <p className="text-xs text-[#737373] mt-0.5">
              Your brand governance overview. Protect Every Word. Preserve Every Identity.
            </p>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              onClick={handleRunSampleTest}
              disabled={isTesting}
              className="px-4 py-2.5 text-xs font-mono font-bold rounded-xl bg-white border border-[#E5E5E5] hover:border-[#0A0A0A] text-[#0A0A0A] hover:bg-[#F5F5F5] transition-all flex items-center space-x-2 shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isTesting ? "AUDITING..." : "VERIFY SAMPLE TEST CASE"}</span>
            </button>
          </div>
        </div>

        {/* Setup progress (real onboarding completion) */}
        {onboarding && (
          <Link
            href="/onboarding"
            className="block bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-4 hover:border-[#A3A3A3] transition-all group"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center space-x-3 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center shrink-0">
                  <Rocket className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-[#0A0A0A]">
                    Workspace setup — {onboarding.completion === 100 ? "complete" : `${onboarding.completion}%`}
                  </div>
                  <div className="text-[11px] font-mono text-[#737373]">
                    {onboarding.completed}/{onboarding.total} steps{onboarding.is_demo ? " · demo data loaded" : ""}
                  </div>
                </div>
              </div>
              <div className="hidden sm:block flex-1 max-w-[220px]">
                <div className="h-2 w-full rounded-full bg-[#F0F0F0] overflow-hidden">
                  <div className="h-full bg-[#0A0A0A] rounded-full" style={{ width: `${onboarding.completion}%` }} />
                </div>
              </div>
              <span className="text-[11px] font-mono font-bold text-[#0A0A0A] inline-flex items-center shrink-0">
                {onboarding.completion === 100 ? "View guide" : "Finish setup"}
                <ChevronRight className="w-3.5 h-3.5 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </div>
          </Link>
        )}

        {/* Sample test callout */}
        {testResult && (
          <div className="p-5 rounded-2xl border border-[#E5E5E5] bg-white shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-[#0A0A0A]" />
                <span className="text-xs font-mono font-bold text-[#0A0A0A]">
                  AUDIT COMPLETE: {testResult.title}
                </span>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#0A0A0A] text-white font-bold">
                Health Score: {testResult.overall_score}/100
              </span>
            </div>
            <p className="text-xs text-[#0A0A0A] font-mono bg-[#F5F5F5] p-3 rounded-xl border border-[#E5E5E5]">
              "{testResult.content}"
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5]">
                <div className="font-mono text-[#737373] text-[10px] uppercase font-bold mb-1">
                  Findings ({testResult.findings.length})
                </div>
                <ul className="space-y-1">
                  {testResult.findings.map((f) => (
                    <li key={f.id} className="text-[#404040]">
                      • <span className="text-[#0A0A0A] font-bold">[{f.issue_category}]</span> {f.original_text} → <span className="underline font-medium">{f.suggested_correction}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="p-3 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5]">
                <div className="font-mono text-[#737373] text-[10px] uppercase font-bold mb-1">
                  ClaimDNA Verifications ({testResult.claim_verifications.length})
                </div>
                <ul className="space-y-1">
                  {testResult.claim_verifications.map((c) => (
                    <li key={c.id} className="text-[#404040]">
                      • <span className="font-mono text-[#0A0A0A] font-bold">[{c.status.toUpperCase()}]</span> {c.claim_text}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="flex justify-end pt-1">
              <Link
                href={`/content-intelligence?submissionId=${testResult.id}`}
                className="text-xs font-mono font-bold text-[#0A0A0A] hover:underline flex items-center space-x-1"
              >
                <span>Inspect in Content Intelligence Studio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* Metric cards + chart */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
          <div className="lg:col-span-5 grid grid-cols-2 gap-4">
            <div className="bg-white rounded-2xl border border-[#E5E5E5] p-4 shadow-sm flex flex-col justify-between hover:border-[#A3A3A3] transition-all">
              <div className="flex items-center justify-between text-[#737373]">
                <FileSearch className="w-4 h-4 text-[#0A0A0A]" />
                <span className="text-[10px] font-mono text-[#A3A3A3]">LIVE</span>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold tracking-tight text-[#0A0A0A]">{submissions.length}</div>
                <div className="text-[11px] font-mono text-[#737373] mt-0.5 leading-tight">Total Reviews</div>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-[#E5E5E5] p-4 shadow-sm flex flex-col justify-between hover:border-[#A3A3A3] transition-all">
              <div className="flex items-center justify-between text-[#737373]">
                <Clock className="w-4 h-4 text-[#0A0A0A]" />
                <span className="text-[10px] font-mono text-[#A3A3A3]">QUEUE</span>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold tracking-tight text-[#0A0A0A]">{pendingApprovalsCount}</div>
                <div className="text-[11px] font-mono text-[#737373] mt-0.5 leading-tight">Pending Approvals</div>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-[#E5E5E5] p-4 shadow-sm flex flex-col justify-between hover:border-[#A3A3A3] transition-all">
              <div className="flex items-center justify-between text-[#737373]">
                <Dna className="w-4 h-4 text-[#0A0A0A]" />
                <span className="text-[10px] font-mono text-[#A3A3A3]">RULES</span>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold tracking-tight text-[#0A0A0A]">{rulesCount}</div>
                <div className="text-[11px] font-mono text-[#737373] mt-0.5 leading-tight">Active Brand Rules</div>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-[#E5E5E5] p-4 shadow-sm flex flex-col justify-between hover:border-[#A3A3A3] transition-all">
              <div className="flex items-center justify-between text-[#737373]">
                <AlertTriangle className="w-4 h-4 text-[#0A0A0A]" />
                <span className="text-[10px] font-mono text-[#A3A3A3]">ISSUES</span>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold tracking-tight text-[#0A0A0A]">{criticalFindingsCount}</div>
                <div className="text-[11px] font-mono text-[#737373] mt-0.5 leading-tight">Critical Findings</div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-7">
            <AnalyticsChart submissions={submissions} />
          </div>
        </div>

        {/* Recent submissions */}
        <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm overflow-hidden space-y-2">
          <div className="p-5 border-b border-[#F0F0F0] flex items-center justify-between">
            <div>
              <div className="text-sm font-bold text-[#0A0A0A]">Recent Content Submissions</div>
              <div className="text-[11px] font-mono text-[#737373]">
                Showing {submissions.length} campaigns audited against NOVA TECH Brand DNA
              </div>
            </div>
            <Link
              href="/content-intelligence"
              className="text-xs font-mono font-bold text-[#0A0A0A] hover:underline flex items-center space-x-1"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAFAFA] border-b border-[#F0F0F0] text-[#737373] font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-5 font-semibold">Content Title</th>
                  <th className="py-3 px-4 font-semibold">Submitted By</th>
                  <th className="py-3 px-4 font-semibold">Risk Level</th>
                  <th className="py-3 px-4 font-semibold">Review Status</th>
                  <th className="py-3 px-4 font-semibold">Date</th>
                  <th className="py-3 px-5 text-right font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F0F0F0]">
                {submissions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-0">
                      <EmptyState
                        icon={FileSearch}
                        title="No content analysed yet"
                        description="Content Intelligence audits your marketing copy against your approved brand DNA — flagging unsupported claims, pricing conflicts, tone drift and prohibited terms, each with retrieved evidence."
                        actionLabel="Analyse content"
                        actionHref="/content-intelligence"
                        example={<>Try: &ldquo;Introducing the world&apos;s fastest AI laptop! Now only ₹69,999!&rdquo;</>}
                        compact
                      />
                    </td>
                  </tr>
                ) : (
                  submissions.map((sub) => {
                    const isCritical = sub.overall_score < 50;
                    return (
                      <tr key={sub.id} className="hover:bg-[#FAFAFA] transition-colors group">
                        <td className="py-3.5 px-5">
                          <div className="flex items-center space-x-3">
                            <div className="w-7 h-7 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5] flex items-center justify-center shrink-0">
                              <FileText className="w-3.5 h-3.5 text-[#0A0A0A]" />
                            </div>
                            <div className="truncate max-w-[220px]">
                              <div className="font-bold text-[#0A0A0A] truncate">{sub.title}</div>
                              <div className="text-[10px] font-mono text-[#737373] truncate">
                                "{sub.content}"
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-[#404040]">
                          <div className="font-medium text-[#0A0A0A]">{sub.author_name}</div>
                          <div className="text-[10px] text-[#737373]">{sub.author_role}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`text-[10px] font-mono px-2 py-0.5 rounded-full border font-bold ${
                              isCritical
                                ? "bg-[#0A0A0A] text-white border-[#0A0A0A]"
                                : "bg-[#F5F5F5] text-[#0A0A0A] border-[#E5E5E5]"
                            }`}
                          >
                            {isCritical ? "HIGH RISK" : "COMPLIANT"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="font-mono text-[10px] px-2 py-0.5 rounded-md border border-[#E5E5E5] bg-[#F5F5F5] text-[#0A0A0A] font-semibold">
                            {sub.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-[11px] text-[#737373]">
                          {new Date(sub.updated_at || sub.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3.5 px-5 text-right">
                          <Link
                            href={`/content-intelligence?submissionId=${sub.id}`}
                            className="px-3 py-1 rounded-lg bg-[#0A0A0A] hover:bg-[#262626] text-white font-mono text-[10px] font-bold transition-all shadow-sm inline-flex items-center space-x-1"
                          >
                            <span>Inspect</span>
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="p-3 border-t border-[#F0F0F0] flex items-center justify-center space-x-1.5">
            <span className="w-5 h-1.5 rounded-full bg-[#0A0A0A]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4D4D4]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4D4D4]" />
          </div>
        </div>
      </div>

      <RightActivityPanel />
    </div>
  );
}
