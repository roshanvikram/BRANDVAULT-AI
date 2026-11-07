"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, Clock, Award, AlertTriangle, Loader2 } from "lucide-react";
import { fetchSubmissions, fetchPassports, Submission, BrandPassport } from "@/lib/api";
import { useClickOutside } from "@/lib/useClickOutside";

type Note = {
  id: string;
  kind: "review" | "critical" | "passport";
  title: string;
  detail: string;
  href: string;
  when: string;
};

/**
 * Real notifications derived from backend state:
 *  - submissions awaiting human review  -> Approval Hub
 *  - submissions carrying CRITICAL findings -> Content Intelligence
 *  - recently issued Brand Passports
 * The unread dot reflects the count of actionable (review) items, not a static
 * badge.
 */
export function NotificationsMenu() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [subs, setSubs] = useState<Submission[] | null>(null);
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => setOpen(false), open);

  const load = () => {
    fetchSubmissions().then(setSubs).catch(() => setSubs([]));
    fetchPassports().then((p) => setPassports(p.slice(0, 3))).catch(() => setPassports([]));
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30_000); // keep the badge current
    return () => clearInterval(t);
  }, []);

  const notes = useMemo<Note[]>(() => {
    const list: Note[] = [];
    (subs || []).forEach((s) => {
      const when = new Date(s.updated_at || s.created_at).toLocaleString();
      if (s.status === "Pending Review" || s.status === "Analysed") {
        list.push({
          id: `rev-${s.id}`, kind: "review",
          title: "Awaiting review", detail: s.title,
          href: "/approval-hub", when,
        });
      }
      const crit = s.findings?.filter((f) => f.severity === "CRITICAL").length || 0;
      if (crit > 0) {
        list.push({
          id: `crit-${s.id}`, kind: "critical",
          title: `${crit} critical finding${crit > 1 ? "s" : ""}`, detail: s.title,
          href: `/content-intelligence?submissionId=${s.id}`, when,
        });
      }
    });
    passports.forEach((p) => {
      list.push({
        id: `pp-${p.id}`, kind: "passport",
        title: "Brand Passport issued", detail: `${p.passport_number} · ${p.content_title}`,
        href: "/brand-passport", when: new Date(p.issued_at).toLocaleString(),
      });
    });
    return list;
  }, [subs, passports]);

  const reviewCount = (subs || []).filter((s) => s.status === "Pending Review" || s.status === "Analysed").length;

  const go = (href: string) => { setOpen(false); router.push(href); };

  const Icon = ({ kind }: { kind: Note["kind"] }) =>
    kind === "review" ? <Clock className="w-3.5 h-3.5" />
      : kind === "critical" ? <AlertTriangle className="w-3.5 h-3.5" />
        : <Award className="w-3.5 h-3.5" />;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        title="Notifications"
        className="relative p-2 rounded-xl text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] cursor-pointer transition-colors"
      >
        <Bell className="w-4 h-4" />
        {reviewCount > 0 && (
          <span className="absolute top-1 right-1 min-w-[14px] h-[14px] px-0.5 rounded-full bg-[#0A0A0A] ring-2 ring-white text-[8px] font-medium text-white flex items-center justify-center">
            {reviewCount > 9 ? "9+" : reviewCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-xl border border-[#E4E4E7] bg-white shadow-[0_12px_32px_-8px_rgba(10,10,10,0.16)] z-50 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-[#F0F0F0] flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase font-bold text-[#A3A3A3]">Notifications</span>
            <span className="text-[11px] font-mono text-[#737373]">{notes.length} total</span>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {subs === null ? (
              <div className="px-4 py-8 flex items-center justify-center text-[#737373]">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            ) : notes.length === 0 ? (
              <div className="px-4 py-8 text-center text-xs text-[#737373] font-mono">
                You&apos;re all caught up.
              </div>
            ) : (
              notes.map((n) => (
                <button
                  key={n.id}
                  onClick={() => go(n.href)}
                  className="w-full text-left px-4 py-3 flex items-start space-x-2.5 hover:bg-[#FAFAFA] border-b border-[#F5F5F5] last:border-0 transition-colors"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5] flex items-center justify-center shrink-0 text-[#0A0A0A]">
                    <Icon kind={n.kind} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-bold text-[#0A0A0A]">{n.title}</div>
                    <div className="text-[11px] text-[#737373] truncate">{n.detail}</div>
                    <div className="text-[11px] font-mono text-[#A3A3A3] mt-0.5">{n.when}</div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
