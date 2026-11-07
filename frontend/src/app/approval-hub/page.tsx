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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
              Approval Hub
            </span>
            <span className="text-[11px] text-slate-500">Human-in-the-Loop Governance</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">Human-in-the-Loop Review Queue</h2>
          <p className="text-[13px] text-slate-600 mt-0.5 max-w-2xl">
            Only authorized human reviewers can sign off on promotional marketing campaigns and issue cryptographic Brand Passports.
          </p>
        </div>

        {/* Decisions are always recorded as the signed-in user (server-enforced). */}
        <div className="flex items-center gap-2 h-9 px-3.5 rounded-xl border border-slate-200/80 bg-white shadow-soft text-[13px]">
          <span className="text-slate-500">Signed in as</span>
          <span className="font-bold text-slate-900">{user?.full_name || "—"}</span>
          <span className="text-slate-300">·</span>
          <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold">{user?.role || "—"}</span>
        </div>
      </div>

      {feedbackMessage && (
        <div className="p-3.5 rounded-xl border border-indigo-200 bg-indigo-50/80 shadow-sm text-xs font-medium text-indigo-900 flex items-center justify-between">
          <span>{feedbackMessage}</span>
          <button onClick={() => setFeedbackMessage(null)} className="text-indigo-400 hover:text-indigo-700 font-bold ml-2">×</button>
        </div>
      )}

      {/* Two Column Layout: Submission List vs Review Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Submissions Queue (4 cols) */}
        <div className="lg:col-span-4 border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden flex flex-col h-[640px]">
          <div className="p-3.5 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Approval Queue</span>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">{submissions.length} Total</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2">
            {submissions.map((sub) => {
              const isSelected = selectedSub?.id === sub.id;
              const isApproved = sub.status === "Approved";
              const isRejected = sub.status === "Rejected";
              return (
                <div
                  key={sub.id}
                  onClick={() => setSelectedSub(sub)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all shadow-sm ${
                    isSelected
                      ? "bg-indigo-50/40 border-indigo-500 ring-2 ring-indigo-200"
                      : "bg-white border-slate-200/80 hover:border-indigo-300"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                      isApproved ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                      isRejected ? 'bg-rose-50 text-rose-700 border-rose-200' :
                      'bg-amber-50 text-amber-800 border-amber-200'
                    }`}>
                      {sub.status}
                    </span>
                    <span className="text-xs font-bold text-slate-800">{sub.overall_score}/100</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 truncate">{sub.title}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Author: {sub.author_name}</div>
                  <div className="text-[11px] text-slate-600 mt-1 truncate">"{sub.content}"</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Review & Decision Inspector (8 cols) */}
        <div className="lg:col-span-8 border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden flex flex-col h-[640px]">
          {selectedSub ? (
            <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
              {/* Header Details */}
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Campaign Audit Details</span>
                  <h3 className="text-lg font-bold text-slate-900 mt-0.5">{selectedSub.title}</h3>
                  <div className="text-xs text-slate-500 mt-1">
                    Version: v{selectedSub.version} | Author: {selectedSub.author_name} | Status: <span className="text-indigo-600 font-bold">{selectedSub.status}</span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-3xl font-bold tracking-tight text-slate-900">{selectedSub.overall_score}<span className="text-base text-slate-400 font-normal">/100</span></div>
                  <div className="text-[11px] text-slate-500 font-medium">Brand Health Score</div>
                </div>
              </div>

              {/* Submitted Content Preview */}
              <div>
                <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1.5">Copy Under Review</label>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs font-sans leading-relaxed text-slate-800">
                  "{selectedSub.content}"
                </div>
              </div>

              {/* Findings & Claim Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80">
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
                    Detected Violations ({selectedSub.findings.length})
                  </div>
                  {selectedSub.findings.length === 0 ? (
                    <div className="text-xs text-emerald-700 font-medium flex items-center space-x-1.5">
                      <CheckCircle className="w-4 h-4 text-emerald-600" />
                      <span>Clean copy — no violations detected.</span>
                    </div>
                  ) : (
                    <ul className="text-xs space-y-1.5 text-slate-700">
                      {selectedSub.findings.map((f) => (
                        <li key={f.id} className="flex items-start space-x-1.5">
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-rose-100 text-rose-700 shrink-0">[{f.issue_category}]</span>
                          <span className="line-through text-slate-500">{f.original_text}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80">
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
                    ClaimDNA Verifications ({selectedSub.claim_verifications.length})
                  </div>
                  {selectedSub.claim_verifications.length === 0 ? (
                    <div className="text-xs text-slate-500">No claim conflicts logged.</div>
                  ) : (
                    <ul className="text-xs space-y-1.5 text-slate-700">
                      {selectedSub.claim_verifications.map((c) => (
                        <li key={c.id} className="flex items-start space-x-1.5">
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-200 text-slate-800 shrink-0">[{c.status}]</span>
                          <span className="truncate">{c.claim_text}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* Reviewer Decision Form */}
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">
                  Reviewer Audit Comments & Decision Rationale
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Enter governance review notes, justification, or required modifications..."
                  className="w-full text-xs font-sans bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white h-24 resize-none transition-all"
                />

                <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleDecision("Revision Requested")}
                    disabled={isSubmitting}
                    className="px-4 py-2 text-xs font-semibold rounded-xl border border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100 transition-colors shadow-sm"
                  >
                    Request Revision
                  </button>
                  <button
                    onClick={() => handleDecision("Rejected")}
                    disabled={isSubmitting}
                    className="px-4 py-2 text-xs font-semibold rounded-xl border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors shadow-sm"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecision("Approved")}
                    disabled={isSubmitting}
                    className="px-5 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white transition-all shadow-md shadow-emerald-600/20 active:scale-[0.99]"
                  >
                    {isSubmitting ? "Processing…" : "Approve & Issue Passport"}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400">
              <UserCheck className="w-10 h-10 mb-2 text-slate-300" />
              <p className="text-xs text-slate-500">Select a campaign submission from the queue to conduct human review.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
