"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { Sparkles, Send, ShieldCheck, Info, ArrowUpRight, Loader2, MessageSquare } from "lucide-react";
import { askBrandTwin, TwinAnswer } from "@/lib/api";

const GLASS = "bg-white border border-[#E4E4E7] shadow-[0_1px_2px_rgba(10,10,10,0.04)] rounded-xl";

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
    <div className="max-w-3xl mx-auto space-y-5 select-none">
      {/* Header */}
      <div className="border-b border-[#E4E4E7] pb-5">
        <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">Ask about your brand</h2>
        <p className="text-xs text-[#737373] mt-0.5 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-[#0A0A0A]" />
          Answers come <span className="font-semibold text-[#0A0A0A]">only from your approved brand data</span>, with citations — never invented.
        </p>
      </div>

      {/* Conversation */}
      <div ref={scrollRef} className="space-y-4 max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
        {log.length === 0 && (
          <div className={`${GLASS} p-6 text-center`}>
            <MessageSquare className="w-8 h-8 mx-auto text-[#A3A3A3] mb-3" />
            <p className="text-xs text-[#737373] max-w-sm mx-auto leading-relaxed">
              Ask a question about your pricing, approved claims, brand rules, prohibited terms, or brand voice.
              Every answer is grounded in your organisation&apos;s approved records.
            </p>
          </div>
        )}

        {log.map((t, i) =>
          t.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="bg-[#0A0A0A] text-white text-xs font-medium rounded-lg rounded-br-sm px-4 py-2.5 max-w-[80%]">{t.text}</div>
            </div>
          ) : (
            <div key={i} className={`${GLASS} p-4`}>
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-6 h-6 rounded-lg bg-[#0A0A0A] text-white flex items-center justify-center shrink-0"><Sparkles className="w-3.5 h-3.5" /></div>
                <span className="text-[11px] font-mono font-bold text-[#0A0A0A]">BrandVault</span>
                <span className={`text-[11px] font-mono px-1.5 py-0.5 rounded-full ${t.grounded ? "bg-[#0A0A0A] text-white" : "bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]"}`}>
                  {t.grounded ? "grounded" : "not in approved data"}
                </span>
                {t.phrased_by?.startsWith("llm:") && t.model && (
                  <span className="text-[11px] font-mono px-1.5 py-0.5 rounded-full bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]">AI · {t.model}</span>
                )}
              </div>
              <p className="text-xs text-[#0A0A0A] leading-relaxed whitespace-pre-line">{t.answer}</p>

              {t.evidence.length > 0 && (
                <div className="mt-3 pt-3 border-t border-[#E4E4E7]">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-[#A3A3A3] font-bold mb-2">Sources ({t.evidence.length})</div>
                  <div className="space-y-1.5">
                    {t.evidence.map((e, j) => (
                      <Link key={j} href={e.href} className="block px-3 py-2 rounded-lg bg-white border border-[#E4E4E7] hover:bg-white transition-colors group">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-[#0A0A0A] truncate pr-2">{e.label}{e.page ? ` · p.${e.page}` : ""}</span>
                          <ArrowUpRight className="w-3 h-3 text-[#A3A3A3] group-hover:text-[#0A0A0A] shrink-0" />
                        </div>
                        {e.detail && <div className="text-[11px] text-[#737373] truncate mt-0.5">{e.detail}</div>}
                        {e.source && <div className="text-[11px] font-mono text-[#A3A3A3] truncate mt-0.5">{e.source}</div>}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        )}

        {busy && (
          <div className={`${GLASS} p-4 flex items-center space-x-2 text-[#737373]`}>
            <Loader2 className="w-4 h-4 animate-spin" /><span className="text-xs font-mono">Searching your approved brand data…</span>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {log.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => ask(s)} className={`${GLASS} px-3 py-1.5 text-[11px] font-medium text-[#404040] hover:text-[#0A0A0A] transition-colors`}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Composer */}
      <form onSubmit={(e) => { e.preventDefault(); ask(input); }} className={`${GLASS} p-2 flex items-center gap-2 sticky bottom-2`}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about pricing, claims, rules, terminology…"
          className="flex-1 bg-transparent px-3 py-2 text-xs text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none"
        />
        <button type="submit" disabled={busy || !input.trim()}
                className="px-4 py-2 rounded-lg bg-[#0A0A0A] text-white text-xs font-medium hover:bg-[#27272A] disabled:opacity-40 transition-all flex items-center space-x-1.5">
          <Send className="w-3.5 h-3.5" /><span>Ask</span>
        </button>
      </form>

      <p className="text-[11px] font-mono text-[#A3A3A3] text-center flex items-center justify-center gap-1.5">
        <Info className="w-3 h-3" /> Deterministic, grounded answers from approved records. It does not take actions or browse the web.
      </p>
    </div>
  );
}
