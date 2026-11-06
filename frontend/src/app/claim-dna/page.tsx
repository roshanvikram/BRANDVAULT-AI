
"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  Link2,
  Database,
  Clock,
  ShieldOff,
} from "lucide-react";
import {
  fetchSubmissions,
  runSampleNovaTest,
  analyzeContent,
  fetchEvidenceMap,
  Submission,
  EvidenceMap,
  EvidenceClaim,
  EvidenceState,
} from "@/lib/api";

const GLASS = "bg-white/70 backdrop-blur-xl border border-white/70 shadow-[0_10px_34px_-14px_rgba(10,10,10,0.22)] rounded-2xl";

const STATE_META: Record<EvidenceState, { label: string; shade: string; text: string }> = {
  supported:   { label: "Supported",   shade: "#0A0A0A", text: "#FFFFFF" },
  contradicted:{ label: "Contradicted",shade: "#404040", text: "#FFFFFF" },
  outdated:    { label: "Outdated",    shade: "#737373", text: "#FFFFFF" },
  missing:     { label: "Missing",     shade: "#A3A3A3", text: "#FFFFFF" },
  review:      { label: "Needs review",shade: "#D4D4D4", text: "#0A0A0A" },
};
const STATE_ORDER: EvidenceState[] = ["supported", "contradicted", "missing", "outdated", "review"];

export default function ClaimDNA() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [activeSubmission, setActiveSubmission] = useState<Submission | null>(null);
  const [customClaim, setCustomClaim] = useState("");
  const [runningTest, setRunningTest] = useState(false);
  const [evidence, setEvidence] = useState<EvidenceMap | null>(null);

  const loadSubmissions = () => {
    fetchSubmissions().then((subs) => {
      setSubmissions(subs);
      if (subs.length > 0 && !activeSubmission) {
        setActiveSubmission(subs[0]);
      }
    }).catch(console.error);
    fetchEvidenceMap().then(setEvidence).catch(console.error);
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
        return "bg-[#F5F5F5] text-[#0A0A0A] border-[#E5E5E5] font-semibold";
      case "Contradicted":
        return "bg-[#0A0A0A] text-[#FFFFFF] border-[#0A0A0A] font-bold";
      case "Unsupported":
        return "bg-[#FFFFFF] text-[#737373] border-[#E5E5E5] font-semibold";
      case "Outdated":
        return "bg-[#FAFAFA] text-[#A3A3A3] border-[#E5E5E5]";
      default:
        return "bg-[#F5F5F5] text-[#404040] border-[#E5E5E5]";
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E5E5E5] pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span className="font-semibold">ClaimDNA // Evidence-Backed Claim Verification Engine</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A]">Promotional & Factual Claim Auditor</h2>
          <p className="text-xs text-[#737373] mt-0.5">
            Cross-verifying claims, pricing accuracy, and competitor benchmarks against ground-truth guidelines.
          </p>
        </div>

        <button
          onClick={handleRunSampleNovaTest}
          disabled={runningTest}
          className="px-4 py-2.5 text-xs font-mono font-semibold rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{runningTest ? "AUDITING..." : "EXECUTE NOVA TECH BENCHMARK AUDIT"}</span>
        </button>
      </div>

      {/* Claim Tester Input Card */}
      <div className="p-5 rounded-xl border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-[#0A0A0A]">Instant Claim Verification</span>
          <span className="text-[10px] font-mono text-[#737373]">Checks against NOVA TECH Knowledge Base (Launch Price: ₹79,999)</span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={customClaim}
            onChange={(e) => setCustomClaim(e.target.value)}
            placeholder="e.g. 'Now only ₹69,999' or 'World's fastest AI laptop with 18 hours battery life'"
            className="flex-1 text-xs bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg px-3 py-2.5 text-[#0A0A0A] focus:outline-none focus:border-[#0A0A0A]"
            onKeyDown={(e) => e.key === "Enter" && handleTestCustomClaim()}
          />
          <button
            onClick={handleTestCustomClaim}
            disabled={runningTest}
            className="px-4 py-2 text-xs font-mono font-semibold rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#262626] transition-colors shadow-sm"
          >
            VERIFY CLAIM
          </button>
        </div>
      </div>

      {/* Evidence Integrity Map (R2-7) */}
      {evidence && evidence.total > 0 && (
        <div className={`${GLASS} p-5 space-y-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Link2 className="w-4 h-4 text-[#0A0A0A]" />
              <span className="text-sm font-bold text-[#0A0A0A]">Evidence Integrity Map</span>
            </div>
            <span className="text-[11px] font-mono text-[#737373]">{evidence.total} claims · claim → approved evidence</span>
          </div>

          {/* Summary distribution bar */}
          <div>
            <div className="h-3 w-full rounded-full overflow-hidden flex bg-black/5">
              {STATE_ORDER.map((st) => {
                const n = evidence.summary[st] || 0;
                const pct = evidence.total ? (n / evidence.total) * 100 : 0;
                return pct > 0 ? <div key={st} style={{ width: `${pct}%`, background: STATE_META[st].shade }} title={`${STATE_META[st].label}: ${n}`} /> : null;
              })}
            </div>
            <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5">
              {STATE_ORDER.map((st) => (
                <div key={st} className="flex items-center space-x-1.5 text-[11px]">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: STATE_META[st].shade }} />
                  <span className="text-[#404040]">{STATE_META[st].label}</span>
                  <span className="font-mono font-bold text-[#0A0A0A]">{evidence.summary[st] || 0}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Claim → evidence relationship rows */}
          <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
            {[...evidence.items]
              .sort((a, b) => STATE_ORDER.indexOf(a.evidence_state) - STATE_ORDER.indexOf(b.evidence_state))
              .map((c: EvidenceClaim) => {
                const meta = STATE_META[c.evidence_state];
                const hasEv = c.source.present;
                return (
                  <div key={c.id} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-stretch p-3 rounded-xl bg-white/50 border border-white/60">
                    {/* Claim */}
                    <div className="md:col-span-5 min-w-0">
                      <div className="text-xs font-bold text-[#0A0A0A] truncate">&ldquo;{c.claim_text}&rdquo;</div>
                      <div className="text-[10px] font-mono text-[#737373] mt-0.5">{c.category} · {(c.confidence * 100).toFixed(0)}% conf.</div>
                    </div>
                    {/* Connector + state */}
                    <div className="md:col-span-2 flex items-center justify-center">
                      <span className="hidden md:block h-px flex-1 bg-[#D4D4D4]" />
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded-full shrink-0 mx-1" style={{ background: meta.shade, color: meta.text }}>{meta.label}</span>
                      <span className="hidden md:block h-px flex-1 bg-[#D4D4D4]" />
                    </div>
                    {/* Evidence */}
                    <div className="md:col-span-5 min-w-0">
                      {hasEv ? (
                        <>
                          <div className="text-[11px] text-[#0A0A0A] leading-snug line-clamp-2">
                            {c.evidence_state === "contradicted" ? "Contradicts: " : ""}{c.evidence_text}
                          </div>
                          <div className="flex items-center flex-wrap gap-1.5 mt-1">
                            <span className="inline-flex items-center gap-1 text-[9px] font-mono text-[#737373]"><Database className="w-2.5 h-2.5" />{c.source.reliability}</span>
                            <span className="inline-flex items-center gap-1 text-[9px] font-mono text-[#737373]"><Clock className="w-2.5 h-2.5" />{c.source.freshness}</span>
                            {c.source_reference && <span className="text-[9px] font-mono text-[#A3A3A3] truncate">Ref: {c.source_reference}</span>}
                          </div>
                        </>
                      ) : (
                        <div className="inline-flex items-center gap-1.5 text-[11px] font-mono text-[#737373]">
                          <ShieldOff className="w-3.5 h-3.5 text-[#A3A3A3]" />{c.source.reliability}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>
          <p className="text-[10px] font-mono text-[#A3A3A3] flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3" /> Missing = no approved evidence found; Contradicted = evidence conflicts with the claim. Both are distinguished, never conflated.
          </p>
        </div>
      )}

      {/* Active Audit Verifications */}
      {activeSubmission && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#0A0A0A]">
                Audit Results: {activeSubmission.title}
              </h3>
              <p className="text-xs text-[#737373] font-mono mt-0.5">
                Content: "{activeSubmission.content}"
              </p>
            </div>
            <span className="text-xs font-mono font-bold px-3 py-1 rounded-lg bg-[#FFFFFF] border border-[#E5E5E5] text-[#0A0A0A] shadow-sm">
              Compliance Score: {activeSubmission.overall_score}/100
            </span>
          </div>

          <div className="border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden">
            <div className="p-3.5 border-b border-[#E5E5E5] flex items-center justify-between bg-[#F5F5F5]">
              <span className="text-xs font-bold text-[#0A0A0A]">
                ClaimDNA Verification Matrix ({activeSubmission.claim_verifications.length} Claims Audited)
              </span>
              <span className="text-[10px] font-mono text-[#737373]">
                Strict 5-Status Truth Model
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#FFFFFF] border-b border-[#E5E5E5] text-[#737373] font-mono uppercase text-[10px]">
                  <tr>
                    <th className="py-3 px-4">Claim Statement</th>
                    <th className="py-3 px-4">Verification Status</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Explanation & Rationale</th>
                    <th className="py-3 px-4">Ground-Truth Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E5E5]">
                  {activeSubmission.claim_verifications.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-xs text-[#737373]">
                        No specific promotional or pricing claims detected in this copy.
                      </td>
                    </tr>
                  ) : (
                    activeSubmission.claim_verifications.map((claim) => (
                      <tr key={claim.id} className="hover:bg-[#F5F5F5] transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-[#0A0A0A]">{claim.claim_text}</td>
                        <td className="py-3 px-4">
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(claim.status)}`}>
                            {claim.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[#737373] font-mono text-[11px]">{claim.category}</td>
                        <td className="py-3 px-4 text-[#404040] leading-relaxed max-w-xs">{claim.explanation}</td>
                        <td className="py-3 px-4 text-[#737373] font-mono text-[10px] leading-relaxed max-w-xs">
                          {claim.evidence_text ? (
                            <div>
                              <div className="text-[#0A0A0A] font-medium">{claim.evidence_text}</div>
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
