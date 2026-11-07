"use client";

import { useEffect, useState } from "react";
import {
  Brain, Check, RefreshCw, AlertTriangle, Repeat, XCircle, Lightbulb, ArrowRight, Loader2, Info, Lock,
} from "lucide-react";
import { fetchBrandMemory, applyMemoryTerminology, BrandMemory, MemoryInsight, MemoryProposal } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const GLASS = "bg-white border border-[#E4E4E7] shadow-[0_1px_2px_rgba(10,10,10,0.04)] rounded-xl";

const INSIGHT_ICON: Record<string, any> = {
  accepted_correction: Check,
  recurring_violation: Repeat,
  contradiction: XCircle,
};

export default function BrandMemoryPage() {
  const { user } = useAuth();
  const [mem, setMem] = useState<BrandMemory | null>(null);
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState<Record<string, string>>({});
  const isAdmin = user?.role === "Administrator";

  const load = () => {
    setLoading(true);
    fetchBrandMemory().then(setMem).catch(console.error).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const apply = async (p: MemoryProposal) => {
    const key = p.prohibited_term;
    setApplied((a) => ({ ...a, [key]: "applying" }));
    try {
      const res = await applyMemoryTerminology({
        org_id: mem!.org.id,
        prohibited_term: p.prohibited_term,
        preferred_term: p.preferred_term,
        explanation: p.reason,
      });
      setApplied((a) => ({ ...a, [key]: res.created ? "applied" : "exists" }));
      load();
    } catch (e: any) {
      setApplied((a) => ({ ...a, [key]: e?.message || "failed" }));
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E4E4E7] pb-5">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">What your governance history is telling you</h2>
          <p className="text-[13px] text-[#71717A] mt-1 max-w-2xl">
            Patterns learned from real reviews. BrandVault never edits policy automatically — proposals need an administrator.
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className="px-3.5 py-2 text-xs font-medium rounded-lg bg-[#0A0A0A] text-white hover:bg-[#27272A] transition-colors flex items-center space-x-2">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {!mem && <div className="flex items-center justify-center py-16 text-[#737373]"><Loader2 className="w-5 h-5 animate-spin" /></div>}

      {mem && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Accepted corrections", value: mem.summary.applied_corrections ?? 0 },
              { label: "Recurring patterns", value: mem.summary.recurring_patterns ?? 0 },
              { label: "Contradictions", value: mem.summary.contradictions ?? 0 },
              { label: "Policy proposals", value: mem.summary.proposals ?? 0 },
            ].map((s) => (
              <div key={s.label} className={`${GLASS} p-4`}>
                <div className="text-3xl font-bold tracking-tight text-[#0A0A0A]">{s.value}</div>
                <div className="text-[11px] font-mono text-[#737373] mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Proposals */}
          <div className={`${GLASS} p-5 space-y-4`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Lightbulb className="w-4 h-4 text-[#0A0A0A]" />
                <span className="text-sm font-bold text-[#0A0A0A]">Proposed policy improvements</span>
              </div>
              {!isAdmin && (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-[#737373]"><Lock className="w-3 h-3" /> Administrator applies</span>
              )}
            </div>
            {mem.proposals.length === 0 ? (
              <div className="text-xs text-[#737373] py-2">
                No new proposals — your terminology already covers the recurring issues in your history.
              </div>
            ) : (
              <div className="space-y-2.5">
                {mem.proposals.map((p: MemoryProposal) => {
                  const st = applied[p.prohibited_term];
                  return (
                    <div key={p.prohibited_term} className="p-3.5 rounded-xl bg-white border border-[#E4E4E7] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 text-xs flex-wrap">
                          <span className="font-mono font-bold text-[#A3A3A3] line-through">{p.prohibited_term}</span>
                          <ArrowRight className="w-3 h-3 text-[#A3A3A3]" />
                          <span className="font-mono font-bold text-[#0A0A0A]">{p.preferred_term}</span>
                        </div>
                        <div className="text-[11px] text-[#737373] mt-0.5">Add as approved terminology · {p.reason}</div>
                      </div>
                      <div className="shrink-0">
                        {st === "applied" ? (
                          <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-[#0A0A0A]"><Check className="w-3.5 h-3.5" /> Added to Brand DNA</span>
                        ) : st === "exists" ? (
                          <span className="text-[11px] font-mono text-[#737373]">Already exists</span>
                        ) : st && st !== "applying" ? (
                          <span className="text-[11px] font-mono text-[#737373]">{st}</span>
                        ) : (
                          <button
                            onClick={() => apply(p)}
                            disabled={!isAdmin || st === "applying"}
                            title={isAdmin ? "Add this to your terminology" : "Only an Administrator can apply"}
                            className="px-3 py-1.5 text-[11px] font-medium rounded-lg bg-[#0A0A0A] text-white hover:bg-[#27272A] disabled:opacity-40 disabled:cursor-not-allowed transition-all inline-flex items-center gap-1.5"
                          >
                            {st === "applying" ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                            <span>Add to terminology</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Insights */}
          <div className={`${GLASS} p-5 space-y-3`}>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-[#0A0A0A]" />
              <span className="text-sm font-bold text-[#0A0A0A]">Learned insights</span>
            </div>
            {mem.insights.length === 0 ? (
              <div className="text-xs text-[#737373]">Not enough history yet — analyse some content to build memory.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {mem.insights.map((ins: MemoryInsight, i: number) => {
                  const Icon = INSIGHT_ICON[ins.type] || Info;
                  return (
                    <div key={i} className="p-3.5 rounded-xl bg-white border border-[#E4E4E7] flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg bg-white border border-[#E4E4E7] flex items-center justify-center shrink-0 text-[#0A0A0A]"><Icon className="w-3.5 h-3.5" /></div>
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-[#0A0A0A] flex items-center gap-2">
                          {ins.title}
                          <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-[#F5F5F5] border border-[#E5E5E5] text-[#404040]">×{ins.count}</span>
                        </div>
                        <div className="text-[11px] text-[#737373] mt-0.5 leading-relaxed">{ins.detail}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <p className="text-[11px] font-mono text-[#A3A3A3] flex items-center gap-1.5">
            <Info className="w-3 h-3" /> {mem.note}
          </p>
        </>
      )}
    </div>
  );
}
