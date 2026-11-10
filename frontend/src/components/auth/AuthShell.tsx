import { ReactNode } from "react";
import { BadgeCheck, ShieldCheck, Sparkles } from "lucide-react";
import { Backdrop } from "@/components/layout/Backdrop";

/**
 * Sign-in / sign-up layout: the moving glass backdrop, a glassmorphism showcase of
 * what BrandVault does (left, wide screens) and the form (right). The showcase uses
 * the NOVA TECH demo brand's real facts and is labelled as an example.
 */
export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="bv-glass-app min-h-screen relative overflow-hidden select-none">
      <Backdrop />
      <div className="relative z-10 min-h-screen grid lg:grid-cols-[1.1fr_1fr] items-center gap-10 px-6 py-10 lg:px-16 max-w-[1400px] mx-auto">
        <Showcase />
        <main className="flex justify-center">{children}</main>
      </div>
    </div>
  );
}

function Showcase() {
  return (
    <section aria-label="What BrandVault does" className="hidden lg:block relative h-[560px]">
      {/* morphing orbs behind the glass */}
      <div aria-hidden className="bv-morph absolute left-[150px] top-[230px] w-72 h-72 bg-gradient-to-br from-[#6093F6] to-[#1E3894] opacity-80" />
      <div aria-hidden className="bv-morph bv-morph-slow absolute right-6 bottom-10 w-56 h-56 bg-gradient-to-br from-[#C3C8CF] to-[#2E3135] opacity-70" />
      <div aria-hidden className="absolute left-6 bottom-24 w-20 h-20 rounded-full bg-gradient-to-br from-white to-[#C3C8CF] shadow-[0_14px_30px_-10px_rgba(34,36,39,0.4)]" />

      <div className="relative">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#1D42B8]">Brand governance, verified</p>
        <h1 className="mt-2 text-[40px] leading-[1.08] font-semibold tracking-tight text-[#222427] max-w-md">
          Protect every word.<br />Preserve every identity.
        </h1>
        <p className="mt-3 text-[14px] text-[#555A62] max-w-sm leading-relaxed">
          Every claim, price and image checked against your approved brand facts, with the evidence attached.
        </p>
      </div>

      {/* glass card: a caught price error and its fix */}
      <div className="bv-float absolute left-0 top-[275px] w-[300px] rounded-3xl bg-white/35 backdrop-blur-xl border border-white/70 shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_24px_50px_-20px_rgba(34,36,39,0.45)] p-4 -rotate-2">
        <div className="flex items-center justify-between text-[11px] font-semibold text-[#555A62]">
          <span className="uppercase tracking-wider">Price check</span>
          <span className="rounded-full bg-[#3B6FEF]/10 text-[#1D42B8] px-2 py-0.5">Contradicted</span>
        </div>
        <p className="mt-2 text-[13px] text-[#222427]">“Now only <span className="line-through decoration-[#3B6FEF] decoration-2">₹69,999</span>”</p>
        <p className="mt-1 text-[13px] font-semibold text-[#222427]">Approved price: ₹79,999</p>
        <p className="mt-2 text-[11px] text-[#727881]">Source: Pricing Policy Master Document 2026</p>
      </div>

      {/* glass card: brand passport */}
      <div className="bv-float bv-float-delay absolute right-4 top-[250px] w-[230px] rounded-3xl bg-white/40 backdrop-blur-xl border border-white/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_24px_50px_-20px_rgba(34,36,39,0.45)] p-4 rotate-3">
        <div className="flex items-center gap-2.5">
          <span className="w-10 h-10 rounded-2xl bg-gradient-to-br from-white/80 to-white/30 border border-white flex items-center justify-center text-[#1D42B8] shadow-[inset_0_1px_0_white,0_8px_18px_-8px_rgba(30,56,148,0.5)]">
            <ShieldCheck className="w-5 h-5" />
          </span>
          <div>
            <p className="text-[13px] font-semibold text-[#222427]">Brand Passport</p>
            <p className="text-[11px] text-[#727881]">Approved version, fingerprinted</p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-1.5 text-[11px] font-medium text-emerald-700">
          <BadgeCheck className="w-3.5 h-3.5" /> Verified match
        </div>
      </div>

      {/* glass chip: claims checked */}
      <div className="bv-float absolute left-[220px] bottom-6 rounded-2xl bg-white/45 backdrop-blur-xl border border-white/80 shadow-[inset_0_1px_0_white,0_18px_40px_-18px_rgba(34,36,39,0.45)] px-4 py-3 flex items-center gap-3">
        <Sparkles className="w-4 h-4 text-[#1D42B8]" />
        <div className="text-[12px] text-[#222427]">
          <span className="font-semibold">Fixed in one click:</span> “world’s fastest” → benchmark-backed wording
        </div>
      </div>

      <p className="absolute left-0 -bottom-6 text-[10px] text-[#727881]">Example from the NOVA TECH demo workspace.</p>
    </section>
  );
}
