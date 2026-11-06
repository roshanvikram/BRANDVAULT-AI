"use client";

import { useEffect, useState } from "react";
import { Wand2, Sparkles, ArrowRight, Loader2, Info, Check, Cpu } from "lucide-react";
import { rewriteCopy, fetchCopyStudioStatus, CopyRewrite, CopyStudioStatus } from "@/lib/api";

const GLASS = "bg-white/70 backdrop-blur-xl border border-white/70 shadow-[0_10px_34px_-14px_rgba(10,10,10,0.22)] rounded-2xl";
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
    <div className="max-w-5xl mx-auto space-y-5 select-none">
      {/* Header */}
      <div className="border-b border-white/50 pb-5">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
          <Wand2 className="w-3.5 h-3.5 text-[#0A0A0A]" />
          <span className="font-semibold">AI Copy Studio // Generative Compliant Rewrite</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A]">Rewrite copy to be on-brand</h2>
            <p className="text-xs text-[#737373] mt-0.5">
              Generates a compliant version grounded in your approved rules, facts and terminology — preserving intent.
            </p>
          </div>
          {status && (
            <div className={`shrink-0 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-[11px] font-mono font-semibold ${status.llm_available ? "bg-[#0A0A0A] text-white" : `${GLASS} text-[#737373]`}`}>
              <Cpu className="w-3.5 h-3.5" />
              <span>{status.llm_available ? `AI live · ${status.model}` : "Heuristic mode — set an LLM API key (ANTHROPIC_API_KEY or GROQ_API_KEY) for generative AI"}</span>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className={`${GLASS} p-4`}>
        <label className="text-[10px] font-mono uppercase text-[#737373] font-semibold block mb-2">Marketing copy</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          className="w-full text-sm bg-white/60 border border-white/70 rounded-xl p-3 text-[#0A0A0A] focus:outline-none focus:border-[#0A0A0A] resize-y leading-relaxed"
          placeholder="Paste marketing copy to rewrite…"
        />
        <div className="flex items-center justify-between mt-3">
          <button onClick={() => { setContent(SAMPLE); setResult(null); }} className="text-[11px] font-mono text-[#737373] hover:text-[#0A0A0A]">
            Load sample
          </button>
          <button onClick={run} disabled={busy || !content.trim()}
                  className="px-5 py-2.5 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] disabled:opacity-40 transition-all flex items-center space-x-2 shadow-sm">
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>{busy ? "Rewriting…" : "Rewrite"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className={`${GLASS} p-4 text-xs font-mono text-[#737373] flex items-center space-x-2`}>
          <Info className="w-4 h-4 text-[#A3A3A3]" /><span>{error}</span>
        </div>
      )}

      {/* Result */}
      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`${GLASS} p-4`}>
              <div className="text-[10px] font-mono uppercase text-[#A3A3A3] font-bold mb-2">Original</div>
              <p className="text-sm text-[#737373] leading-relaxed whitespace-pre-line line-through decoration-[#D4D4D4]">{result.original}</p>
            </div>
            <div className={`${GLASS} p-4 ring-1 ring-[#0A0A0A]/10`}>
              <div className="flex items-center justify-between mb-2">
                <div className="text-[10px] font-mono uppercase text-[#A3A3A3] font-bold">Compliant rewrite</div>
                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full ${isAI ? "bg-[#0A0A0A] text-white" : "bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]"}`}>
                  {isAI ? `AI · ${result.model}` : "rules-based"}
                </span>
              </div>
              <p className="text-sm text-[#0A0A0A] leading-relaxed whitespace-pre-line font-medium">{result.rewritten}</p>
            </div>
          </div>

          <div className={`${GLASS} p-4`}>
            <div className="text-[10px] font-mono uppercase text-[#A3A3A3] font-bold mb-3">
              What changed ({result.changes.length})
            </div>
            {result.changes.length === 0 ? (
              <div className="text-xs text-[#737373]">No changes were needed — this copy is already on-brand.</div>
            ) : (
              <div className="space-y-2">
                {result.changes.map((c, i) => (
                  <div key={i} className="flex items-start space-x-3 px-3 py-2 rounded-lg bg-white/50 border border-white/60">
                    <Check className="w-3.5 h-3.5 text-[#0A0A0A] mt-0.5 shrink-0" />
                    <div className="min-w-0 text-xs">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="line-through text-[#A3A3A3]">{c.from}</span>
                        <ArrowRight className="w-3 h-3 text-[#A3A3A3]" />
                        <span className="font-semibold text-[#0A0A0A]">{c.to}</span>
                      </div>
                      {c.reason && <div className="text-[11px] text-[#737373] mt-0.5">{c.reason}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="text-[10px] font-mono text-[#A3A3A3] mt-3 flex items-center gap-1.5">
              <Info className="w-3 h-3" /> {result.note}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
