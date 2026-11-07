"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ImageOff, Loader2 } from "lucide-react";
import { fetchProtectedImage } from "@/lib/api";

export const CARD = "bg-white border border-slate-200/80 shadow-soft rounded-2xl";

const TONES: Record<string, string> = {
  good: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  warn: "bg-amber-50 text-amber-700 ring-amber-200",
  bad: "bg-rose-50 text-rose-700 ring-rose-200",
  info: "bg-sky-50 text-sky-700 ring-sky-200",
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
  ai: "bg-violet-50 text-violet-700 ring-violet-200",
};
export type Tone = keyof typeof TONES;

export function Badge({ tone = "neutral", children, className = "" }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ring-1 whitespace-nowrap ${TONES[tone]} ${className}`}>
      {children}
    </span>
  );
}

export function PageHeader({ back, eyebrow, icon, title, description, actions }: {
  back?: { href: string; label: string }; eyebrow: string; icon: ReactNode; title: string; description: string; actions?: ReactNode;
}) {
  return (
    <div className="space-y-3">
      {back && (
        <Link href={back.href} className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-indigo-700">
          <ArrowLeft className="w-3.5 h-3.5" /> {back.label}
        </Link>
      )}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 mb-1.5">{icon} {eyebrow}</div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h2>
          <p className="text-[13px] text-slate-600 mt-1 max-w-3xl">{description}</p>
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>}
      </div>
    </div>
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return <div role="alert" className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{message}</div>;
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-[13px] text-slate-500 py-6 justify-center">
      <Loader2 className="w-4 h-4 animate-spin" /> {label}
    </div>
  );
}

export const BTN_PRIMARY =
  "h-10 px-4 inline-flex items-center justify-center gap-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 disabled:opacity-40 shadow-md shadow-indigo-500/20 transition-all";
export const BTN_SECONDARY =
  "h-9 px-3 inline-flex items-center justify-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-colors";
export const INPUT =
  "w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 focus:outline-none focus:border-indigo-500 focus:bg-white transition-colors";

/** Image that needs the bearer token (files are not publicly served). */
export function ProtectedImage({ path, alt, className, onSize }: {
  path: string; alt: string; className?: string; onSize?: (w: number, h: number) => void;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let revoke: string | null = null;
    let cancelled = false;
    setUrl(null);
    setFailed(false);
    fetchProtectedImage(path)
      .then((u) => { if (cancelled) URL.revokeObjectURL(u); else { revoke = u; setUrl(u); } })
      .catch(() => !cancelled && setFailed(true));
    return () => { cancelled = true; if (revoke) URL.revokeObjectURL(revoke); };
  }, [path]);
  if (failed) {
    return <div className={`flex items-center justify-center bg-slate-100 text-slate-400 ${className}`}><ImageOff className="w-5 h-5" /></div>;
  }
  if (!url) return <div className={`animate-pulse bg-slate-100 ${className}`} />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={alt} className={className} onLoad={(e) => onSize?.(e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)} />;
}
