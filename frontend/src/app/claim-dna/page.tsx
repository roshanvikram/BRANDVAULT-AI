
"use client";

import { BadgeCheck as BadgeCheckHdr } from "lucide-react";
import { PageHeader } from "@/components/engines/ui";
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

const GLASS = "bg-white border border-slate-200/80 shadow-soft rounded-2xl";

const STATE_META: Record<EvidenceState, { label: string; shade: string; bg: string; border: string; text: string }> = {
  supported:   { label: "Supported",   shade: "#10B981", bg: "#ECFDF5", border: "#A7F3D0", text: "#047857" },
  contradicted:{ label: "Contradicted",shade: "#F43F5E", bg: "#FFF1F2", border: "#FECDD3", text: "#BE123C" },
  outdated:    { label: "Outdated",    shade: "#8B5CF6", bg: "#F5F3FF", border: "#DDD6FE", text: "#6D28D9" },
  missing:     { label: "Missing",     shade: "#0284C7", bg: "#F0F9FF", border: "#BAE6FD", text: "#0369A1" },
  review:      { label: "Needs review",shade: "#F59E0B", bg: "#FFFBEB", border: "#FDE68A", text: "#B45309" },
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
    switch (status.toLowerCase()) {
      case "supported":
        return "bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold";
      case "contradicted":
        return "bg-rose-50 text-rose-700 border-rose-200 font-semibold";
      case "unsupported":
      case "missing":
        return "bg-sky-50 text-sky-700 border-sky-200 font-semibold";
      case "outdated":
        return "bg-purple-50 text-purple-700 border-purple-200 font-semibold";
      case "needs review":
      case "review":
        return "bg-amber-50 text-amber-700 border-amber-200 font-semibold";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <PageHeader
        eyebrow="ClaimDNA"
        icon={<BadgeCheckHdr />}
        title="Claim verification"
        description="Every claim is checked against approved facts and classed as supported, unsupported, contradicted, outdated or needing review."
        actions={<>
        <button
          onClick={handleRunSampleNovaTest}
          disabled={runningTest}
          className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-200" />
          <span>{runningTest ? "Auditing…" : "Run sample claim audit"}</span>
        </button>
        </>}
      />

      {/* Claim Tester Input Card */}
      <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-soft space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-900">Instant Claim Verification</span>
          <span className="text-[11px] text-slate-500">Audits a sample launch claim against your organisation’s approved facts</span>
        </div>
        <div className="flex gap-2.5">
          <input
            type="text"
            value={customClaim}
            onChange={(e) => setCustomClaim(e.target.value)}
            placeholder="e.g. 'Now only ₹69,999' or 'World's fastest AI laptop with 18 hours battery life'"
            className="flex-1 text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-slate-800 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
            onKeyDown={(e) => e.key === "Enter" && handleTestCustomClaim()}
          />
          <button
            onClick={handleTestCustomClaim}
            disabled={runningTest}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-sm"
          >
            Verify Claim
          </button>
        </div>
      </div>

      {/* Evidence Integrity Map (R2-7) */}
      {evidence && evidence.total > 0 && (
        <div className={`${GLASS} p-5 space-y-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Link2 className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-bold text-slate-900">Evidence Integrity Map</span>
            </div>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{evidence.total} claims · claim → approved evidence</span>
          </div>

          {/* Summary distribution bar */}
          <div>
            <div className="h-3 w-full rounded-full overflow-hidden flex bg-slate-100">
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
                  <span className="text-slate-600 font-medium">{STATE_META[st].label}</span>
                  <span className="font-bold text-slate-900">{evidence.summary[st] || 0}</span>
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
                  <div key={c.id} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-stretch p-3 rounded-xl bg-slate-50/70 border border-slate-200/80 hover:bg-white hover:border-indigo-200 transition-colors">
                    {/* Claim */}
                    <div className="md:col-span-5 min-w-0">
                      <div className="text-xs font-bold text-slate-900 truncate">&ldquo;{c.claim_text}&rdquo;</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{c.category} · {(c.confidence * 100).toFixed(0)}% conf.</div>
                    </div>
                    {/* Connector + state */}
                    <div className="md:col-span-2 flex items-center justify-center">
                      <span className="hidden md:block h-px flex-1 bg-slate-200" />
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 mx-1 border" style={{ background: meta.bg, color: meta.text, borderColor: meta.border }}>{meta.label}</span>
                      <span className="hidden md:block h-px flex-1 bg-slate-200" />
                    </div>
                    {/* Evidence */}
                    <div className="md:col-span-5 min-w-0">
                      {hasEv ? (
                        <>
                          <div className="text-[11px] text-slate-800 leading-snug line-clamp-2">
                            {c.evidence_state === "contradicted" ? <span className="font-bold text-rose-600">Contradicts: </span> : ""}{c.evidence_text}
                          </div>
                          <div className="flex items-center flex-wrap gap-1.5 mt-1">
                            <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 font-medium"><Database className="w-2.5 h-2.5 text-indigo-500" />{c.source.reliability}</span>
                            <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 font-medium"><Clock className="w-2.5 h-2.5 text-slate-400" />{c.source.freshness}</span>
                            {c.source_reference && <span className="text-[10px] text-slate-400 truncate">Ref: {c.source_reference}</span>}
                          </div>
                        </>
                      ) : (
                        <div className="inline-flex items-center gap-1.5 text-[11px] text-slate-500">
                          <ShieldOff className="w-3.5 h-3.5 text-slate-400" />{c.source.reliability}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3 text-amber-500" /> Missing = no approved evidence found; Contradicted = evidence conflicts with the claim. Both are distinguished, never conflated.
          </p>
        </div>
      )}

      {/* Active Audit Verifications */}
      {activeSubmission && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Audit Results: {activeSubmission.title}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Content: "{activeSubmission.content}"
              </p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 shadow-sm">
              Compliance Score: {activeSubmission.overall_score}/100
            </span>
          </div>

          <div className="border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden">
            <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
              <span className="text-xs font-bold text-slate-900">
                ClaimDNA Verification Matrix ({activeSubmission.claim_verifications.length} Claims Audited)
              </span>
              <span className="text-[11px] text-slate-500 font-medium">
                Strict 5-Status Truth Model
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200/80 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Claim Statement</th>
                    <th className="py-3 px-4">Verification Status</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Explanation & Rationale</th>
                    <th className="py-3 px-4">Ground-Truth Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeSubmission.claim_verifications.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-xs text-slate-400">
                        No specific promotional or pricing claims detected in this copy.
                      </td>
                    </tr>
                  ) : (
                    activeSubmission.claim_verifications.map((claim) => (
                      <tr key={claim.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-900">{claim.claim_text}</td>
                        <td className="py-3 px-4">
                          <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${getStatusBadge(claim.status)}`}>
                            {claim.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-500 text-[11px]">{claim.category}</td>
                        <td className="py-3 px-4 text-slate-700 leading-relaxed max-w-xs">{claim.explanation}</td>
                        <td className="py-3 px-4 text-slate-500 text-[11px] leading-relaxed max-w-xs">
                          {claim.evidence_text ? (
                            <div>
                              <div className="text-slate-900 font-medium">{claim.evidence_text}</div>
                              <div className="text-indigo-600 mt-0.5">Ref: {claim.source_reference}</div>
                            </div>
                          ) : (
                            <span className="italic text-slate-400">Insufficient guideline evidence</span>
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
