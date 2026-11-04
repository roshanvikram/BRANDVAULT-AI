"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  FileSearch,
  Sparkles,
  ShieldCheck,
  BookOpen,
  ArrowRight
} from "lucide-react";
import {
  fetchSubmissions,
  runSampleNovaTest,
  analyzeContent,
  Submission,
  ClaimVerification
} from "@/lib/api";

export default function ClaimDNA() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [activeSubmission, setActiveSubmission] = useState<Submission | null>(null);
  const [customClaim, setCustomClaim] = useState("");
  const [runningTest, setRunningTest] = useState(false);

  const loadSubmissions = () => {
    fetchSubmissions().then((subs) => {
      setSubmissions(subs);
      if (subs.length > 0 && !activeSubmission) {
        setActiveSubmission(subs[0]);
      }
    }).catch(console.error);
  };

  useEffect(() => {
    loadSubmissions();
  }, []);

  const handleRunSampleNovaTest = async () => {
    setRunningTest(true);
    try {
      const res = await runSampleNovaTest();
      setActiveSubmission(res);
      loadSubmissions();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningTest(false);
    }
  };

  const handleTestCustomClaim = async () => {
    if (!customClaim.trim()) return;
    setRunningTest(true);
    try {
      const res = await analyzeContent({
        org_id: "nova-tech-org-001",
        title: "ClaimDNA Custom Verification",
        content: customClaim
      });
      setActiveSubmission(res);
      loadSubmissions();
      setCustomClaim("");
    } catch (err) {
      console.error(err);
    } finally {
      setRunningTest(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Supported":
        return "bg-[#171717] text-[#FFFFFF] border-[#737373]";
      case "Contradicted":
        return "bg-[#262626] text-[#FFFFFF] border-[#FFFFFF] font-bold";
      case "Unsupported":
        return "bg-[#171717] text-[#A3A3A3] border-[#404040]";
      case "Outdated":
        return "bg-[#0A0A0A] text-[#737373] border-[#262626]";
      default:
        return "bg-[#0A0A0A] text-[#A3A3A3] border-[#404040]";
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#262626] pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#A3A3A3]" />
            <span>ClaimDNA // Evidence-Backed Claim Verification Engine</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Promotional & Factual Claim Auditor</h2>
          <p className="text-xs text-[#A3A3A3] mt-0.5">
            Cross-verifying claims, pricing accuracy, and competitor benchmarks against ground-truth guidelines.
          </p>
        </div>

        <button
          onClick={handleRunSampleNovaTest}
          disabled={runningTest}
          className="px-4 py-2 text-xs font-mono font-medium rounded border border-[#737373] bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#FFFFFF] transition-all flex items-center space-x-2 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{runningTest ? "AUDITING..." : "EXECUTE NOVA TECH BENCHMARK AUDIT"}</span>
        </button>
      </div>

      {/* Claim Tester Input Card */}
      <div className="p-4 rounded-lg border border-[#262626] bg-[#121212] space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#FFFFFF]">Instant Claim Verification</span>
          <span className="text-[10px] font-mono text-[#737373]">Checks against NOVA TECH Knowledge Base (Launch Price: ₹79,999)</span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={customClaim}
            onChange={(e) => setCustomClaim(e.target.value)}
            placeholder="e.g. 'Now only ₹69,999' or 'World's fastest AI laptop with 18 hours battery life'"
            className="flex-1 text-xs bg-[#171717] border border-[#262626] rounded px-3 py-2 text-[#FFFFFF] focus:outline-none focus:border-[#737373]"
            onKeyDown={(e) => e.key === "Enter" && handleTestCustomClaim()}
          />
          <button
            onClick={handleTestCustomClaim}
            disabled={runningTest}
            className="px-4 py-2 text-xs font-mono rounded bg-[#262626] text-[#FFFFFF] hover:bg-[#404040] transition-colors"
          >
            VERIFY CLAIM
          </button>
        </div>
      </div>

      {/* Active Audit Verifications */}
      {activeSubmission && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#FFFFFF]">
                Audit Results: {activeSubmission.title}
              </h3>
              <p className="text-xs text-[#737373] font-mono mt-0.5">
                Content: "{activeSubmission.content}"
              </p>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#171717] border border-[#404040] text-[#FFFFFF]">
              Compliance Score: {activeSubmission.overall_score}/100
            </span>
          </div>

          <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
            <div className="p-3.5 border-b border-[#262626] flex items-center justify-between bg-[#0A0A0A]">
              <span className="text-xs font-semibold text-[#FFFFFF]">
                ClaimDNA Verification Matrix ({activeSubmission.claim_verifications.length} Claims Audited)
              </span>
              <span className="text-[10px] font-mono text-[#737373]">
                Strict 5-Status Truth Model
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0A0A0A] border-b border-[#262626] text-[#737373] font-mono uppercase text-[10px]">
                  <tr>
                    <th className="py-2.5 px-4">Claim Statement</th>
                    <th className="py-2.5 px-4">Verification Status</th>
                    <th className="py-2.5 px-4">Category</th>
                    <th className="py-2.5 px-4">Explanation & Rationale</th>
                    <th className="py-2.5 px-4">Ground-Truth Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#262626]">
                  {activeSubmission.claim_verifications.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-xs text-[#737373]">
                        No specific promotional or pricing claims detected in this copy.
                      </td>
                    </tr>
                  ) : (
                    activeSubmission.claim_verifications.map((claim) => (
                      <tr key={claim.id} className="hover:bg-[#171717] transition-colors">
                        <td className="py-3 px-4 font-mono font-medium text-[#FFFFFF]">{claim.claim_text}</td>
                        <td className="py-3 px-4">
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(claim.status)}`}>
                            {claim.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[#A3A3A3] font-mono text-[11px]">{claim.category}</td>
                        <td className="py-3 px-4 text-[#A3A3A3] leading-relaxed max-w-xs">{claim.explanation}</td>
                        <td className="py-3 px-4 text-[#737373] font-mono text-[10px] leading-relaxed max-w-xs">
                          {claim.evidence_text ? (
                            <div>
                              <div className="text-[#A3A3A3]">{claim.evidence_text}</div>
                              <div className="text-[#737373] mt-0.5">Ref: {claim.source_reference}</div>
                            </div>
                          ) : (
                            <span className="italic">Insufficient guideline evidence</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
