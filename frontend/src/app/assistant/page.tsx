"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { Sparkles, Send, ShieldCheck, Info, ArrowUpRight, Loader2, MessageSquare } from "lucide-react";
import { askBrandTwin, TwinAnswer } from "@/lib/api";

const SUGGESTIONS = [
  "What is the approved launch price?",
  "Which brand rules are most often violated?",
  "What terms are prohibited?",
  "Which claims and facts are approved?",
  "Explain our brand voice and tone.",
];

type Turn = { role: "user"; text: string } | ({ role: "assistant" } & TwinAnswer);

export default function AssistantPage() {
  const [log, setLog] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const ask = async (question: string) => {
    const q = question.trim();
    if (!q || busy) return;
    setInput("");
    setLog((l) => [...l, { role: "user", text: q }]);
    setBusy(true);
    try {
      const ans = await askBrandTwin(q);
      setLog((l) => [...l, { role: "assistant", ...ans }]);
    } catch {
      setLog((l) => [...l, {
        role: "assistant", intent: "error", grounded: false, question: q,
        answer: "I couldn't reach the backend. Make sure the server is running, then try again.",
        evidence: [], suggestions: [],
      }]);
    } finally {
      setBusy(false);
      setTimeout(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }), 50);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 select-none">
      {/* Header */}
      <div className="border-b border-slate-200/80 pb-5">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-indigo-200 bg-indigo-50/80 text-[11px] font-bold uppercase tracking-wider text-indigo-700 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Brand Intelligence Assistant</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Ask about your brand</h2>
        <p className="text-xs text-slate-600 mt-1 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Answers come <span className="font-semibold text-slate-900">only from your approved brand data</span>, with citations — never invented.
        </p>
      </div>

      {/* Conversation */}
      <div ref={scrollRef} className="space-y-4 max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
        {log.length === 0 && (
          <div className="bg-gradient-to-br from-indigo-50/70 via-white to-purple-50/40 border border-indigo-100/80 shadow-soft rounded-2xl p-8 text-center">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white flex items-center justify-center mx-auto mb-3 shadow-md shadow-indigo-500/20">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 mb-1">Grounded Brand Intelligence</h3>
            <p className="text-xs text-slate-600 max-w-sm mx-auto leading-relaxed">
              Ask a question about your pricing, approved claims, brand rules, prohibited terms, or brand voice.
              Every answer is verified against your organisation&apos;s approved records.
            </p>
          </div>
        )}

        {log.map((t, i) =>
          t.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white text-xs font-medium rounded-2xl rounded-br-sm px-5 py-3 max-w-[80%] shadow-md shadow-indigo-500/15">
                {t.text}
              </div>
            </div>
          ) : (
            <div key={i} className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-5">
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                  <Sparkles className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-900">BrandVault Twin</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${t.grounded ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-rose-50 text-rose-700 border-rose-200"}`}>
                  {t.grounded ? "Grounded in approved DNA" : "Not found in approved data"}
                </span>
                {t.phrased_by?.startsWith("llm:") && t.model && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">AI · {t.model}</span>
                )}
              </div>
              <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line font-medium">{t.answer}</p>

              {t.evidence.length > 0 && (
                <div className="mt-4 pt-3.5 border-t border-slate-100">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Sources ({t.evidence.length})</div>
                  <div className="space-y-1.5">
                    {t.evidence.map((e, j) => (
                      <Link key={j} href={e.href} className="block px-3.5 py-2.5 rounded-xl bg-slate-50/80 border border-slate-200/60 hover:bg-indigo-50/50 hover:border-indigo-200 transition-colors group">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-indigo-900 group-hover:text-indigo-600 transition-colors truncate pr-2">
                            {e.label}{e.page ? ` · p.${e.page}` : ""}
                          </span>
                          <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 shrink-0" />
                        </div>
                        {e.detail && <div className="text-[11px] text-slate-600 truncate mt-0.5">{e.detail}</div>}
                        {e.source && <div className="text-[10px] font-mono text-slate-400 truncate mt-0.5">{e.source}</div>}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        )}

        {busy && (
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-4 flex items-center space-x-2 text-indigo-600">
            <Loader2 className="w-4 h-4 animate-spin" /><span className="text-xs font-semibold">Searching your approved brand data…</span>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {log.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => ask(s)} className="px-3.5 py-2 rounded-xl bg-white border border-indigo-200 text-xs font-semibold text-indigo-700 hover:bg-indigo-50 hover:border-indigo-300 transition-all shadow-sm">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Composer */}
      <form onSubmit={(e) => { e.preventDefault(); ask(input); }} className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-2 flex items-center gap-2 sticky bottom-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about pricing, claims, rules, terminology…"
          className="flex-1 bg-transparent px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none"
        />
        <button type="submit" disabled={busy || !input.trim()}
                className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white text-xs font-semibold disabled:opacity-40 transition-all flex items-center space-x-1.5 shadow-md shadow-indigo-500/20">
          <Send className="w-3.5 h-3.5" /><span>Ask</span>
        </button>
      </form>

      <p className="text-[11px] font-medium text-slate-400 text-center flex items-center justify-center gap-1.5">
        <Info className="w-3.5 h-3.5 text-indigo-500" /> Deterministic, grounded answers from approved records. Never invents policy.
      </p>
    </div>
  );
}
