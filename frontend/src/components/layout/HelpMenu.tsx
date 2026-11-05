"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { HelpCircle, BookOpen, Keyboard, ExternalLink, Workflow } from "lucide-react";
import { useClickOutside } from "@/lib/useClickOutside";

const API_DOCS = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1").replace(/\/api\/v1\/?$/, "/docs");

const STEPS = [
  { n: 1, t: "Brand DNA", d: "Review approved rules, facts & terminology." },
  { n: 2, t: "Content Intelligence", d: "Analyse copy against the brand DNA." },
  { n: 3, t: "Approval Hub", d: "A Reviewer/Admin signs off (never the AI)." },
  { n: 4, t: "Brand Passport", d: "Approved content is certified & hashed." },
];

const SHORTCUTS = [
  { k: "⌘ / Ctrl + K", d: "Focus global search" },
  { k: "Esc", d: "Close menus & panels" },
];

export function HelpMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => setOpen(false), open);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        title="Help & workflow"
        className="p-2 rounded-xl text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] cursor-pointer transition-colors"
      >
        <HelpCircle className="w-4 h-4" />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-xl border border-white/70 bg-white/85 backdrop-blur-xl shadow-[0_16px_40px_-12px_rgba(10,10,10,0.25)] z-50 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-[#F0F0F0] flex items-center space-x-1.5">
            <Workflow className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span className="text-[10px] font-mono uppercase font-bold text-[#A3A3A3]">Governance Workflow</span>
          </div>
          <div className="p-3 space-y-1.5">
            {STEPS.map((s) => (
              <div key={s.n} className="flex items-start space-x-2.5 px-1.5 py-1">
                <div className="w-5 h-5 rounded-md bg-[#0A0A0A] text-white text-[10px] font-mono font-bold flex items-center justify-center shrink-0 mt-0.5">
                  {s.n}
                </div>
                <div>
                  <div className="text-xs font-bold text-[#0A0A0A]">{s.t}</div>
                  <div className="text-[11px] text-[#737373] leading-snug">{s.d}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="px-4 py-2.5 border-t border-[#F0F0F0] flex items-center space-x-1.5">
            <Keyboard className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span className="text-[10px] font-mono uppercase font-bold text-[#A3A3A3]">Shortcuts</span>
          </div>
          <div className="px-4 pb-2 space-y-1">
            {SHORTCUTS.map((s) => (
              <div key={s.k} className="flex items-center justify-between text-[11px]">
                <span className="text-[#737373]">{s.d}</span>
                <kbd className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#F5F5F5] border border-[#E5E5E5] text-[#0A0A0A]">{s.k}</kbd>
              </div>
            ))}
          </div>

          <div className="px-3 py-2.5 border-t border-[#F0F0F0] flex items-center gap-2">
            <Link
              href="/settings"
              onClick={() => setOpen(false)}
              className="flex-1 inline-flex items-center justify-center space-x-1.5 text-[11px] font-mono font-semibold px-2 py-1.5 rounded-lg border border-[#E5E5E5] bg-white text-[#0A0A0A] hover:bg-[#F5F5F5] transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>System</span>
            </Link>
            <a
              href={API_DOCS}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center space-x-1.5 text-[11px] font-mono font-semibold px-2 py-1.5 rounded-lg border border-[#E5E5E5] bg-white text-[#0A0A0A] hover:bg-[#F5F5F5] transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>API Docs</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
