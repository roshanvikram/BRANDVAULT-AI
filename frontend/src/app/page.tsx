"use client";

import Link from "next/link";
import {
  ArrowRight,
  Dna,
  FileSearch,
  BadgeCheck,
  Image as ImageIcon,
  Bot,
  ClipboardCheck,
  Award,
  Radar,
  ShieldCheck,
  Lock,
  Users,
  TrendingDown,
  Check,
  X,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { HeroSculpture } from "@/components/home/HeroSculpture";
import { FeatureBento } from "@/components/home/FeatureBento";

const NAV = [
  { label: "Platform", href: "#platform" },
  { label: "Workflow", href: "#workflow" },
  { label: "Security", href: "#security" },
  { label: "How it works", href: "/guide" },
];

const FEATURES = [
  { icon: Dna, title: "Brand DNA Studio", desc: "Turn guidelines, approved facts and terminology into structured brand knowledge." },
  { icon: FileSearch, title: "Content Intelligence", desc: "Audit copy against your Brand DNA with evidence behind every finding." },
  { icon: BadgeCheck, title: "ClaimDNA", desc: "Classify claims as supported, unsupported, contradicted or outdated." },
  { icon: ImageIcon, title: "Visual DNA", desc: "Measure colour palette and contrast of creatives against your brand." },
  { icon: ClipboardCheck, title: "Approval Hub", desc: "Role-gated human review. AI recommends, people decide." },
  { icon: Award, title: "Brand Passport", desc: "A SHA-256 fingerprinted record for every approved version." },
  { icon: Radar, title: "Risk Radar", desc: "Explained risk indicators computed from your real review history." },
  { icon: Bot, title: "Agent Control", desc: "Every analysis agent run is persisted, timed and inspectable." },
];

const WORKFLOW = ["Brand DNA", "Submit content", "AI analysis", "Evidence retrieval", "ClaimDNA", "Human approval", "Brand Passport"];

const TRUST = [
  { icon: Lock, title: "Tenant isolation", desc: "Every request is scoped to your organisation from the signed-in identity." },
  { icon: Users, title: "Human approval", desc: "Only Reviewers and Administrators can approve. AI agents cannot." },
  { icon: ShieldCheck, title: "Version-locked records", desc: "Any edit after approval creates a new version that must be re-approved." },
];

/* ---------------- floating cards (NOVA TECH sample audit) ---------------- */
function FloatCard({ className, children }: { className: string; children: React.ReactNode }) {
  return (
    <div
      className={`absolute bg-white/95 backdrop-blur-md rounded-2xl p-4 bv-float border transition-all ${className}`}
    >
      {children}
    </div>
  );
}

function SampleCards() {
  return (
    <>
      {/* Price check */}
      <FloatCard className="hidden md:block left-[2%] lg:left-[5%] top-[6%] w-[240px] -rotate-[4deg] border-rose-200/90 shadow-[0_20px_45px_-12px_rgba(244,63,94,0.18)]">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Price Verification</span>
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
        </div>
        <div className="mt-2.5 flex items-baseline justify-between">
          <span className="text-xl font-bold tabular-nums text-slate-900">₹69,999</span>
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
            <X className="w-3 h-3 text-rose-600" /> Contradicted
          </span>
        </div>
        <div className="text-[11px] text-slate-500">in submitted promotional copy</div>
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-baseline justify-between">
          <span className="text-xl font-bold tabular-nums text-slate-900">₹79,999</span>
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Check className="w-3 h-3 text-emerald-600" /> Approved
          </span>
        </div>
        <div className="text-[11px] text-emerald-700 font-medium">official launch price (LP-41)</div>
      </FloatCard>

      {/* Claim verification */}
      <FloatCard className="hidden md:block right-[2%] lg:right-[5%] top-[4%] w-[250px] rotate-[3deg] [animation-delay:1.2s] border-indigo-200/90 shadow-[0_20px_45px_-12px_rgba(99,102,241,0.22)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-indigo-500" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700">ClaimDNA Engine</span>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">3 claims</span>
        </div>
        <ul className="mt-3 space-y-2 text-[12px]">
          {[
            ["“world’s fastest”", "Unsupported", "bg-sky-50 text-sky-700 border-sky-200"],
            ["“10x faster”", "Unsupported", "bg-sky-50 text-sky-700 border-sky-200"],
            ["“₹69,999”", "Contradicted", "bg-rose-50 text-rose-700 border-rose-200"],
          ].map(([claim, status, colorCls]) => (
            <li key={claim} className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-slate-50/70">
              <span className="truncate text-slate-700 font-medium text-xs">{claim}</span>
              <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full border ${colorCls}`}>{status}</span>
            </li>
          ))}
        </ul>
      </FloatCard>

      {/* Score */}
      <FloatCard className="hidden lg:block left-[2%] bottom-[12%] w-[190px] rotate-[5deg] [animation-delay:0.6s] border-amber-200/90 shadow-[0_20px_45px_-12px_rgba(245,158,11,0.2)]">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Brand Health</span>
          <span className="px-1.5 py-0.5 rounded-md bg-rose-50 text-rose-700 text-[10px] font-bold">Audit</span>
        </div>
        <div className="mt-2 flex items-baseline gap-1">
          <span className="text-3xl font-bold tracking-tight text-rose-600">5</span>
          <span className="text-sm font-semibold text-slate-400">/100</span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-slate-100 overflow-hidden">
          <div className="h-full w-[8%] bg-rose-500 rounded-full" />
        </div>
        <div className="mt-2.5 inline-flex items-center gap-1.5 text-[11px] text-rose-700 font-medium">
          <TrendingDown className="w-3.5 h-3.5 text-rose-500" /> 6 critical findings to fix
        </div>
      </FloatCard>

      {/* Passport */}
      <FloatCard className="hidden lg:block right-[2%] bottom-[10%] w-[230px] -rotate-[6deg] [animation-delay:1.8s] border-emerald-200/90 shadow-[0_20px_45px_-12px_rgba(16,185,129,0.2)]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white flex items-center justify-center shadow-md shadow-emerald-500/20">
            <Award className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[13px] font-bold text-slate-900">Brand Passport</div>
            <div className="text-[10px] font-semibold text-emerald-700">Verified Cryptographic Seal</div>
          </div>
        </div>
        <div className="mt-3 p-2 rounded-lg bg-emerald-50/70 border border-emerald-100 text-[11px] text-slate-700 leading-snug">
          SHA-256 fingerprint certified by Human Reviewer.
        </div>
      </FloatCard>
    </>
  );
}

export default function Home() {
  const { user, loading } = useAuth();
  const primaryHref = user ? "/dashboard" : "/signup";

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900">
      <style>{`
        .bv-float { animation: bv-float-y 6s ease-in-out infinite; }
        @keyframes bv-float-y { 0%,100% { translate: 0 0; } 50% { translate: 0 -10px; } }
      `}</style>

      {/* ============================== HERO ============================== */}
      <div className="p-3 sm:p-4">
        <section className="relative overflow-hidden rounded-[32px] bg-white border border-slate-200/80 shadow-soft">
          {/* Ambient Colorful Background Glow Orbs */}
          <div aria-hidden className="pointer-events-none absolute -top-40 -left-40 w-96 h-96 rounded-full bg-gradient-to-br from-indigo-200/50 via-purple-200/30 to-transparent blur-3xl" />
          <div aria-hidden className="pointer-events-none absolute -top-20 -right-40 w-96 h-96 rounded-full bg-gradient-to-bl from-pink-200/50 via-purple-200/30 to-transparent blur-3xl" />
          <div aria-hidden className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-cyan-100/40 via-emerald-100/30 to-indigo-100/40 blur-3xl" />

          {/* Nav */}
          <nav className="relative z-20 max-w-6xl mx-auto px-5 sm:px-8 h-20 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 text-white flex items-center justify-center text-xs font-bold shadow-md shadow-indigo-500/25">
                BV
              </div>
              <span className="text-[18px] font-bold tracking-tight text-slate-900">BrandVault AI</span>
            </Link>
            <div className="hidden md:flex items-center gap-8 text-[14px] text-slate-600 font-medium">
              {NAV.map((n) => (
                <Link key={n.label} href={n.href} className="hover:text-indigo-600 transition-colors">
                  {n.label}
                </Link>
              ))}
            </div>
            <div className="flex items-center gap-2.5 min-h-[40px]">
              {!loading &&
                (user ? (
                  <Link href="/dashboard" className="h-10 px-5 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white text-[14px] font-semibold shadow-md shadow-indigo-500/25 transition-all">
                    Open dashboard <ArrowRight className="w-4 h-4" />
                  </Link>
                ) : (
                  <>
                    <Link href="/login" className="h-10 px-5 inline-flex items-center rounded-full border border-slate-300 text-slate-700 text-[14px] font-medium hover:bg-slate-50 transition-colors">
                      Log in
                    </Link>
                    <Link href="/signup" className="h-10 px-5 inline-flex items-center rounded-full bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white text-[14px] font-semibold shadow-md shadow-indigo-500/25 transition-all">
                      Sign up
                    </Link>
                  </>
                ))}
            </div>
          </nav>

          {/* Headline */}
          <div className="relative z-20 max-w-4xl mx-auto px-5 text-center pt-8 sm:pt-12">
            <div className="inline-flex items-center gap-2 h-8 px-3.5 rounded-full border border-indigo-200 bg-indigo-50/70 text-[12px] font-semibold text-indigo-700 shadow-sm">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
              Protect every word. Preserve every identity.
            </div>
            <h1 className="mt-5 text-[38px] leading-[1.08] sm:text-6xl lg:text-[72px] font-extrabold tracking-[-0.035em] text-slate-900">
              Brand intelligence for{" "}
              <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                modern enterprises
              </span>
            </h1>
            <p className="mt-5 text-[15px] sm:text-[17px] leading-relaxed text-slate-600 max-w-2xl mx-auto font-normal">
              BrandVault AI checks every campaign against your approved Brand DNA, explains each issue with evidence,
              and routes the final decision to an authorised human reviewer.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
              <Link href={primaryHref} className="h-12 px-7 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-700 hover:from-indigo-700 hover:to-purple-800 text-white text-[15px] font-semibold transition-all shadow-lg shadow-indigo-500/30 active:scale-[0.99]">
                {user ? "Open dashboard" : "Get started"} <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/guide" className="h-12 px-7 inline-flex items-center rounded-full border border-slate-300 text-slate-700 text-[15px] font-semibold hover:bg-slate-50 hover:border-indigo-300 transition-colors">
                See how it works
              </Link>
            </div>
          </div>

          {/* Visual Container: Full, Unclipped Flower with Orbit Rings */}
          <div className="relative mt-8 sm:mt-10 h-[520px] sm:h-[660px] lg:h-[760px] flex items-center justify-center overflow-visible">
            {/* Colorful Orbit Rings */}
            <svg aria-hidden viewBox="0 0 1200 640" preserveAspectRatio="none" className="absolute inset-0 w-full h-full pointer-events-none">
              <ellipse cx="600" cy="320" rx="540" ry="210" fill="none" stroke="rgba(99, 102, 241, 0.22)" strokeWidth="1.5" />
              <ellipse cx="600" cy="340" rx="620" ry="260" fill="none" stroke="rgba(168, 85, 247, 0.35)" strokeWidth="1.8" strokeDasharray="3 9" strokeLinecap="round" />
              <ellipse cx="600" cy="300" rx="460" ry="170" fill="none" stroke="rgba(6, 182, 212, 0.25)" strokeWidth="1.2" transform="rotate(-6 600 300)" />
              {/* Colorful orbital glow nodes */}
              <circle cx="180" cy="240" r="4.5" fill="#6366F1" />
              <circle cx="1020" cy="390" r="4.5" fill="#EC4899" />
              <circle cx="850" cy="180" r="4" fill="#06B6D4" />
              <circle cx="340" cy="460" r="4" fill="#10B981" />
            </svg>

            {/* FULL, Centered, Rich Chromatic Flower Sculpture */}
            <div className="relative z-10 w-[540px] sm:w-[720px] lg:w-[820px] h-[500px] sm:h-[640px] lg:h-[720px] flex items-center justify-center">
              <HeroSculpture className="w-full h-full" />
            </div>

            {/* Floating Context Cards */}
            <SampleCards />
          </div>
        </section>

        <p className="mt-3.5 text-center text-[12px] text-slate-500 font-medium">
          Cards show the NOVA TECH sample campaign audit included with the demo workspace.
        </p>
      </div>

      {/* ============================ WORKFLOW ============================ */}
      <section id="workflow" className="max-w-6xl mx-auto px-5 sm:px-8 pt-20 sm:pt-28">
        <div className="max-w-2xl">
          <div className="inline-block px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[11px] font-bold uppercase tracking-wider border border-indigo-200">
            Workflow Engine
          </div>
          <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-[-0.03em] text-slate-900">
            From guideline to certified campaign
          </h2>
          <p className="mt-3 text-[15px] text-slate-600 leading-relaxed font-normal">
            One governed path for every piece of content, with evidence at each step and an authorized human signing off at the end.
          </p>
        </div>

        <ol className="mt-10 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3.5">
          {WORKFLOW.map((step, i) => (
            <li key={step} className="rounded-2xl bg-white border border-slate-200/80 p-4 shadow-soft hover:border-indigo-300 transition-all group">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center justify-center text-xs font-bold tabular-nums group-hover:scale-105 transition-transform">
                {String(i + 1).padStart(2, "0")}
              </div>
              <div className="mt-5 text-[14px] font-bold text-slate-900 leading-snug">{step}</div>
            </li>
          ))}
        </ol>
      </section>

      {/* ============================ PLATFORM ============================ */}
      <section id="platform" className="max-w-6xl mx-auto px-5 sm:px-8 pt-20 sm:pt-28">
        <div className="max-w-2xl">
          <div className="inline-block px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-[11px] font-bold uppercase tracking-wider border border-purple-200">
            Governance Platform
          </div>
          <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-[-0.03em] text-slate-900">
            One workspace for brand governance
          </h2>
          <p className="mt-3 text-[15px] text-slate-600 leading-relaxed font-normal">
            Deterministic checks first, AI where it helps, and a person signs off on every decision.
          </p>
        </div>

        <FeatureBento />
      </section>

      {/* ============================ SECURITY ============================ */}
      <section id="security" className="max-w-6xl mx-auto px-5 sm:px-8 pt-20 sm:pt-28">
        <div className="rounded-[32px] bg-gradient-to-br from-indigo-50/70 via-white to-purple-50/50 border border-indigo-100 shadow-soft p-8 sm:p-12">
          <div className="max-w-2xl">
            <div className="inline-block px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold uppercase tracking-wider border border-emerald-200">
              Security & Isolation
            </div>
            <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-[-0.03em] text-slate-900">
              Built so AI never has the final word
            </h2>
          </div>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { icon: Lock, title: "Tenant Isolation", desc: "Every request is scoped to your organisation from the signed-in identity. Zero data leakage across workspaces.", color: "bg-indigo-100 text-indigo-700" },
              { icon: Users, title: "Human-in-the-Loop Approval", desc: "Only Reviewers and Administrators can approve. AI agents suggest and flag, but humans certify.", color: "bg-emerald-100 text-emerald-700" },
              { icon: ShieldCheck, title: "Version-Locked Records", desc: "Any edit after approval creates a new version that must be re-approved. Full cryptographic lineage.", color: "bg-purple-100 text-purple-700" },
            ].map((t) => {
              const Icon = t.icon;
              return (
                <div key={t.title} className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-soft">
                  <div className={`w-10 h-10 rounded-xl ${t.color} flex items-center justify-center mb-4`}>
                    <Icon className="w-5 h-5" strokeWidth={2} />
                  </div>
                  <div className="text-[15px] font-bold text-slate-900">{t.title}</div>
                  <div className="mt-1.5 text-[13px] text-slate-600 leading-relaxed">{t.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =============================== CTA =============================== */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 py-20 sm:py-28 text-center">
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-[-0.035em] text-slate-900">
          Ready to govern your brand?
        </h2>
        <p className="mt-4 text-[15px] text-slate-600 max-w-lg mx-auto">
          Sign in with a demo account to run the full workflow: analyse, correct, approve and issue a Brand Passport.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
          <Link href={user ? "/dashboard" : "/login"} className="h-12 px-7 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-700 hover:from-indigo-700 hover:to-purple-800 text-white text-[15px] font-semibold transition-all shadow-lg shadow-indigo-500/25 active:scale-[0.99]">
            {user ? "Open dashboard" : "Log in"} <ArrowRight className="w-4 h-4" />
          </Link>
          {!user && (
            <Link href="/signup" className="h-12 px-7 inline-flex items-center rounded-full border border-slate-300 text-slate-800 text-[15px] font-semibold hover:bg-white hover:border-indigo-300 transition-colors">
              Create account
            </Link>
          )}
        </div>
      </section>

      {/* ============================== FOOTER ============================= */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-[13px] text-slate-500">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-700 text-white flex items-center justify-center text-xs font-bold">
              BV
            </div>
            <span className="text-slate-900 font-bold">BrandVault AI</span>
          </div>
          <span className="font-medium">Team BrandVault AI · CodeNexus India 2026</span>
        </div>
      </footer>
    </div>
  );
}
