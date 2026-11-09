"use client";

import { Rocket as RocketHdr } from "lucide-react";
import { PageHeader } from "@/components/engines/ui";
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
      <PageHeader
        eyebrow="Setup Guide"
        icon={<RocketHdr />}
        title={`Welcome, ${firstName}`}
        description="A few steps take a brand from zero to certified governance. Each item reflects your real saved configuration, not a checklist you tick by hand."
      />

      {error && (
        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-xs font-medium text-rose-700 flex items-center space-x-2">
          <Info className="w-4 h-4 text-rose-500" />
          <span>{error}. Is the backend running?</span>
        </div>
      )}

      {!status && !error && (
        <div className="flex items-center justify-center py-16 text-indigo-600"><Loader2 className="w-6 h-6 animate-spin" /></div>
      )}

      {status && (
        <>
          {/* Progress */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-bold text-slate-900">Setup progress</div>
              <div className="text-xs font-semibold text-indigo-600">{status.completed} of {status.total} complete</div>
            </div>
            <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden p-0.5">
              <div className="h-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-full transition-[width] duration-500" style={{ width: `${status.completion}%` }} />
            </div>
            <div className="mt-2 text-right text-xs font-bold text-slate-900">{status.completion}%</div>

            {status.is_demo && (
              <div className="mt-4 flex items-start space-x-2.5 text-xs text-indigo-900 bg-indigo-50/70 border border-indigo-200 rounded-xl px-4 py-3">
                <Sparkles className="w-4 h-4 mt-0.5 text-indigo-600 shrink-0" />
                <span>
                  You&apos;re exploring the pre-loaded <span className="font-bold text-indigo-900">{status.org.name}</span> demo
                  workspace — these steps are already satisfied with clearly-labelled sample data, so you can try the full
                  workflow immediately.
                </span>
              </div>
            )}
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {status.steps.map((s, i) => (
              <div
                key={s.key}
                className={`bg-white rounded-2xl border shadow-soft p-5 flex items-start justify-between gap-4 transition-all ${s.done ? "border-slate-200/80 hover:border-slate-300" : "border-indigo-300 ring-1 ring-indigo-300/40"}`}
              >
                <div className="flex items-start space-x-3.5 min-w-0">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${s.done ? "bg-emerald-100 text-emerald-700" : "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"}`}>
                    {s.done ? <Check className="w-4 h-4" /> : i + 1}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      {s.label}
                      {s.count !== null && s.count !== undefined && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700">
                          {s.total !== undefined ? `${s.count}/${s.total}` : s.count}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-600 mt-1 leading-relaxed">{s.hint}</div>
                  </div>
                </div>
                <Link
                  href={s.href}
                  className={`shrink-0 inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl transition-all ${s.done ? "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50" : "bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-500/20 hover:from-indigo-700 hover:to-indigo-800"}`}
                >
                  <span>{s.done ? "Review" : "Set up"}</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-gradient-to-br from-indigo-50/80 via-white to-purple-50/60 border border-indigo-200/80 shadow-soft rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <div className="text-base font-bold text-slate-900">
                {status.completion === 100 ? "You're all set." : "Jump in any time."}
              </div>
              <div className="text-xs text-slate-600 mt-0.5">
                {status.completion === 100
                  ? "Your workspace is fully configured. Head to the Command Center."
                  : "You can explore the Command Center while you finish setup."}
              </div>
            </div>
            <Link href="/dashboard" className="inline-flex items-center space-x-2 px-5 py-3 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all shadow-md shadow-indigo-500/20 active:scale-[0.99]">
              <span>Enter Command Center</span>
              <ArrowRight className="w-3.5 h-3.5 text-indigo-200" />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
