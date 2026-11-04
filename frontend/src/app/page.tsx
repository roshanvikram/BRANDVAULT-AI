"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  CheckCircle2,
  FileSearch,
  Dna,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Bot,
  Award,
  Clock,
  Sparkles
} from "lucide-react";
import {
  fetchSubmissions,
  fetchPassports,
  fetchRules,
  fetchFacts,
  runSampleNovaTest,
  Submission,
  BrandPassport
} from "@/lib/api";

export default function CommandCenter() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const [rulesCount, setRulesCount] = useState<number>(5);
  const [factsCount, setFactsCount] = useState<number>(4);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<Submission | null>(null);

  const loadData = () => {
    fetchSubmissions().then(setSubmissions).catch(console.error);
    fetchPassports().then(setPassports).catch(console.error);
    fetchRules().then((r) => setRulesCount(r.length)).catch(console.error);
    fetchFacts().then((f) => setFactsCount(f.length)).catch(console.error);
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

  const avgScore =
    submissions.length > 0
      ? Math.round(submissions.reduce((acc, s) => acc + s.overall_score, 0) / submissions.length)
      : 88;

  return (
    <div className="space-y-8 select-none">
      {/* Top Banner / Hero */}
      <div className="border border-[#262626] rounded-lg p-6 bg-[#121212] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#A3A3A3] mb-1">
            <span className="w-2 h-2 rounded-full bg-[#FFFFFF]" />
            <span>ORGANISATION WORKSPACE: NOVA TECH</span>
            <span className="text-[#404040]">|</span>
            <span>ENTERPRISE GOVERNANCE ONLINE</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-[#FFFFFF]">
            Protect Every Word. Preserve Every Identity.
          </h2>
          <p className="text-xs text-[#A3A3A3] mt-1 max-w-2xl">
            Autonomous multi-agent brand compliance and ClaimDNA verification platform. Enforcing terminology, factual accuracy, pricing constraints, and cryptographic Brand Passports.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleRunSampleTest}
            disabled={isTesting}
            className="px-4 py-2 text-xs font-mono font-medium rounded border border-[#737373] bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#FFFFFF] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isTesting ? "RUNNING NOVA AUDIT..." : "VERIFY SAMPLE TEST CASE"}</span>
          </button>
        </div>
      </div>

      {/* Test Execution Output Banner if triggered */}
      {testResult && (
        <div className="p-4 rounded border border-[#404040] bg-[#171717] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-[#FFFFFF]" />
              <span className="text-xs font-mono font-bold text-[#FFFFFF]">
                TEST AUDIT COMPLETE: {testResult.title}
              </span>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded border border-[#737373] bg-[#0A0A0A] text-[#F5F5F5]">
              Score: {testResult.overall_score}/100
            </span>
          </div>
          <p className="text-xs text-[#A3A3A3] font-mono bg-[#0A0A0A] p-2.5 rounded border border-[#262626]">
            "{testResult.content}"
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded bg-[#0A0A0A] border border-[#262626]">
              <div className="font-mono text-[#737373] text-[10px] uppercase mb-1">
                Findings ({testResult.findings.length})
              </div>
              <ul className="space-y-1">
                {testResult.findings.map((f) => (
                  <li key={f.id} className="text-[#A3A3A3]">
                    • <span className="text-[#FFFFFF] font-medium">[{f.issue_category}]</span> {f.original_text} → <span className="text-[#FFFFFF] underline">{f.suggested_correction}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-2.5 rounded bg-[#0A0A0A] border border-[#262626]">
              <div className="font-mono text-[#737373] text-[10px] uppercase mb-1">
                ClaimDNA Verifications ({testResult.claim_verifications.length})
              </div>
              <ul className="space-y-1">
                {testResult.claim_verifications.map((c) => (
                  <li key={c.id} className="text-[#A3A3A3]">
                    • <span className="font-mono text-[#FFFFFF]">[{c.status.toUpperCase()}]</span> {c.claim_text} ({c.category})
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="flex justify-end pt-1">
            <Link
              href={`/content-intelligence?submissionId=${testResult.id}`}
              className="text-xs font-mono text-[#FFFFFF] hover:underline flex items-center space-x-1"
            >
              <span>Inspect in Content Intelligence Studio</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Four Core Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>HEALTH INDEX</span>
            <TrendingUp className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">{avgScore}<span className="text-sm font-normal text-[#737373]">/100</span></div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">Enterprise compliance average</div>
        </div>

        {/* Card 2 */}
        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>ACTIVE RULES</span>
            <Dna className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">{rulesCount}</div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">{factsCount} approved ground-truth facts</div>
        </div>

        {/* Card 3 */}
        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>CAMPAIGN SUBMISSIONS</span>
            <FileSearch className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">{submissions.length}</div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">Processed across RAG pipeline</div>
        </div>

        {/* Card 4 */}
        <div className="p-5 rounded border border-[#262626] bg-[#121212] space-y-2">
          <div className="flex items-center justify-between text-xs text-[#737373] font-mono">
            <span>BRAND PASSPORTS</span>
            <Award className="w-4 h-4 text-[#A3A3A3]" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-[#FFFFFF]">{passports.length}</div>
          <div className="text-[11px] text-[#A3A3A3] font-mono">Cryptographically certified</div>
        </div>
      </div>

      {/* Module Navigation Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold tracking-tight text-[#FFFFFF]">Enterprise Modules</h3>
          <span className="text-xs font-mono text-[#737373]">10 Modules Operational</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/brand-dna"
            className="p-4 rounded border border-[#262626] bg-[#121212] hover:bg-[#171717] hover:border-[#404040] transition-colors space-y-2 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Dna className="w-4 h-4 text-[#A3A3A3] group-hover:text-[#FFFFFF]" />
                <span className="text-xs font-medium text-[#FFFFFF]">Brand DNA Studio</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#737373] group-hover:text-[#FFFFFF] transition-transform group-hover:translate-x-0.5" />
            </div>
            <p className="text-xs text-[#A3A3A3]">
              Upload PDF guidelines, parse rules, configure launch prices (₹79,999), and manage approved terminology.
            </p>
          </Link>

          <Link
            href="/content-intelligence"
            className="p-4 rounded border border-[#262626] bg-[#121212] hover:bg-[#171717] hover:border-[#404040] transition-colors space-y-2 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileSearch className="w-4 h-4 text-[#A3A3A3] group-hover:text-[#FFFFFF]" />
                <span className="text-xs font-medium text-[#FFFFFF]">Content Intelligence</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#737373] group-hover:text-[#FFFFFF] transition-transform group-hover:translate-x-0.5" />
            </div>
            <p className="text-xs text-[#A3A3A3]">
              Three-panel content editor with instant findings, guideline citations, and one-click correction application.
            </p>
          </Link>

          <Link
            href="/claim-dna"
            className="p-4 rounded border border-[#262626] bg-[#121212] hover:bg-[#171717] hover:border-[#404040] transition-colors space-y-2 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-[#A3A3A3] group-hover:text-[#FFFFFF]" />
                <span className="text-xs font-medium text-[#FFFFFF]">ClaimDNA Engine</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-[#737373] group-hover:text-[#FFFFFF] transition-transform group-hover:translate-x-0.5" />
            </div>
            <p className="text-xs text-[#A3A3A3]">
              Evidence-based verification of promotional claims with 5 rigorous truth statuses against verified facts.
            </p>
          </Link>
        </div>
      </div>

      {/* Recent Submissions & Governance Activity Table */}
      <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
        <div className="p-4 border-b border-[#262626] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-[#A3A3A3]" />
            <h3 className="text-xs font-semibold text-[#FFFFFF]">Recent Campaign Audits</h3>
          </div>
          <span className="text-[11px] font-mono text-[#737373]">Live Database Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0A0A0A] border-b border-[#262626] text-[#737373] font-mono uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Title</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Score</th>
                <th className="py-2.5 px-4">Author</th>
                <th className="py-2.5 px-4">Findings</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#262626]">
              {submissions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-xs text-[#737373]">
                    No submissions found. Click "VERIFY SAMPLE TEST CASE" above to run an instant audit.
                  </td>
                </tr>
              ) : (
                submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-[#171717] transition-colors">
                    <td className="py-3 px-4 font-medium text-[#FFFFFF]">{sub.title}</td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-[#404040] bg-[#171717] text-[#F5F5F5]">
                        {sub.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-[#FFFFFF]">{sub.overall_score}/100</td>
                    <td className="py-3 px-4 text-[#A3A3A3]">{sub.author_name}</td>
                    <td className="py-3 px-4 text-[#A3A3A3]">{sub.findings.length} issues</td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/content-intelligence?submissionId=${sub.id}`}
                        className="font-mono text-[11px] text-[#FFFFFF] hover:underline"
                      >
                        Inspect →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
