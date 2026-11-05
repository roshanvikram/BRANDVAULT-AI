"use client";

import Link from "next/link";
import {
  ShieldCheck,
  ArrowRight,
  Dna,
  FileSearch,
  CheckCircle2,
  Image as ImageIcon,
  Bot,
  UserCheck,
  Award,
  Radar,
  LogIn,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  { icon: Dna, title: "Brand DNA Studio", desc: "Ingest guidelines, facts, and terminology into structured brand knowledge." },
  { icon: FileSearch, title: "Content Intelligence", desc: "Audit copy against approved brand DNA with evidence-backed findings." },
  { icon: CheckCircle2, title: "ClaimDNA", desc: "Verify promotional claims: supported, unsupported, contradicted, outdated." },
  { icon: ImageIcon, title: "Visual DNA", desc: "Measured colour-palette & contrast analysis of creative assets." },
  { icon: Bot, title: "Agent Control", desc: "Observe real analysis agents with persisted execution telemetry." },
  { icon: UserCheck, title: "Approval Hub", desc: "Role-gated human review — only authorised reviewers can approve." },
  { icon: Award, title: "Brand Passport", desc: "Tamper-evident SHA-256 audit record for every approved submission." },
  { icon: Radar, title: "Risk Radar", desc: "Aggregated governance analytics across your submission history." },
];

export default function Home() {
  const { user, loading } = useAuth();

  return (
    <div className="min-h-screen bg-[#F7F7F7] text-[#0A0A0A] select-none">
      {/* Top bar */}
      <header className="h-16 border-b border-[#E5E5E5] bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto h-full px-6 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold text-sm tracking-wider shadow-sm">BV</div>
            <div>
              <div className="font-bold text-sm tracking-tight">BRANDVAULT AI</div>
              <div className="text-[9px] text-[#737373] tracking-widest font-mono uppercase">AI Governance</div>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
          <Link href="/guide" className="hidden sm:inline-flex px-3 py-2 text-xs font-mono font-semibold rounded-xl text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] transition-all">
            How it works
          </Link>
          {!loading && (
            user ? (
              <Link href="/dashboard" className="px-4 py-2 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm">
                <span>Open dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/login" className="px-4 py-2 text-xs font-mono font-bold rounded-xl bg-white border border-[#E5E5E5] text-[#0A0A0A] hover:border-[#0A0A0A] hover:bg-[#F5F5F5] transition-all flex items-center space-x-2">
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign in</span>
                </Link>
                <Link href="/signup" className="px-4 py-2 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm">
                  <span>Create account</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )
          )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-[#E5E5E5] bg-white text-[10px] font-mono uppercase tracking-wider text-[#737373] mb-6">
          <ShieldCheck className="w-3.5 h-3.5 text-[#0A0A0A]" />
          <span>Agentic Brand Governance &amp; Evidence Retrieval</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1] max-w-3xl mx-auto">
          Protect Every Word.<br />Preserve Every Identity.
        </h1>
        <p className="text-sm sm:text-base text-[#737373] mt-5 max-w-2xl mx-auto leading-relaxed">
          BRANDVAULT AI audits marketing content against your organisation&apos;s approved brand DNA —
          flagging unsupported claims, pricing conflicts, tone drift, and prohibited terms with retrieved
          evidence, then routing every decision through authorised human review.
        </p>
        <div className="flex items-center justify-center gap-3 mt-8">
          <Link href={user ? "/dashboard" : "/signup"} className="px-5 py-3 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm">
            <span>{user ? "Open dashboard" : "Get started"}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <a href="#modules" className="px-5 py-3 text-xs font-mono font-bold rounded-xl bg-white border border-[#E5E5E5] text-[#0A0A0A] hover:border-[#0A0A0A] hover:bg-[#F5F5F5] transition-all">
            Explore modules
          </a>
        </div>
      </section>

      {/* Workflow strip */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <Link href="/guide" className="block bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-5 hover:border-[#A3A3A3] transition-all group">
          <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2 text-[10px] sm:text-xs font-mono text-[#404040]">
            {["Brand DNA", "Submit content", "AI analysis", "RAG evidence", "ClaimDNA", "Human approval", "Brand Passport"].map((step, i, arr) => (
              <span key={step} className="flex items-center">
                <span className="px-2.5 py-1 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5] font-semibold text-[#0A0A0A]">{step}</span>
                {i < arr.length - 1 && <ArrowRight className="w-3 h-3 mx-1 text-[#A3A3A3]" />}
              </span>
            ))}
          </div>
          <div className="text-center mt-3 text-[11px] font-mono text-[#737373] group-hover:text-[#0A0A0A] transition-colors inline-flex items-center justify-center w-full">
            See the step-by-step guide (with audio) <ArrowRight className="w-3 h-3 ml-1" />
          </div>
        </Link>
      </section>

      {/* Modules */}
      <section id="modules" className="max-w-6xl mx-auto px-6 pb-20">
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold tracking-tight">One console for brand governance</h2>
          <p className="text-xs text-[#737373] mt-1">Ten functional modules, backed by real analysis and persistent records.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-5 hover:border-[#A3A3A3] transition-all">
                <div className="w-9 h-9 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] flex items-center justify-center mb-3">
                  <Icon className="w-4 h-4 text-[#0A0A0A]" />
                </div>
                <div className="text-sm font-bold tracking-tight">{f.title}</div>
                <div className="text-[11px] text-[#737373] mt-1 leading-relaxed">{f.desc}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <div className="bg-[#0A0A0A] rounded-2xl p-8 sm:p-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white">Ready to govern your brand?</h2>
          <p className="text-xs text-[#A3A3A3] mt-2 max-w-md mx-auto">
            Sign in with a demo account to run the full workflow — analyse, correct, approve, and issue a Brand Passport.
          </p>
          <Link href={user ? "/dashboard" : "/login"} className="inline-flex items-center space-x-2 mt-6 px-5 py-3 text-xs font-mono font-bold rounded-xl bg-white text-[#0A0A0A] hover:bg-[#E5E5E5] transition-all shadow-sm">
            <span>{user ? "Open dashboard" : "Sign in"}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#E5E5E5] bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] font-mono text-[#737373]">
          <span>BRANDVAULT AI — Protect Every Word. Preserve Every Identity.</span>
          <span>Team BRANDVAULT AI · CodeNexus India 2026</span>
        </div>
      </footer>
    </div>
  );
}
