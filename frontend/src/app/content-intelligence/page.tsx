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
        org_id: "nova-tech-org-001",
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
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="space-y-4 select-none">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#262626] pb-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-0.5">
            <FileSearch className="w-3.5 h-3.5 text-[#A3A3A3]" />
            <span>Content Intelligence // Three-Panel Analysis Studio</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Marketing Copy Compliance Auditor</h2>
        </div>

        <div className="flex items-center space-x-3">
          {submission && (
            <div className="px-3 py-1 rounded bg-[#171717] border border-[#262626] flex items-center space-x-2">
              <span className="text-[10px] font-mono text-[#737373]">HEALTH SCORE:</span>
              <span className="text-xs font-mono font-bold text-[#FFFFFF]">
                {submission.overall_score}/100
              </span>
            </div>
          )}
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-2 text-xs font-mono font-semibold rounded border border-[#737373] bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#FFFFFF] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{analyzing ? "ANALYSING..." : "RUN AI ANALYSIS"}</span>
          </button>
        </div>
      </div>

      {reviewMessage && (
        <div className="p-3 rounded border border-[#404040] bg-[#171717] text-xs font-mono text-[#FFFFFF] flex items-center justify-between">
          <span>{reviewMessage}</span>
          <button onClick={() => setReviewMessage(null)} className="text-[#A3A3A3] hover:text-[#FFFFFF]">×</button>
        </div>
      )}

      {/* THREE-PANEL INTERFACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-190px)] min-h-[580px]">
        {/* PANEL 1: Content Editor (5 cols) */}
        <div className="lg:col-span-5 flex flex-col border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
          <div className="p-3 border-b border-[#262626] flex items-center justify-between bg-[#0A0A0A]">
            <span className="text-xs font-mono uppercase text-[#A3A3A3] font-medium">Panel 1 // Content Editor</span>
            <span className="text-[10px] font-mono text-[#737373]">{content.length} chars</span>
          </div>

          <div className="p-4 flex-1 flex flex-col space-y-3 overflow-y-auto">
            <div>
              <label className="text-[10px] font-mono uppercase text-[#737373] block mb-1">Campaign Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full text-xs font-medium bg-[#171717] border border-[#262626] rounded px-3 py-2 text-[#FFFFFF] focus:outline-none focus:border-[#737373]"
              />
            </div>

            <div className="flex-1 flex flex-col">
              <label className="text-[10px] font-mono uppercase text-[#737373] block mb-1">Marketing Copy</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter or paste promotional copy to inspect..."
                className="w-full flex-1 min-h-[220px] text-xs leading-relaxed font-sans bg-[#171717] border border-[#262626] rounded p-3 text-[#FFFFFF] focus:outline-none focus:border-[#737373] resize-none"
              />
            </div>

            {submission && (
              <div className="pt-2 border-t border-[#262626] flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#737373]">
                  Status: <span className="text-[#FFFFFF]">{submission.status}</span>
                </span>
                <button
                  onClick={handleSubmitForReview}
                  disabled={submittingReview}
                  className="px-3 py-1.5 text-xs font-mono rounded bg-[#262626] text-[#FFFFFF] hover:bg-[#404040] transition-colors flex items-center space-x-1.5"
                >
                  <Send className="w-3 h-3" />
                  <span>{submittingReview ? "SUBMITTING..." : "SUBMIT FOR REVIEW"}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* PANEL 2: Findings List (4 cols) */}
        <div className="lg:col-span-4 flex flex-col border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
          <div className="p-3 border-b border-[#262626] flex items-center justify-between bg-[#0A0A0A]">
            <span className="text-xs font-mono uppercase text-[#A3A3A3] font-medium">
              Panel 2 // Findings ({submission?.findings.length || 0})
            </span>
            <span className="text-[10px] font-mono text-[#737373]">Multi-Agent Audit</span>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-2.5">
            {!submission || submission.findings.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#737373]">
                <CheckCircle className="w-8 h-8 mb-2 text-[#404040]" />
                <p className="text-xs font-mono">
                  {submission ? "No brand violations detected! Copy is 100% compliant." : "Click 'RUN AI ANALYSIS' to execute brand audit."}
                </p>
              </div>
            ) : (
              submission.findings.map((f) => {
                const isSelected = selectedFinding?.id === f.id;
                return (
                  <div
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className={`p-3 rounded border cursor-pointer transition-all ${
                      isSelected
                        ? "bg-[#171717] border-[#737373]"
                        : "bg-[#0A0A0A] border-[#262626] hover:border-[#404040]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded border border-[#404040] bg-[#171717] text-[#FFFFFF]">
                        {f.issue_category}
                      </span>
                      <span className="text-[9px] font-mono text-[#A3A3A3] border border-[#262626] px-1 py-0.5 rounded">
                        {f.severity}
                      </span>
                    </div>

                    <div className="text-xs font-medium text-[#FFFFFF] line-through decoration-[#737373]">
                      "{f.original_text}"
                    </div>

                    <div className="text-[11px] text-[#A3A3A3] mt-1 line-clamp-2">
                      {f.explanation}
                    </div>

                    <div className="mt-2 pt-2 border-t border-[#262626] flex items-center justify-between">
                      <span className="text-[10px] font-mono text-[#737373]">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApplyCorrection(f);
                        }}
                        className="px-2 py-0.5 text-[10px] font-mono rounded bg-[#F5F5F5] text-[#0A0A0A] font-semibold hover:bg-[#FFFFFF] transition-colors"
                      >
                        APPLY FIX
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* PANEL 3: Evidence & Brand Rules (3 cols) */}
        <div className="lg:col-span-3 flex flex-col border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
          <div className="p-3 border-b border-[#262626] flex items-center justify-between bg-[#0A0A0A]">
            <span className="text-xs font-mono uppercase text-[#A3A3A3] font-medium">Panel 3 // Evidence</span>
            <BookOpen className="w-3.5 h-3.5 text-[#737373]" />
          </div>

          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            {selectedFinding ? (
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] mb-1">Issue Category</div>
                  <div className="text-xs font-semibold text-[#FFFFFF]">{selectedFinding.issue_category} Violation</div>
                </div>

                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] mb-1">Original Fragment</div>
                  <div className="text-xs font-mono p-2 rounded bg-[#0A0A0A] border border-[#262626] text-[#FFFFFF]">
                    {selectedFinding.original_text}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] mb-1">Suggested Replacement</div>
                  <div className="text-xs font-mono p-2 rounded bg-[#171717] border border-[#404040] text-[#FFFFFF] font-bold">
                    {selectedFinding.suggested_correction}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] mb-1">Brand Rule Reference</div>
                  <div className="text-xs text-[#A3A3A3] leading-relaxed">
                    {selectedFinding.rule_reference}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] mb-1">Source & Ground Truth Citation</div>
                  <div className="text-[11px] font-mono p-2.5 rounded bg-[#0A0A0A] border border-[#262626] text-[#A3A3A3] leading-relaxed">
                    {selectedFinding.evidence_source}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => handleApplyCorrection(selectedFinding)}
                    className="w-full py-2 text-xs font-mono font-medium rounded bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#FFFFFF] transition-colors"
                  >
                    APPLY THIS CORRECTION
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-4 text-[#737373]">
                <ShieldAlert className="w-8 h-8 mb-2 text-[#404040]" />
                <p className="text-xs font-mono">Select any finding from Panel 2 to inspect relevant citations and evidence.</p>
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
    <Suspense fallback={<div className="p-8 text-xs font-mono text-[#737373]">INITIALIZING CONTENT INTELLIGENCE SUITE...</div>}>
      <ContentIntelligenceContent />
    </Suspense>
  );
}
