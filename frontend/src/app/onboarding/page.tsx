"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Rocket, Check, ArrowRight, ArrowUpRight, Loader2, Info, Sparkles } from "lucide-react";
import { fetchOnboardingStatus, OnboardingStatus } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function OnboardingPage() {
  const { user } = useAuth();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => fetchOnboardingStatus().then(setStatus).catch((e) => setError(e?.message || "Failed to load"));
  useEffect(() => { load(); }, []);

  const firstName = (user?.full_name || "there").split(/\s+/)[0];

  return (
    <div className="max-w-3xl mx-auto space-y-6 select-none">
      {/* Header */}
      <div className="border-b border-[#E5E5E5] pb-5">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
          <Rocket className="w-3.5 h-3.5 text-[#0A0A0A]" />
          <span className="font-semibold">Guided setup // Get your workspace ready</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#0A0A0A]">Welcome, {firstName} 👋</h2>
        <p className="text-xs text-[#737373] mt-1">
          A few steps take a brand from zero to certified governance. Each item below reflects your
          <span className="font-semibold text-[#0A0A0A]"> real saved configuration</span> — not a checklist you tick manually.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-[#E5E5E5] bg-white text-xs font-mono text-[#737373] flex items-center space-x-2">
          <Info className="w-4 h-4 text-[#A3A3A3]" />
          <span>{error}. Is the backend running?</span>
        </div>
      )}

      {!status && !error && (
        <div className="flex items-center justify-center py-16 text-[#737373]"><Loader2 className="w-5 h-5 animate-spin" /></div>
      )}

      {status && (
        <>
          {/* Progress */}
          <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-bold text-[#0A0A0A]">Setup progress</div>
              <div className="text-xs font-mono text-[#737373]">{status.completed} of {status.total} complete</div>
            </div>
            <div className="h-2.5 w-full rounded-full bg-[#F0F0F0] overflow-hidden">
              <div className="h-full bg-[#0A0A0A] rounded-full transition-[width] duration-500" style={{ width: `${status.completion}%` }} />
            </div>
            <div className="mt-1.5 text-right text-[11px] font-mono font-bold text-[#0A0A0A]">{status.completion}%</div>

            {status.is_demo && (
              <div className="mt-3 flex items-start space-x-2 text-[11px] text-[#404040] bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg px-3 py-2">
                <Sparkles className="w-3.5 h-3.5 mt-0.5 text-[#0A0A0A] shrink-0" />
                <span>
                  You&apos;re exploring the pre-loaded <span className="font-semibold text-[#0A0A0A]">{status.org.name}</span> demo
                  workspace — these steps are already satisfied with clearly-labelled sample data, so you can try the full
                  workflow immediately.
                </span>
              </div>
            )}
          </div>

          {/* Steps */}
          <div className="space-y-2.5">
            {status.steps.map((s, i) => (
              <div
                key={s.key}
                className={`bg-white rounded-xl border shadow-sm p-4 flex items-start justify-between gap-4 ${s.done ? "border-[#E5E5E5]" : "border-[#0A0A0A]"}`}
              >
                <div className="flex items-start space-x-3 min-w-0">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-mono font-bold ${s.done ? "bg-[#0A0A0A] text-white" : "bg-[#F5F5F5] text-[#737373] border border-[#E5E5E5]"}`}>
                    {s.done ? <Check className="w-3.5 h-3.5" /> : i + 1}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-[#0A0A0A] flex items-center gap-2">
                      {s.label}
                      {s.count !== null && s.count !== undefined && (
                        <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-[#F5F5F5] border border-[#E5E5E5] text-[#404040]">
                          {s.total !== undefined ? `${s.count}/${s.total}` : s.count}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-[#737373] mt-0.5 leading-relaxed">{s.hint}</div>
                  </div>
                </div>
                <Link
                  href={s.href}
                  className={`shrink-0 inline-flex items-center space-x-1.5 px-3 py-1.5 text-[11px] font-mono font-semibold rounded-lg transition-all ${s.done ? "border border-[#E5E5E5] bg-white text-[#0A0A0A] hover:bg-[#F5F5F5]" : "bg-[#0A0A0A] text-white hover:bg-[#262626]"}`}
                >
                  <span>{s.done ? "Review" : "Set up"}</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-[#0A0A0A] rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <div className="text-sm font-bold text-white">
                {status.completion === 100 ? "You're all set." : "Jump in any time."}
              </div>
              <div className="text-[11px] text-[#A3A3A3] mt-0.5">
                {status.completion === 100
                  ? "Your workspace is fully configured. Head to the Command Center."
                  : "You can explore the Command Center while you finish setup."}
              </div>
            </div>
            <Link href="/dashboard" className="inline-flex items-center space-x-2 px-5 py-3 text-xs font-mono font-bold rounded-xl bg-white text-[#0A0A0A] hover:bg-[#E5E5E5] transition-all shadow-sm">
              <span>Enter Command Center</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
