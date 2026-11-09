"use client";

import { Brain as BrainHdr } from "lucide-react";
import { PageHeader } from "@/components/engines/ui";
import { useEffect, useState } from "react";
import {
  Brain, Check, RefreshCw, AlertTriangle, Repeat, XCircle, Lightbulb, ArrowRight, Loader2, Info, Lock,
} from "lucide-react";
import { fetchBrandMemory, applyMemoryTerminology, BrandMemory, MemoryInsight, MemoryProposal } from "@/lib/api";
import { useAuth } from "@/lib/auth";

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
      <PageHeader
        eyebrow="Brand Memory"
        icon={<BrainHdr />}
        title="What your review history is telling you"
        description="Patterns learned from real reviews. BrandVault never edits policy on its own — every proposal needs an administrator."
        actions={<>
        <button onClick={load} disabled={loading}
          className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors flex items-center space-x-2 shadow-sm self-start sm:self-auto">
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-600 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh analysis</span>
        </button>
        </>}
      />

      {!mem && <div className="flex items-center justify-center py-16 text-indigo-600"><Loader2 className="w-6 h-6 animate-spin" /></div>}

      {mem && (
        <>
          {/* Summary KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Accepted corrections", value: mem.summary.applied_corrections ?? 0, bg: "from-emerald-500/10 to-teal-500/5", border: "border-emerald-200", text: "text-emerald-700" },
              { label: "Recurring patterns", value: mem.summary.recurring_patterns ?? 0, bg: "from-amber-500/10 to-orange-500/5", border: "border-amber-200", text: "text-amber-700" },
              { label: "Contradictions", value: mem.summary.contradictions ?? 0, bg: "from-rose-500/10 to-pink-500/5", border: "border-rose-200", text: "text-rose-700" },
              { label: "Policy proposals", value: mem.summary.proposals ?? 0, bg: "from-indigo-500/10 to-purple-500/5", border: "border-indigo-200", text: "text-indigo-700" },
            ].map((s) => (
              <div key={s.label} className={`bg-gradient-to-br ${s.bg} bg-white rounded-2xl border ${s.border} shadow-soft p-5`}>
                <div className={`text-3xl font-extrabold tracking-tight ${s.text}`}>{s.value}</div>
                <div className="text-xs font-bold text-slate-600 mt-1">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Proposals */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center">
                  <Lightbulb className="w-4 h-4" />
                </div>
                <span className="text-sm font-bold text-slate-900">Proposed policy improvements</span>
              </div>
              {!isAdmin && (
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1 rounded-full"><Lock className="w-3.5 h-3.5" /> Administrator action required</span>
              )}
            </div>
            {mem.proposals.length === 0 ? (
              <div className="text-xs text-slate-500 py-3 bg-slate-50 rounded-xl px-4">
                No new proposals — your approved terminology already covers the recurring issues in your history.
              </div>
            ) : (
              <div className="space-y-3">
                {mem.proposals.map((p: MemoryProposal) => {
                  const st = applied[p.prohibited_term];
                  return (
                    <div key={p.prohibited_term} className="p-4 rounded-xl bg-gradient-to-r from-amber-50/40 via-white to-indigo-50/30 border border-amber-200/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 text-xs flex-wrap">
                          <span className="font-bold text-rose-500 line-through bg-rose-50 px-2 py-0.5 rounded border border-rose-200">{p.prohibited_term}</span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                          <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">{p.preferred_term}</span>
                        </div>
                        <div className="text-xs text-slate-600 mt-1">Add as approved terminology · {p.reason}</div>
                      </div>
                      <div className="shrink-0">
                        {st === "applied" ? (
                          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl"><Check className="w-3.5 h-3.5" /> Added to Brand DNA</span>
                        ) : st === "exists" ? (
                          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-xl">Already exists</span>
                        ) : st && st !== "applying" ? (
                          <span className="text-xs font-semibold text-rose-600">{st}</span>
                        ) : (
                          <button
                            onClick={() => apply(p)}
                            disabled={!isAdmin || st === "applying"}
                            title={isAdmin ? "Add this to your terminology" : "Only an Administrator can apply"}
                            className="px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all inline-flex items-center gap-1.5 shadow-md shadow-indigo-500/20"
                          >
                            {st === "applying" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
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
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-6 space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-200 flex items-center justify-center">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <span className="text-sm font-bold text-slate-900">Learned governance patterns</span>
            </div>
            {mem.insights.length === 0 ? (
              <div className="text-xs text-slate-500 py-3 bg-slate-50 rounded-xl px-4">Not enough review history yet — analyse content to build memory patterns.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {mem.insights.map((ins: MemoryInsight, i: number) => {
                  const Icon = INSIGHT_ICON[ins.type] || Info;
                  return (
                    <div key={i} className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80 hover:bg-white hover:shadow-soft transition-all flex items-start gap-3.5">
                      <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0"><Icon className="w-4 h-4" /></div>
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                          {ins.title}
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700">×{ins.count}</span>
                        </div>
                        <div className="text-xs text-slate-600 mt-1 leading-relaxed">{ins.detail}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <p className="text-xs text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-indigo-500" /> {mem.note}
          </p>
        </>
      )}
    </div>
  );
}
