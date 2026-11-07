"use client";

import { useEffect, useState } from "react";
import {
  UserCheck,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  MessageSquare,
  ShieldAlert,
  ArrowRight,
  Send,
  History
} from "lucide-react";
import {
  fetchSubmissions,
  submitApprovalDecision,
  Submission
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ApprovalHub() {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [selectedSub, setSelectedSub] = useState<Submission | null>(null);
  const [comments, setComments] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const loadSubmissions = () => {
    fetchSubmissions().then((subs) => {
      setSubmissions(subs);
      if (subs.length > 0 && !selectedSub) {
        setSelectedSub(subs[0]);
      }
    }).catch(console.error);
  };

  useEffect(() => {
    loadSubmissions();
  }, []);

  const handleDecision = async (decision: "Approved" | "Rejected" | "Revision Requested") => {
    if (!selectedSub) return;
    if (!comments.trim()) {
      alert("Please provide reviewer feedback/comments before submitting decision.");
      return;
    }

    setIsSubmitting(true);
    setFeedbackMessage(null);
    try {
      // The decision is made as the signed-in user; the backend enforces that
      // only a Reviewer/Administrator may approve/reject (Creators get 403) and
      // attributes the decision to the authenticated identity.
      const res = await submitApprovalDecision({
        submission_id: selectedSub.id,
        expected_version: selectedSub.version,
        decision: decision,
        comments: comments,
      });
      setSelectedSub(res);
      setComments("");
      setFeedbackMessage(`Campaign marked as '${decision}' by ${user?.full_name} (${user?.role}). Audit log recorded.`);
      loadSubmissions();
    } catch (err: any) {
      setFeedbackMessage(err?.message || "Decision failed. Your role may not permit this action.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E5E5] pb-5">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">Human-in-the-Loop Review Queue</h2>
          <p className="text-[13px] text-[#71717A] mt-1 max-w-2xl">
            Only authorized human reviewers can sign off on promotional marketing campaigns.
          </p>
        </div>

        {/* Decisions are always recorded as the signed-in user (server-enforced). */}
        <div className="flex items-center gap-2 h-9 px-3 rounded-lg border border-[#E4E4E7] bg-white text-[13px]">
          <span className="text-[#71717A]">Signed in as</span>
          <span className="font-medium text-[#0A0A0A]">{user?.full_name || "—"}</span>
          <span className="text-[#A1A1AA]">·</span>
          <span className="text-[#52525B]">{user?.role || "—"}</span>
        </div>
      </div>

      {feedbackMessage && (
        <div className="p-3.5 rounded-lg border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm text-xs font-mono text-[#0A0A0A] flex items-center justify-between">
          <span>{feedbackMessage}</span>
          <button onClick={() => setFeedbackMessage(null)} className="text-[#737373] hover:text-[#0A0A0A]">×</button>
        </div>
      )}

      {/* Two Column Layout: Submission List vs Review Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Submissions Queue (4 cols) */}
        <div className="lg:col-span-4 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden flex flex-col h-[640px]">
          <div className="p-3 border-b border-[#E5E5E5] bg-[#F5F5F5] flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">Approval Queue</span>
            <span className="text-[11px] font-mono text-[#737373]">{submissions.length} Total</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2">
            {submissions.map((sub) => {
              const isSelected = selectedSub?.id === sub.id;
              return (
                <div
                  key={sub.id}
                  onClick={() => setSelectedSub(sub)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all shadow-sm ${
                    isSelected
                      ? "bg-[#F5F5F5] border-[#0A0A0A]"
                      : "bg-[#FFFFFF] border-[#E5E5E5] hover:border-[#A3A3A3]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded border border-[#E5E5E5] bg-[#FFFFFF] text-[#0A0A0A] font-bold">
                      {sub.status}
                    </span>
                    <span className="text-xs font-mono font-bold text-[#0A0A0A]">{sub.overall_score}/100</span>
                  </div>
                  <div className="text-xs font-bold text-[#0A0A0A] truncate">{sub.title}</div>
                  <div className="text-[11px] text-[#737373] font-mono mt-0.5">Author: {sub.author_name}</div>
                  <div className="text-[11px] text-[#404040] mt-1 truncate">"{sub.content}"</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Review & Decision Inspector (8 cols) */}
        <div className="lg:col-span-8 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden flex flex-col h-[640px]">
          {selectedSub ? (
            <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
              {/* Header Details */}
              <div className="flex items-start justify-between border-b border-[#E5E5E5] pb-4">
                <div>
                  <span className="text-[11px] font-mono text-[#737373] uppercase font-semibold">Campaign Audit Details</span>
                  <h3 className="text-lg font-bold text-[#0A0A0A]">{selectedSub.title}</h3>
                  <div className="text-xs font-mono text-[#737373] mt-1">
                    Version: v{selectedSub.version} | Author: {selectedSub.author_name} | Status: <span className="text-[#0A0A0A] font-bold">{selectedSub.status}</span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-2xl font-bold font-mono text-[#0A0A0A]">{selectedSub.overall_score}/100</div>
                  <div className="text-[11px] font-mono text-[#737373]">Brand Health Score</div>
                </div>
              </div>

              {/* Submitted Content Preview */}
              <div>
                <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Copy Under Review</label>
                <div className="p-4 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5] text-xs font-sans leading-relaxed text-[#0A0A0A]">
                  "{selectedSub.content}"
                </div>
              </div>

              {/* Findings & Claim Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5]">
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-bold mb-1.5">
                    Detected Violations ({selectedSub.findings.length})
                  </div>
                  {selectedSub.findings.length === 0 ? (
                    <div className="text-xs text-[#737373]">Clean copy — no violations detected.</div>
                  ) : (
                    <ul className="text-xs space-y-1 text-[#404040]">
                      {selectedSub.findings.map((f) => (
                        <li key={f.id}>
                          • <span className="text-[#0A0A0A] font-semibold">[{f.issue_category}]</span> {f.original_text}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5]">
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-bold mb-1.5">
                    ClaimDNA Verifications ({selectedSub.claim_verifications.length})
                  </div>
                  {selectedSub.claim_verifications.length === 0 ? (
                    <div className="text-xs text-[#737373]">No claim conflicts logged.</div>
                  ) : (
                    <ul className="text-xs space-y-1 text-[#404040]">
                      {selectedSub.claim_verifications.map((c) => (
                        <li key={c.id}>
                          • <span className="font-mono text-[#0A0A0A] font-bold">[{c.status}]</span> {c.claim_text}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* Reviewer Decision Form */}
              <div className="pt-4 border-t border-[#E5E5E5] space-y-3">
                <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block">
                  Reviewer Audit Comments & Decision Rationale
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Enter governance review notes, justification, or required modifications..."
                  className="w-full text-xs font-sans bg-[#FAFAFA] border border-[#E5E5E5] rounded-xl p-3 text-[#0A0A0A] focus:outline-none focus:border-[#0A0A0A] h-20 resize-none"
                />

                <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleDecision("Revision Requested")}
                    disabled={isSubmitting}
                    className="px-3.5 py-2 text-xs font-mono font-semibold rounded-lg border border-[#E5E5E5] bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#E5E5E5] transition-colors shadow-sm"
                  >
                    Request revision
                  </button>
                  <button
                    onClick={() => handleDecision("Rejected")}
                    disabled={isSubmitting}
                    className="px-3.5 py-2 text-xs font-mono font-semibold rounded-lg border border-[#E5E5E5] bg-[#FFFFFF] text-[#737373] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] transition-colors shadow-sm"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecision("Approved")}
                    disabled={isSubmitting}
                    className="px-4 py-2.5 text-xs font-medium rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#27272A] transition-all shadow-sm"
                  >
                    {isSubmitting ? "Processing…" : "Approve & issue passport"}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-[#737373]">
              <UserCheck className="w-10 h-10 mb-2 text-[#A3A3A3]" />
              <p className="text-xs font-mono">Select a campaign submission from the queue to conduct human review.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
