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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E5E5] pb-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">Marketing copy review</h2>
          <p className="text-[13px] text-[#71717A] mt-1">Check copy against your Brand DNA, review evidence for each finding and apply corrections.</p>
        </div>

        <div className="flex items-center space-x-3">
          {submission && (
            <div className="px-3.5 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#E5E5E5] shadow-sm flex items-center space-x-2">
              <span className="text-[13px] text-[#71717A]">Health score</span>
              <span className="text-xs font-mono font-bold text-[#0A0A0A]">
                {submission.overall_score}/100
              </span>
            </div>
          )}
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-2 text-xs font-medium rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#27272A] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{analyzing ? "Analysing…" : "Run AI analysis"}</span>
          </button>
        </div>
      </div>

      {reviewMessage && (
        <div className="p-3.5 rounded-lg border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm text-xs font-mono text-[#0A0A0A] flex items-center justify-between">
          <span>{reviewMessage}</span>
          <button onClick={() => setReviewMessage(null)} className="text-[#737373] hover:text-[#0A0A0A]">×</button>
        </div>
      )}

      {/* THREE-PANEL INTERFACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-190px)] min-h-[580px]">
        {/* PANEL 1: Content Editor (5 cols) */}
        <div className="lg:col-span-5 flex flex-col border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden">
          <div className="p-3 border-b border-[#E5E5E5] flex items-center justify-between bg-[#F5F5F5]">
            <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">Content editor</span>
            <span className="text-[11px] font-mono text-[#737373]">{content.length} chars</span>
          </div>

          <div className="p-4 flex-1 flex flex-col space-y-3 overflow-y-auto">
            <div>
              <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Campaign Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full text-xs font-semibold bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg px-3 py-2 text-[#0A0A0A] focus:outline-none focus:border-[#0A0A0A]"
              />
            </div>

            <div className="flex-1 flex flex-col">
              <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Marketing Copy</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter or paste promotional copy to inspect..."
                className="w-full flex-1 min-h-[220px] text-xs leading-relaxed font-sans bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg p-3 text-[#0A0A0A] focus:outline-none focus:border-[#0A0A0A] resize-none"
              />
            </div>

            {submission && (
              <div className="pt-3 border-t border-[#E5E5E5] flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#737373]">
                  Status: <span className="text-[#0A0A0A] font-bold">{submission.status}</span>
                </span>
                <button
                  onClick={handleSubmitForReview}
                  disabled={submittingReview}
                  className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#27272A] transition-colors flex items-center space-x-1.5 shadow-sm"
                >
                  <Send className="w-3 h-3" />
                  <span>{submittingReview ? "Submitting…" : "Submit for review"}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* PANEL 2: Findings List (4 cols) */}
        <div className="lg:col-span-4 flex flex-col border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden">
          <div className="p-3 border-b border-[#E5E5E5] flex items-center justify-between bg-[#F5F5F5]">
            <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">
              Findings ({submission?.findings.length || 0})
            </span>
            <span className="text-[11px] font-mono text-[#737373]">Multi-Agent Audit</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5">
            {!submission || submission.findings.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#737373]">
                <CheckCircle className="w-8 h-8 mb-2 text-[#A3A3A3]" />
                <p className="text-xs font-mono">
                  {submission ? "No brand violations detected. This copy is compliant." : "Run AI analysis to check this copy against your brand rules."}
                </p>
              </div>
            ) : (
              submission.findings.map((f) => {
                const isSelected = selectedFinding?.id === f.id;
                return (
                  <div
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all shadow-sm ${
                      isSelected
                        ? "bg-[#F5F5F5] border-[#0A0A0A]"
                        : "bg-[#FFFFFF] border-[#E5E5E5] hover:border-[#A3A3A3]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border border-[#E5E5E5] bg-[#FFFFFF] text-[#0A0A0A] font-semibold">
                          {f.issue_category}
                        </span>
                        {f.analysis_engine?.startsWith("llm") ? (
                          <span className="text-[11px] px-1.5 py-0.5 rounded bg-[#0A0A0A] text-[#FFFFFF] font-medium" title={f.analysis_engine}>
                            AI
                          </span>
                        ) : (
                          <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border border-[#E5E5E5] bg-[#F5F5F5] text-[#737373] font-semibold" title="Deterministic rule engine">
                            RULES
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] font-mono text-[#737373] border border-[#E5E5E5] px-1 py-0.5 rounded font-semibold">
                        {f.severity}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-[#0A0A0A] line-through decoration-[#737373]">
                      "{f.original_text}"
                    </div>

                    <div className="text-[11px] text-[#404040] mt-1 line-clamp-2 leading-relaxed">
                      {f.explanation}
                    </div>

                    <div className="mt-2.5 pt-2.5 border-t border-[#E5E5E5] flex items-center justify-between">
                      <span className="text-[11px] font-mono text-[#737373]">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApplyCorrection(f);
                        }}
                        className="px-2.5 py-1 text-[11px] rounded bg-[#0A0A0A] text-[#FFFFFF] font-medium hover:bg-[#27272A] transition-colors shadow-sm"
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
        <div className="lg:col-span-3 flex flex-col border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden">
          <div className="p-3 border-b border-[#E5E5E5] flex items-center justify-between bg-[#F5F5F5]">
            <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">Evidence</span>
            <BookOpen className="w-3.5 h-3.5 text-[#0A0A0A]" />
          </div>

          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            {selectedFinding ? (
              <div className="space-y-4">
                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-semibold mb-1">Issue Category</div>
                  <div className="text-xs font-bold text-[#0A0A0A]">{selectedFinding.issue_category} Violation</div>
                </div>

                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-semibold mb-1">Original Fragment</div>
                  <div className="text-xs font-mono p-2.5 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5] text-[#0A0A0A]">
                    {selectedFinding.original_text}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-semibold mb-1">Suggested Replacement</div>
                  <div className="text-xs font-mono p-2.5 rounded-lg bg-[#FFFFFF] border border-[#0A0A0A] text-[#0A0A0A] font-bold shadow-sm">
                    {selectedFinding.suggested_correction}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-semibold mb-1">Brand Rule Reference</div>
                  <div className="text-xs text-[#404040] leading-relaxed">
                    {selectedFinding.rule_reference}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-semibold mb-1">Source & Ground Truth Citation</div>
                  <div className="text-[11px] font-mono p-2.5 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5] text-[#404040] leading-relaxed">
                    {selectedFinding.evidence_source}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => handleApplyCorrection(selectedFinding)}
                    className="w-full py-2.5 text-xs font-mono font-bold rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#262626] transition-colors shadow-sm"
                  >
                    Apply this correction
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-4 text-[#737373]">
                <ShieldAlert className="w-8 h-8 mb-2 text-[#A3A3A3]" />
                <p className="text-xs font-mono">Select a finding to see its evidence and the brand rule it relates to.</p>
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
