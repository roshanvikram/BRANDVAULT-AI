"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { ArrowRight, LucideIcon } from "lucide-react";

/**
 * Smart empty state (R2-1). Never a blank screen: it explains what the page
 * does, why it matters, what to do next, and gives a clear primary action
 * (and an optional example). Reusable across modules.
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  example,
  compact = false,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  example?: ReactNode;
  compact?: boolean;
}) {
  const action = actionLabel && (
    actionHref ? (
      <Link
        href={actionHref}
        className="inline-flex items-center space-x-2 px-4 py-2.5 text-xs font-mono font-bold rounded-lg bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all shadow-sm"
      >
        <span>{actionLabel}</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    ) : (
      <button
        onClick={onAction}
        className="inline-flex items-center space-x-2 px-4 py-2.5 text-xs font-mono font-bold rounded-lg bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all shadow-sm"
      >
        <span>{actionLabel}</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </button>
    )
  );

  return (
    <div className={`flex flex-col items-center justify-center text-center ${compact ? "py-8" : "py-14"} px-6`}>
      <div className="w-12 h-12 rounded-2xl bg-[#F5F5F5] border border-[#E5E5E5] flex items-center justify-center mb-4">
        <Icon className="w-5 h-5 text-[#0A0A0A]" />
      </div>
      <h3 className="text-sm font-bold tracking-tight text-[#0A0A0A]">{title}</h3>
      <p className="text-xs text-[#737373] mt-1.5 max-w-sm leading-relaxed">{description}</p>
      {example && (
        <div className="mt-3 text-[11px] font-mono text-[#404040] bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg px-3 py-2 max-w-sm">
          {example}
        </div>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
