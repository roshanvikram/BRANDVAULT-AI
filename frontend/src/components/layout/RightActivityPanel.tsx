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
    <aside className="w-full xl:w-[285px] shrink-0 space-y-5 select-none">
      {/* Primary Action Button */}
      <Link
        href="/content-intelligence"
        className="w-full py-3 px-4 rounded-2xl bg-[#0A0A0A] hover:bg-[#262626] text-white font-mono text-xs font-bold tracking-wide transition-all shadow-sm flex items-center justify-center space-x-2 group"
      >
        <Sparkles className="w-4 h-4" />
        <span>NEW CONTENT REVIEW</span>
      </Link>

      {/* Governance Reviewers Card */}
      <div className="bg-white rounded-2xl border border-[#E5E5E5] p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-[#0A0A0A]">Governance Reviewers</div>
            <div className="text-[10px] text-[#737373] font-mono">Signoff authority active</div>
          </div>
          <span className="w-2 h-2 rounded-full bg-[#0A0A0A] animate-pulse" />
        </div>

        {/* Reviewer Avatars */}
        <div className="flex items-center -space-x-2 pt-1">
          {[
            { initials: "DM", name: "Deepak Mouriya M", role: "Team Leader" },
            { initials: "RV", name: "Roshan Vikram AV", role: "Lead Engineer" },
            { initials: "PR", name: "Preethish", role: "Governance Lead" },
            { initials: "AR", name: "Aishwarya R M", role: "Brand Reviewer" },
          ].map((user, i) => (
            <div
              key={i}
              title={`${user.name} (${user.role})`}
              className="w-8 h-8 rounded-full border-2 border-white bg-[#0A0A0A] text-white flex items-center justify-center text-[10px] font-mono font-bold shadow-sm cursor-pointer hover:scale-105 transition-transform"
            >
              {user.initials}
            </div>
          ))}
          <div className="pl-3 text-[10px] font-mono text-[#737373] font-semibold">
            4 Leads Active
          </div>
        </div>
      </div>

      {/* Pending Approvals Callout */}
      <div className="bg-[#F5F5F5] rounded-2xl border border-[#E5E5E5] p-4 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono font-bold uppercase text-[#737373]">Review Queue</span>
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#0A0A0A] text-white">
            {pendingCount} Pending
          </span>
        </div>
        <div className="text-xs font-bold text-[#0A0A0A]">
          Campaigns Awaiting Review
        </div>
        <p className="text-[11px] text-[#737373] leading-relaxed">
          Unapproved promotional assertions require human audit prior to Brand Passport certification.
        </p>
        <Link
          href="/approval-hub"
          className="inline-flex items-center space-x-1.5 text-xs font-mono font-bold text-[#0A0A0A] hover:underline pt-1"
        >
          <span>Open Approval Hub</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Live Agent Telemetry Stream */}
      <div className="bg-white rounded-2xl border border-[#E5E5E5] p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <Bot className="w-4 h-4 text-[#0A0A0A]" />
            <span className="text-xs font-bold text-[#0A0A0A]">Agent Telemetry</span>
          </div>
          <Link href="/agent-control" className="text-[10px] font-mono text-[#737373] hover:text-[#0A0A0A]">
            View All →
          </Link>
        </div>

        <div className="space-y-2.5">
          {runs.length === 0 ? (
            <div className="py-4 text-center text-xs text-[#737373] font-mono">
              Agents standby...
            </div>
          ) : (
            runs.map((run) => (
              <div
                key={run.id}
                className="p-2.5 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5] flex items-center justify-between text-xs transition-colors hover:border-[#A3A3A3]"
              >
                <div className="space-y-0.5 truncate pr-2">
                  <div className="font-bold text-[#0A0A0A] text-[11px] truncate">
                    {run.agent_name}
                  </div>
                  <div className="text-[10px] font-mono text-[#737373] truncate">
                    {run.task_name}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#0A0A0A] text-white font-bold">
                    {run.execution_time_ms}ms
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent Brand Passport Certifications */}
      <div className="bg-white rounded-2xl border border-[#E5E5E5] p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <Award className="w-4 h-4 text-[#0A0A0A]" />
            <span className="text-xs font-bold text-[#0A0A0A]">Recent Passports</span>
          </div>
          <Link href="/brand-passport" className="text-[10px] font-mono text-[#737373] hover:text-[#0A0A0A]">
            Registry →
          </Link>
        </div>

        <div className="space-y-2">
          {passports.length === 0 ? (
            <div className="py-3 text-center text-xs text-[#737373] font-mono">
              No passports certified yet.
            </div>
          ) : (
            passports.map((p) => (
              <div
                key={p.id}
                className="p-2.5 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5] space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-[#0A0A0A]">{p.passport_number}</span>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded border border-[#E5E5E5] bg-white text-[#0A0A0A] font-semibold">
                    {p.verification_status}
                  </span>
                </div>
                <div className="text-[11px] text-[#737373] truncate">{p.content_title}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Bottom Brand Governance Tip Card */}
      <div className="bg-[#F5F5F5] rounded-2xl border border-[#E5E5E5] p-4 shadow-sm flex items-center justify-between space-x-3">
        <div className="w-8 h-8 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center shrink-0">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="text-xs font-bold text-[#0A0A0A]">Governance Protocol</div>
          <div className="text-[10px] text-[#737373]">Launch price LP-41 enforced</div>
        </div>
        <Link href="/brand-dna" className="text-[#0A0A0A] hover:translate-x-0.5 transition-transform">
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </aside>
  );
}
