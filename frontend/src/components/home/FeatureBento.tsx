import Link from "next/link";
import {
  FileSearch, Languages, PackageCheck, Award, ShieldAlert, Rocket, FlaskConical, ArrowUpRight,
  BadgeCheck, Image as ImageIcon, ScanSearch, Copy, MessageSquareWarning, LayoutGrid, UserCheck, Puzzle, Bot, Radar,
} from "lucide-react";

const TILE = "relative overflow-hidden rounded-3xl border p-6 transition-all duration-200 hover:-translate-y-0.5";

const MORE = [
  { icon: BadgeCheck, label: "ClaimDNA" },
  { icon: ImageIcon, label: "Visual DNA" },
  { icon: ScanSearch, label: "Asset Forensics" },
  { icon: Copy, label: "Similarity Detector" },
  { icon: MessageSquareWarning, label: "Reputation Early Warning" },
  { icon: LayoutGrid, label: "Consistency Heatmap" },
  { icon: UserCheck, label: "Reviewer Intelligence" },
  { icon: Puzzle, label: "Knowledge Gap Detector" },
  { icon: Radar, label: "Risk Radar" },
  { icon: Bot, label: "Agent Control" },
];

/** Landing-page feature grid. Example values are the NOVA TECH demo audit, labelled as such. */
export function FeatureBento() {
  return (
    <>
    <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:auto-rows-[minmax(190px,auto)]">
      {/* Hero tile */}
      <div className={`${TILE} lg:col-span-2 lg:row-span-2 border-indigo-900/10 bg-gradient-to-br from-indigo-950 via-indigo-900 to-violet-900 text-white p-7 flex flex-col`}>
        <div aria-hidden className="absolute -right-24 -top-24 w-80 h-80 rounded-full bg-violet-500/30 blur-3xl" />
        <div aria-hidden className="absolute -left-16 bottom-0 w-64 h-64 rounded-full bg-indigo-500/20 blur-3xl" />
        <div className="relative flex items-center gap-2 text-[12px] font-semibold text-indigo-200">
          <FileSearch className="w-4 h-4" /> Content Intelligence
        </div>
        <h3 className="relative mt-3 !text-white text-[28px] sm:text-[32px] leading-[1.1] font-semibold tracking-tight max-w-md">
          Every finding comes with the evidence behind it.
        </h3>
        <p className="relative mt-3 text-[14px] text-indigo-200/90 max-w-md leading-relaxed">
          Copy is checked against your guidelines, approved facts and terminology. Each issue cites the rule, the source page and a suggested fix.
        </p>
        <div className="relative mt-auto pt-6">
          <div className="rounded-2xl bg-white/[0.07] ring-1 ring-white/15 backdrop-blur p-4 space-y-2.5">
            <div className="flex items-center justify-between text-[11px] text-indigo-200">
              <span>Example · NOVA TECH demo campaign</span><span className="tabular-nums">score 5/100</span>
            </div>
            {[
              ["CRITICAL", "₹69,999 contradicts the approved launch price ₹79,999", "bg-rose-400/20 text-rose-200 ring-rose-300/30"],
              ["CRITICAL", "“world’s fastest” → “benchmark-leading”: unsupported superlative", "bg-rose-400/20 text-rose-200 ring-rose-300/30"],
              ["WARNING", "Multiple exclamation marks break the brand tone of voice", "bg-amber-400/20 text-amber-200 ring-amber-300/30"],
            ].map(([sev, text, cls]) => (
              <div key={text} className="flex items-start gap-2.5 text-[13px]">
                <span className={`shrink-0 mt-px text-[10px] font-semibold px-1.5 py-0.5 rounded-md ring-1 ${cls}`}>{sev}</span>
                <span className="text-white/90">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stat tile */}
      <div className={`${TILE} border-indigo-500/20 bg-gradient-to-br from-indigo-500 to-violet-600 text-white flex flex-col justify-between`}>
        <span className="w-9 h-9 rounded-xl bg-white/15 ring-1 ring-white/25 flex items-center justify-center"><Rocket className="w-4 h-4" /></span>
        <div>
          <div className="text-[44px] leading-none font-semibold tracking-tight tabular-nums">12</div>
          <div className="mt-2 text-[13px] text-indigo-100">intelligence engines, from product truth to fraud investigation</div>
        </div>
      </div>

      {/* Translation Guard */}
      <div className={`${TILE} border-slate-200/80 bg-white hover:shadow-medium flex flex-col justify-between`}>
        <span className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 ring-1 ring-sky-100 flex items-center justify-center"><Languages className="w-4 h-4" /></span>
        <div>
          <div className="text-[15px] font-semibold text-slate-900">Translation Guard</div>
          <p className="mt-1 text-[13px] text-slate-500 leading-relaxed">Catches changed numbers, prices, qualifiers and negations in translated campaigns — full checks in 9 languages.</p>
        </div>
      </div>

      {/* Product truth */}
      <div className={`${TILE} border-emerald-200/70 bg-gradient-to-br from-emerald-50 to-white hover:shadow-medium flex flex-col justify-between`}>
        <span className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center"><PackageCheck className="w-4 h-4" /></span>
        <div>
          <div className="text-[15px] font-semibold text-slate-900">Product Truth</div>
          <div className="mt-2 flex items-center gap-2 text-[13px] tabular-nums">
            <span className="line-through decoration-rose-500 text-slate-400">₹69,999</span>
            <span className="text-slate-300">→</span>
            <span className="font-semibold text-emerald-700">₹79,999 approved</span>
          </div>
          <p className="mt-1 text-[12px] text-slate-500">Prices and specs checked against source documents.</p>
        </div>
      </div>

      {/* Passport */}
      <div className={`${TILE} border-slate-200/80 bg-white hover:shadow-medium flex flex-col justify-between`}>
        <span className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 ring-1 ring-amber-100 flex items-center justify-center"><Award className="w-4 h-4" /></span>
        <div>
          <div className="text-[15px] font-semibold text-slate-900">Brand Passport</div>
          <p className="mt-1 text-[13px] text-slate-500 leading-relaxed">A SHA-256 fingerprint of the approved version. Paste any copy later to see if it was changed.</p>
        </div>
      </div>

      {/* Fraud */}
      <div className={`${TILE} lg:col-span-2 border-rose-200/70 bg-gradient-to-br from-rose-50 via-white to-white hover:shadow-medium`}>
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div className="flex-1">
            <span className="w-9 h-9 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center"><ShieldAlert className="w-4 h-4" /></span>
            <div className="mt-4 text-[15px] font-semibold text-slate-900">Brand Fraud Intelligence</div>
            <p className="mt-1 text-[13px] text-slate-500 leading-relaxed">Investigate a reported link or screenshot: look-alike domains, fake prices, OTP and card requests, logo misuse.</p>
          </div>
          <div className="sm:w-60 rounded-2xl bg-white ring-1 ring-rose-100 p-3.5 text-[12px] space-y-1.5 shadow-sm">
            <div className="font-mono text-slate-700 truncate">n0vatech-offers.shop</div>
            {["Look-alike brand domain", "Unapproved price ₹19,999", "Asks for an OTP"].map((t) => (
              <div key={t} className="flex items-center gap-1.5 text-rose-700"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" />{t}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Stress test */}
      <div className={`${TILE} border-violet-200/70 bg-gradient-to-br from-violet-50 to-white hover:shadow-medium flex flex-col justify-between`}>
        <span className="w-9 h-9 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center"><FlaskConical className="w-4 h-4" /></span>
        <div>
          <div className="text-[15px] font-semibold text-slate-900">Campaign Stress Testing</div>
          <p className="mt-1 text-[13px] text-slate-500 leading-relaxed">“What if the price drops?” See which risks appear before you change anything.</p>
        </div>
      </div>

      {/* Launch readiness */}
      <div className={`${TILE} border-slate-200/80 bg-slate-900 text-white flex flex-col justify-between`}>
        <span className="w-9 h-9 rounded-xl bg-white/10 ring-1 ring-white/15 flex items-center justify-center"><Rocket className="w-4 h-4" /></span>
        <div>
          <div className="text-[15px] font-semibold">Launch Readiness</div>
          <p className="mt-1 text-[13px] text-slate-400 leading-relaxed">12 checks before launch. AI recommends — an authorised person approves.</p>
        </div>
      </div>
    </div>

      {/* Everything else */}
      <div className="mt-4 rounded-3xl border border-slate-200/80 bg-white p-5">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="text-[13px] font-semibold text-slate-900 shrink-0">Also in the workspace</div>
          <div className="flex flex-wrap gap-2 flex-1">
            {MORE.map(({ icon: Icon, label }) => (
              <span key={label} className="inline-flex items-center gap-1.5 text-[12px] font-medium text-slate-600 bg-slate-50 ring-1 ring-slate-200/80 rounded-full px-3 py-1.5">
                <Icon className="w-3.5 h-3.5 text-slate-400" /> {label}
              </span>
            ))}
          </div>
          <Link href="/guide" className="shrink-0 inline-flex items-center gap-1 text-[13px] font-semibold text-indigo-600 hover:text-indigo-800">
            See how it works <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </>
  );
}
