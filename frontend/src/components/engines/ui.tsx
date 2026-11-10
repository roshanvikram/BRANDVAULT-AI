"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ImageOff, Loader2 } from "lucide-react";
import { fetchProtectedImage } from "@/lib/api";
import { HeroArt } from "./HeroArt";

export const CARD = "bv-glass-edge bg-white/80 border border-white/75 rounded-2xl";

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

export interface HeaderStat { label: string; value: ReactNode; tone?: Tone }

/** Hero page header used by every module: icon tile, eyebrow, title, description, actions and optional stat chips. */
export function PageHeader({ back, eyebrow, icon, title, description, actions, stats, status }: {
  back?: { href: string; label: string }; eyebrow: string; icon: ReactNode; title: ReactNode; description: ReactNode;
  actions?: ReactNode; stats?: HeaderStat[]; status?: ReactNode;
}) {
  return (
    <div className="space-y-3">
      {back && (
        <Link href={back.href} className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-indigo-700 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> {back.label}
        </Link>
      )}
      <header className="relative overflow-hidden rounded-3xl border border-white/70 bg-white/60 backdrop-blur-2xl backdrop-saturate-150 px-5 py-5 sm:px-7 sm:py-6 shadow-[0_1px_2px_rgba(34,36,39,0.04),0_16px_40px_-20px_rgba(34,36,39,0.25)]">
        <div aria-hidden className="pointer-events-none absolute -top-24 -right-16 w-72 h-72 rounded-full bg-violet-200/40 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute -bottom-28 right-40 w-64 h-64 rounded-full bg-indigo-200/30 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute inset-0 bv-grid opacity-[0.35]" />
        <HeroArt eyebrow={eyebrow} />
        <div className="relative flex flex-col lg:flex-row lg:items-center xl:flex-col xl:items-start justify-between gap-5 xl:pr-[320px]">
          <div className="flex items-start gap-4 min-w-0">
            <span className="hidden sm:flex w-12 h-12 shrink-0 rounded-2xl bg-slate-900 text-indigo-300 ring-1 ring-indigo-500/40 items-center justify-center shadow-lg shadow-slate-900/25 [&>svg]:w-5 [&>svg]:h-5">{icon}</span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-indigo-600">{eyebrow}</span>
                {status}
              </div>
              <h2 className="text-[26px] sm:text-[28px] leading-tight font-semibold tracking-tight text-slate-900">{title}</h2>
              <p className="text-[13.5px] text-slate-500 mt-1.5 max-w-3xl leading-relaxed">{description}</p>
            </div>
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>}
        </div>
        {stats && stats.length > 0 && (
          <dl className="relative mt-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {stats.map((s) => (
              <div key={s.label} className="rounded-2xl bg-white/70 ring-1 ring-white/80 shadow-sm px-3.5 py-2.5">
                <dt className="text-[11px] text-slate-500 truncate">{s.label}</dt>
                <dd className={`text-lg font-semibold tabular-nums leading-tight ${s.tone === "bad" ? "text-rose-600" : s.tone === "warn" ? "text-amber-600" : s.tone === "good" ? "text-emerald-600" : "text-slate-900"}`}>{s.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </header>
    </div>
  );
}

/** Shimmering placeholder while data loads. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`bv-shimmer rounded-xl bg-slate-100 ${className}`} />;
}

export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className={`${CARD} p-5 space-y-3`} role="status" aria-label="Loading">
      <Skeleton className="h-4 w-1/3" />
      {Array.from({ length: rows }).map((_, i) => <Skeleton key={i} className="h-3" />)}
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
  "h-10 px-4 inline-flex items-center justify-center gap-2 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-40 disabled:pointer-events-none shadow-sm shadow-indigo-600/25 ring-1 ring-inset ring-white/10 transition-colors focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/25";
export const BTN_SECONDARY =
  "h-9 px-3 inline-flex items-center justify-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 shadow-[0_1px_1px_rgba(34,36,39,0.04)] hover:bg-slate-50 hover:border-slate-300 disabled:opacity-40 disabled:pointer-events-none transition-colors focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/15";
export const INPUT =
  "w-full text-sm bg-white border border-slate-200 rounded-xl px-3 placeholder:text-slate-400 shadow-[0_1px_1px_rgba(34,36,39,0.03)] focus:outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 transition-[border-color,box-shadow]";

/** Pill-style segmented control (period pickers, view toggles). */
export function Segmented<T extends string | number>({ value, options, onChange, label }: {
  value: T; options: { value: T; label: string }[]; onChange: (v: T) => void; label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex items-center p-0.5 rounded-xl bg-slate-100/80 ring-1 ring-slate-200/70">
      {options.map((o) => (
        <button key={String(o.value)} role="radio" aria-checked={o.value === value} onClick={() => onChange(o.value)}
          className={`h-7 px-2.5 rounded-[10px] text-xs font-semibold tabular-nums transition-all ${o.value === value ? "bg-white text-slate-900 shadow-sm ring-1 ring-slate-200/80" : "text-slate-500 hover:text-slate-800"}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

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
