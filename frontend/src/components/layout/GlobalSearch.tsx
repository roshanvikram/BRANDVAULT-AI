"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Dna, CheckCircle2, FileText, Ban, CornerDownLeft } from "lucide-react";
import {
  fetchRules, fetchFacts, fetchTerms, fetchSubmissions,
  BrandRule, ApprovedFact, TerminologyRule, Submission,
} from "@/lib/api";
import { useClickOutside } from "@/lib/useClickOutside";

type Result = { id: string; group: string; label: string; sub: string; href: string; icon: "rule" | "fact" | "term" | "sub" };

/**
 * Global search over real backend data (brand rules, approved facts,
 * terminology, and submissions). The corpus is fetched once on first focus and
 * filtered client-side; selecting a result navigates to the owning module.
 */
export function GlobalSearch() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const boxRef = useRef<HTMLDivElement>(null);
  useClickOutside(boxRef, () => setOpen(false), open);

  const [rules, setRules] = useState<BrandRule[]>([]);
  const [facts, setFacts] = useState<ApprovedFact[]>([]);
  const [terms, setTerms] = useState<TerminologyRule[]>([]);
  const [subs, setSubs] = useState<Submission[]>([]);
  const [loaded, setLoaded] = useState(false);

  const ensureCorpus = () => {
    if (loaded) return;
    setLoaded(true);
    fetchRules().then(setRules).catch(() => {});
    fetchFacts().then(setFacts).catch(() => {});
    fetchTerms().then(setTerms).catch(() => {});
    fetchSubmissions().then(setSubs).catch(() => {});
  };

  // ⌘K / Ctrl+K focuses the search.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
        ensureCorpus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loaded]);

  const results = useMemo<Result[]>(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return [];
    const has = (s?: string) => (s || "").toLowerCase().includes(needle);
    const out: Result[] = [];
    rules.forEach((r) => {
      if (has(r.title) || has(r.rule_text) || has(r.category))
        out.push({ id: `r-${r.id}`, group: "Brand Rules", label: r.title, sub: r.category, href: "/brand-dna", icon: "rule" });
    });
    facts.forEach((f) => {
      if (has(f.fact_key) || has(f.fact_value) || has(f.category))
        out.push({ id: `f-${f.id}`, group: "Approved Facts", label: f.fact_key, sub: f.fact_value, href: "/claim-dna", icon: "fact" });
    });
    terms.forEach((t) => {
      if (has(t.prohibited_term) || has(t.preferred_term))
        out.push({ id: `t-${t.id}`, group: "Terminology", label: t.prohibited_term, sub: `→ ${t.preferred_term}`, href: "/brand-dna", icon: "term" });
    });
    subs.forEach((s) => {
      if (has(s.title) || has(s.content))
        out.push({ id: `s-${s.id}`, group: "Submissions", label: s.title, sub: s.status, href: `/content-intelligence?submissionId=${s.id}`, icon: "sub" });
    });
    return out.slice(0, 12);
  }, [q, rules, facts, terms, subs]);

  useEffect(() => setActive(0), [q]);

  const go = (r?: Result) => {
    const target = r || results[active];
    if (!target) return;
    setOpen(false);
    setQ("");
    router.push(target.href);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((i) => Math.min(i + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); go(); }
  };

  const Ico = ({ t }: { t: Result["icon"] }) =>
    t === "rule" ? <Dna className="w-3.5 h-3.5" />
      : t === "fact" ? <CheckCircle2 className="w-3.5 h-3.5" />
        : t === "term" ? <Ban className="w-3.5 h-3.5" />
          : <FileText className="w-3.5 h-3.5" />;

  return (
    <div className="hidden md:block w-full max-w-md relative" ref={boxRef}>
      <div className="relative">
        <Search className="w-4 h-4 text-[#A3A3A3] absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          ref={inputRef}
          type="text"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => { setOpen(true); ensureCorpus(); }}
          onKeyDown={onKeyDown}
          placeholder="Search guidelines, claims, rules, or campaigns… (⌘K)"
          className="w-full h-9 pl-10 pr-4 text-[13px] bg-[#F4F4F5] border border-transparent hover:border-[#E4E4E7] focus:border-[#0A0A0A] focus:bg-white rounded-lg text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none transition-all"
        />
      </div>

      {open && q.trim() && (
        <div className="absolute left-0 right-0 mt-2 rounded-xl border border-[#E4E4E7] bg-white shadow-[0_12px_32px_-8px_rgba(10,10,10,0.16)] z-50 overflow-hidden">
          {results.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-[#737373] font-mono">
              No matches for “{q.trim()}”.
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto py-1">
              {results.map((r, i) => (
                <button
                  key={r.id}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => go(r)}
                  className={`w-full text-left px-3.5 py-2.5 flex items-center space-x-2.5 transition-colors ${i === active ? "bg-[#F5F5F5]" : "hover:bg-[#FAFAFA]"}`}
                >
                  <div className="w-7 h-7 rounded-lg bg-white border border-[#E5E5E5] flex items-center justify-center shrink-0 text-[#0A0A0A]">
                    <Ico t={r.icon} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-bold text-[#0A0A0A] truncate">{r.label}</div>
                    <div className="text-[11px] font-mono text-[#737373] truncate">{r.group} · {r.sub}</div>
                  </div>
                  {i === active && <CornerDownLeft className="w-3.5 h-3.5 text-[#A3A3A3] shrink-0" />}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
