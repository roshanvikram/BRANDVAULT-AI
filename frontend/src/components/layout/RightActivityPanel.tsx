"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Bot,
  UserCheck,
  Award,
  ArrowRight,
  ShieldCheck,
  Clock,
  ChevronRight,
  TrendingUp,
  AlertCircle
} from "lucide-react";
import { fetchAgentRuns, fetchPassports, fetchSubmissions, AgentRun, BrandPassport, Submission } from "@/lib/api";

export function RightActivityPanel() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);

  useEffect(() => {
    fetchAgentRuns().then((data) => setRuns(data.slice(0, 4))).catch(console.error);
    fetchPassports().then((data) => setPassports(data.slice(0, 2))).catch(console.error);
    fetchSubmissions().then(setSubmissions).catch(console.error);
  }, []);

  const pendingCount = submissions.filter((s) => s.status === "Pending Review" || s.status === "Analysed").length;

  return (
    <aside className="w-full xl:w-[285px] shrink-0 space-y-4 select-none">
      {/* Primary Action Button */}
      <Link
        href="/content-intelligence"
        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white text-xs font-semibold tracking-wide transition-all shadow-md shadow-indigo-500/20 flex items-center justify-center space-x-2 group active:scale-[0.99]"
      >
        <Sparkles className="w-4 h-4 text-indigo-200" />
        <span>New Content Review</span>
        <ArrowRight className="w-3.5 h-3.5 text-indigo-200 group-hover:translate-x-0.5 transition-transform" />
      </Link>

      {/* Governance Reviewers Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-soft space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-slate-900">Governance Reviewers</div>
            <div className="text-[11px] text-slate-500">Signoff authority active</div>
          </div>
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-semibold border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Online</span>
          </span>
        </div>

        {/* Reviewer Avatars with vibrant color rings */}
        <div className="flex items-center -space-x-2 pt-1">
          {[
            { initials: "DM", name: "Deepak Mouriya M", role: "Team Leader", bg: "bg-indigo-100 text-indigo-700 ring-indigo-300" },
            { initials: "RV", name: "Roshan Vikram AV", role: "Lead Engineer", bg: "bg-violet-100 text-violet-700 ring-violet-300" },
            { initials: "PR", name: "Preethish", role: "Governance Lead", bg: "bg-emerald-100 text-emerald-700 ring-emerald-300" },
            { initials: "AR", name: "Aishwarya R M", role: "Brand Reviewer", bg: "bg-rose-100 text-rose-700 ring-rose-300" },
          ].map((user, i) => (
            <div
              key={i}
              title={`${user.name} (${user.role})`}
              className={`w-8 h-8 rounded-full border-2 border-white ring-1 ring-inset ${user.bg} flex items-center justify-center text-[11px] font-bold shadow-sm cursor-pointer hover:scale-110 transition-transform`}
            >
              {user.initials}
            </div>
          ))}
          <div className="pl-3 text-[11px] text-slate-600 font-semibold">
            4 Leads Active
          </div>
        </div>
      </div>

      {/* Pending Approvals Callout */}
      <div className="bg-gradient-to-br from-amber-50/80 via-white to-amber-50/30 rounded-2xl border border-amber-200/80 p-4 shadow-soft space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Review Queue</span>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 ring-1 ring-amber-300">
            {pendingCount} Pending
          </span>
        </div>
        <div className="text-xs font-bold text-slate-900">
          Campaigns Awaiting Review
        </div>
        <p className="text-[11px] text-slate-600 leading-relaxed">
          Unapproved promotional assertions require human audit prior to Brand Passport certification.
        </p>
        <Link
          href="/approval-hub"
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:underline pt-1"
        >
          <span>Open Approval Hub</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Live Agent Telemetry Stream */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-soft space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <Bot className="w-4 h-4 text-indigo-600" />
            <span className="text-xs font-bold text-slate-900">Agent Telemetry</span>
          </div>
          <Link href="/agent-control" className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800">
            View All →
          </Link>
        </div>

        <div className="space-y-2">
          {runs.length === 0 ? (
            <div className="py-4 text-center text-xs text-slate-400">
              Agents standby...
            </div>
          ) : (
            runs.map((run) => (
              <div
                key={run.id}
                className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-100 flex items-center justify-between text-xs transition-colors hover:border-indigo-200 hover:bg-white"
              >
                <div className="space-y-0.5 truncate pr-2">
                  <div className="font-semibold text-slate-800 text-[11px] truncate flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                    <span>{run.agent_name}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">
                    {run.task_name}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-200 font-semibold font-mono">
                    {run.execution_time_ms}ms
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent Brand Passport Certifications */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-soft space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <Award className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-slate-900">Recent Passports</span>
          </div>
          <Link href="/brand-passport" className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800">
            Registry →
          </Link>
        </div>

        <div className="space-y-2">
          {passports.length === 0 ? (
            <div className="py-3 text-center text-xs text-slate-400">
              No passports certified yet.
            </div>
          ) : (
            passports.map((p) => (
              <div
                key={p.id}
                className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-100 space-y-1 hover:border-emerald-200 hover:bg-white transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-800">{p.passport_number}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                    {p.verification_status}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 truncate">{p.content_title}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Bottom Brand Governance Tip Card */}
      <div className="bg-gradient-to-br from-indigo-50/90 via-white to-purple-50/60 rounded-2xl border border-indigo-100 p-3.5 shadow-soft flex items-center justify-between space-x-3">
        <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 ring-1 ring-inset ring-indigo-200 flex items-center justify-center shrink-0">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-bold text-slate-900 truncate">Governance Protocol</div>
          <div className="text-[11px] text-slate-500 truncate">Launch price LP-41 enforced</div>
        </div>
        <Link href="/brand-dna" className="text-indigo-600 hover:text-indigo-800 hover:translate-x-0.5 transition-transform">
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </aside>
  );
}

