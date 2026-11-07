"use client";

import { useEffect, useState } from "react";
import { Wand2, Sparkles, ArrowRight, Loader2, Info, Check, Cpu } from "lucide-react";
import { rewriteCopy, fetchCopyStudioStatus, CopyRewrite, CopyStudioStatus } from "@/lib/api";

const GLASS = "bg-white border border-slate-200/80 shadow-soft rounded-2xl";
const SAMPLE = "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only Rs 69,999!!!";

export default function CopyStudioPage() {
  const [content, setContent] = useState(SAMPLE);
  const [result, setResult] = useState<CopyRewrite | null>(null);
  const [status, setStatus] = useState<CopyStudioStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchCopyStudioStatus().then(setStatus).catch(() => setStatus(null)); }, []);

  const run = async () => {
    if (!content.trim() || busy) return;
    setBusy(true); setError(null);
    try { setResult(await rewriteCopy(content)); }
    catch { setError("Couldn't reach the backend. Make sure the server is running."); }
    finally { setBusy(false); }
  };

  const isAI = result?.engine?.startsWith("llm:");

  return (
    <div className="max-w-5xl mx-auto space-y-6 select-none">
      {/* Header */}
      <div className="border-b border-slate-200/80 pb-5">
        <div className="flex items-center space-x-2 text-xs font-bold text-indigo-600 uppercase mb-1">
          <Wand2 className="w-3.5 h-3.5 text-indigo-600" />
          <span>AI Copy Studio · Generative Compliant Rewrite</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-1">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">Rewrite copy to be on-brand</h2>
            <p className="text-xs text-slate-600 mt-0.5">
              Generates a compliant version grounded in your approved rules, facts and terminology — preserving creative intent.
            </p>
          </div>
          {status && (
            <div className={`shrink-0 inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold ${status.llm_available ? "bg-purple-50 text-purple-700 border border-purple-200 shadow-sm" : "bg-slate-100 text-slate-600 border border-slate-200"}`}>
              <Cpu className="w-3.5 h-3.5 text-purple-600" />
              <span>{status.llm_available ? `AI Live · ${status.model}` : "Heuristic mode"}</span>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className={`${GLASS} p-5 space-y-3`}>
        <label className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">Marketing copy to rewrite</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white resize-y leading-relaxed transition-all"
          placeholder="Paste marketing copy to rewrite…"
        />
        <div className="flex items-center justify-between pt-1">
          <button onClick={() => { setContent(SAMPLE); setResult(null); }} className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:underline">
            Load sample copy
          </button>
          <button onClick={run} disabled={busy || !content.trim()}
                  className="px-5 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white disabled:opacity-40 transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]">
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin text-white" /> : <Sparkles className="w-3.5 h-3.5 text-indigo-200" />}
            <span>{busy ? "Rewriting…" : "Generate Compliant Copy"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center space-x-2 font-medium">
          <Info className="w-4 h-4 text-rose-600 shrink-0" /><span>{error}</span>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-rose-50/50 border border-rose-200 shadow-soft">
              <div className="text-[10px] uppercase font-bold text-rose-600 tracking-wider mb-2">Original Copy</div>
              <p className="text-sm text-slate-500 leading-relaxed whitespace-pre-line line-through decoration-rose-400">{result.original}</p>
            </div>
            <div className="p-5 rounded-2xl bg-emerald-50/50 border border-emerald-300 shadow-soft ring-2 ring-emerald-100">
              <div className="flex items-center justify-between mb-2">
                <div className="text-[10px] uppercase font-bold text-emerald-800 tracking-wider">Compliant Rewrite</div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${isAI ? "bg-purple-100 text-purple-700 border border-purple-200" : "bg-emerald-100 text-emerald-800 border border-emerald-200"}`}>
                  {isAI ? `AI · ${result.model}` : "Rules-Based"}
                </span>
              </div>
              <p className="text-sm text-emerald-950 leading-relaxed whitespace-pre-line font-bold">{result.rewritten}</p>
            </div>
          </div>

          <div className={`${GLASS} p-5 space-y-3`}>
            <div className="text-xs font-bold text-slate-900">
              Applied Brand Governance Adjustments ({result.changes.length})
            </div>
            {result.changes.length === 0 ? (
              <div className="text-xs text-emerald-700 font-medium">No changes were needed — this copy is already on-brand.</div>
            ) : (
              <div className="space-y-2">
                {result.changes.map((c, i) => (
                  <div key={i} className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                    <Check className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                    <div className="min-w-0 text-xs">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="line-through text-rose-600 font-medium">{c.from}</span>
                        <ArrowRight className="w-3 h-3 text-slate-400" />
                        <span className="font-bold text-emerald-700">{c.to}</span>
                      </div>
                      {c.reason && <div className="text-[11px] text-slate-500 mt-1">{c.reason}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-indigo-500" /> {result.note}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
