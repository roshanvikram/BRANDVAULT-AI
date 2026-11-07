"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  FileSearch,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Send,
  BookOpen,
  ShieldAlert,
  SlidersHorizontal,
  ChevronRight
} from "lucide-react";
import {
  analyzeContent,
  applyCorrection,
  fetchSubmissionDetail,
  submitApprovalDecision,
  Submission,
  Finding
} from "@/lib/api";

function ContentIntelligenceContent() {
  const searchParams = useSearchParams();
  const initialSubmissionId = searchParams.get("submissionId");

  const [title, setTitle] = useState("NovaBook AI Pro 16 Launch Copy");
  const [content, setContent] = useState(
    "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!"
  );
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewMessage, setReviewMessage] = useState<string | null>(null);

  useEffect(() => {
    if (initialSubmissionId) {
      fetchSubmissionDetail(initialSubmissionId)
        .then((res) => {
          setSubmission(res);
          setTitle(res.title);
          setContent(res.content);
          if (res.findings.length > 0) {
            setSelectedFinding(res.findings[0]);
          }
        })
        .catch(console.error);
    }
  }, [initialSubmissionId]);

  const handleAnalyze = async () => {
    if (!content.trim()) return;
    setAnalyzing(true);
    setReviewMessage(null);
    try {
      const res = await analyzeContent({
        title: title || "Untitled Campaign",
        content: content,
        submission_id: submission?.id
      });
      setSubmission(res);
      if (res.findings.length > 0) {
        setSelectedFinding(res.findings[0]);
      } else {
        setSelectedFinding(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApplyCorrection = async (finding: Finding) => {
    if (!submission) return;
    setAnalyzing(true);
    try {
      const res = await applyCorrection({
        submission_id: submission.id,
        finding_id: finding.id,
        target_text: finding.original_text,
        replacement_text: finding.suggested_correction
      });
      setSubmission(res);
      setContent(res.content);
      setSelectedFinding(res.findings.length > 0 ? res.findings[0] : null);
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmitForReview = async () => {
    if (!submission) return;
    setSubmittingReview(true);
    try {
      const res = await submitApprovalDecision({
        submission_id: submission.id,
        decision: "Pending Review" as any,
        comments: "Submitted by Creator for formal brand governance approval.",
        reviewer_name: "Marketing Creator",
        reviewer_role: "Creator"
      });
      setSubmission(res);
      setReviewMessage("Campaign successfully routed to Approval Hub for Reviewer audit.");
    } catch (err: any) {
      setReviewMessage(err?.message || "Submission failed.");
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="space-y-4 select-none">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
              Content Intelligence
            </span>
            <span className="text-[11px] text-slate-500">Autonomous Evidence Verification</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">Marketing Copy Review Studio</h2>
          <p className="text-[13px] text-slate-600 mt-0.5">Check copy against your Brand DNA, review evidence for each finding and apply one-click corrections.</p>
        </div>

        <div className="flex items-center space-x-3">
          {submission && (
            <div className="px-3.5 py-1.5 rounded-xl bg-white border border-slate-200/80 shadow-sm flex items-center space-x-2">
              <span className="text-[13px] text-slate-500 font-medium">Health score</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                submission.overall_score >= 80 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                submission.overall_score >= 50 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                'bg-rose-50 text-rose-700 border border-rose-200'
              }`}>
                {submission.overall_score}/100
              </span>
            </div>
          )}
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-200" />
            <span>{analyzing ? "Analysing…" : "Run AI Analysis"}</span>
          </button>
        </div>
      </div>

      {reviewMessage && (
        <div className="p-3.5 rounded-xl border border-indigo-200 bg-indigo-50/80 shadow-sm text-xs text-indigo-900 flex items-center justify-between font-medium">
          <span>{reviewMessage}</span>
          <button onClick={() => setReviewMessage(null)} className="text-indigo-400 hover:text-indigo-700 font-bold ml-2">×</button>
        </div>
      )}

      {/* THREE-PANEL INTERFACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-190px)] min-h-[580px]">
        {/* PANEL 1: Content Editor (5 cols) */}
        <div className="lg:col-span-5 flex flex-col border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden">
          <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Content Editor</span>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">{content.length} chars</span>
          </div>

          <div className="p-4 flex-1 flex flex-col space-y-3 overflow-y-auto">
            <div>
              <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Campaign Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
              />
            </div>

            <div className="flex-1 flex flex-col">
              <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Marketing Copy</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter or paste promotional copy to inspect..."
                className="w-full flex-1 min-h-[220px] text-xs leading-relaxed font-sans bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white resize-none transition-all"
              />
            </div>

            {submission && (
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-medium">
                  Status: <span className="text-slate-900 font-bold">{submission.status}</span>
                </span>
                <button
                  onClick={handleSubmitForReview}
                  disabled={submittingReview}
                  className="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors flex items-center space-x-1.5 shadow-sm"
                >
                  <Send className="w-3 h-3" />
                  <span>{submittingReview ? "Submitting…" : "Submit for review"}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* PANEL 2: Findings List (4 cols) */}
        <div className="lg:col-span-4 flex flex-col border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden">
          <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Findings ({submission?.findings.length || 0})
            </span>
            <span className="text-[11px] font-semibold text-indigo-600">Multi-Agent Audit</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5">
            {!submission || submission.findings.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
                <CheckCircle className="w-8 h-8 mb-2 text-emerald-500" />
                <p className="text-xs font-medium text-slate-600">
                  {submission ? "No brand violations detected. This copy is compliant." : "Run AI analysis to check this copy against your brand rules."}
                </p>
              </div>
            ) : (
              submission.findings.map((f) => {
                const isSelected = selectedFinding?.id === f.id;
                const isCritical = f.severity?.toUpperCase() === "CRITICAL";
                const isWarning = f.severity?.toUpperCase() === "WARNING";
                return (
                  <div
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all shadow-sm ${
                      isSelected
                        ? "bg-indigo-50/30 border-indigo-500 ring-2 ring-indigo-200"
                        : "bg-white border-slate-200/80 hover:border-indigo-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {f.issue_category}
                        </span>
                        {f.analysis_engine?.startsWith("llm") ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700 font-bold" title={f.analysis_engine}>
                            AI
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600" title="Deterministic rule engine">
                            RULES
                          </span>
                        )}
                      </div>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                        isCritical ? 'bg-rose-50 text-rose-700 border-rose-200' :
                        isWarning ? 'bg-amber-50 text-amber-700 border-amber-200' :
                        'bg-sky-50 text-sky-700 border-sky-200'
                      }`}>
                        {f.severity}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-rose-600 line-through decoration-rose-400">
                      "{f.original_text}"
                    </div>

                    <div className="text-[11px] text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                      {f.explanation}
                    </div>

                    <div className="mt-2.5 pt-2.5 border-t border-slate-100 flex items-center justify-between">
                      <span className="text-[10px] text-slate-400 font-medium">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApplyCorrection(f);
                        }}
                        className="px-2.5 py-1 text-[11px] rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
                      >
                        Apply fix
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* PANEL 3: Evidence & Brand Rules (3 cols) */}
        <div className="lg:col-span-3 flex flex-col border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden">
          <div className="p-3.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Evidence & Source</span>
            <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
          </div>

          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            {selectedFinding ? (
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Issue Category</div>
                  <div className="text-xs font-bold text-slate-900">{selectedFinding.issue_category} Violation</div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Original Fragment</div>
                  <div className="text-xs p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 font-medium">
                    {selectedFinding.original_text}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Suggested Replacement</div>
                  <div className="text-xs p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold shadow-sm">
                    {selectedFinding.suggested_correction}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Brand Rule Reference</div>
                  <div className="text-xs text-slate-700 leading-relaxed bg-slate-50 border border-slate-200 p-2.5 rounded-xl">
                    {selectedFinding.rule_reference}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Ground Truth Citation</div>
                  <div className="text-[11px] p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 leading-relaxed">
                    {selectedFinding.evidence_source}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => handleApplyCorrection(selectedFinding)}
                    className="w-full py-2.5 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition-all shadow-md shadow-emerald-600/20 active:scale-[0.99]"
                  >
                    Apply this correction
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-4 text-slate-400">
                <ShieldAlert className="w-8 h-8 mb-2 text-slate-300" />
                <p className="text-xs text-slate-500">Select a finding to see its evidence and the brand rule it relates to.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ContentIntelligence() {
  return (
    <Suspense fallback={<div className="p-8 text-xs font-mono text-[#737373]">Loading Content Intelligence…</div>}>
      <ContentIntelligenceContent />
    </Suspense>
  );
}
