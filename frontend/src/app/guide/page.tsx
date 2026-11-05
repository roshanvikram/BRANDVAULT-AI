"use client";

import { ReactNode } from "react";
import Link from "next/link";
import {
  ArrowRight, ArrowLeft, ShieldCheck, UserPlus, Dna, FileSearch,
  CheckCircle2, Image as ImageIcon, UserCheck, Award, Mic, ImagePlus, PlayCircle,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { ReadAloud } from "@/components/guide/ReadAloud";
import { WalkthroughPlayer } from "@/components/guide/WalkthroughPlayer";

// The recorded walkthrough video. Defaults to the bundled screen recording in
// public/demo; override with NEXT_PUBLIC_GUIDE_VIDEO_URL (a video file URL or an
// embeddable YouTube/Vimeo URL). Set it to "none" to fall back to the built-in
// animated screenshot reel instead.
const VIDEO_ENV = process.env.NEXT_PUBLIC_GUIDE_VIDEO_URL;
const VIDEO_URL = VIDEO_ENV === "none" ? "" : (VIDEO_ENV || "/demo/walkthrough.mp4");

function VideoEmbed({ url }: { url: string }) {
  const isFile = /\.(mp4|webm|ogg)(\?.*)?$/i.test(url);
  return (
    <div className="rounded-2xl overflow-hidden border border-[#E5E5E5] bg-black aspect-video shadow-sm">
      {isFile ? (
        <video
          src={url}
          controls
          playsInline
          preload="metadata"
          poster="/demo/03-content-intelligence.jpg"
          className="w-full h-full object-contain bg-black"
        />
      ) : (
        <iframe
          src={url}
          title="BRANDVAULT AI walkthrough"
          className="w-full h-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      )}
    </div>
  );
}

/* ------------------------------- illustrations ---------------------------- */
const F = "#F5F5F5", B = "#0A0A0A", G = "#737373", E = "#E5E5E5";

function IllAccount() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <rect x="40" y="18" width="120" height="104" rx="10" fill="white" stroke={E} />
      <circle cx="100" cy="44" r="12" fill={F} stroke={E} /><circle cx="100" cy="40" r="4" fill={G} /><path d="M92 50a8 8 0 0116 0" fill={G} />
      <rect x="60" y="66" width="80" height="10" rx="3" fill={F} stroke={E} />
      <rect x="60" y="82" width="80" height="10" rx="3" fill={F} stroke={E} />
      <rect x="60" y="100" width="80" height="12" rx="4" fill={B} />
    </svg>
  );
}
function IllBrandDNA() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <rect x="34" y="18" width="132" height="104" rx="10" fill="white" stroke={E} />
      <rect x="50" y="34" width="60" height="9" rx="3" fill={B} />
      {[58, 74, 90].map((y) => (<g key={y}><rect x="50" y={y} width="86" height="8" rx="3" fill={F} stroke={E} /></g>))}
      <circle cx="150" cy="34" r="3" fill={G} /><circle cx="150" cy="62" r="3" fill={G} /><circle cx="150" cy="90" r="3" fill={G} />
      <circle cx="128" cy="106" r="10" fill={B} /><path d="M123 106l3 3 6-6" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function IllContent() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <rect x="34" y="18" width="132" height="104" rx="10" fill="white" stroke={E} />
      <rect x="50" y="34" width="100" height="8" rx="3" fill={F} stroke={E} />
      <rect x="50" y="50" width="100" height="8" rx="3" fill={B} opacity="0.12" />
      <rect x="50" y="50" width="54" height="8" rx="3" fill="none" stroke={B} strokeDasharray="3 2" />
      <rect x="50" y="66" width="100" height="8" rx="3" fill={F} stroke={E} />
      <rect x="50" y="82" width="70" height="8" rx="3" fill={F} stroke={E} />
      <g transform="translate(120 96)"><rect width="34" height="16" rx="5" fill={B} /><path d="M7 8h20M7 8l3-3M7 8l3 3" stroke="white" strokeWidth="1.4" fill="none" strokeLinecap="round" /></g>
    </svg>
  );
}
function IllClaim() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <rect x="30" y="22" width="140" height="96" rx="10" fill="white" stroke={E} />
      {[{ y: 36, t: "SUPPORTED", fill: B, tx: "white" }, { y: 60, t: "UNSUPPORTED", fill: F, tx: B }, { y: 84, t: "OUTDATED", fill: F, tx: G }].map((p) => (
        <g key={p.y} transform={`translate(44 ${p.y})`}>
          <rect width="112" height="18" rx="6" fill={p.fill} stroke={E} />
          <text x="10" y="13" fontFamily="monospace" fontSize="9" fontWeight="700" fill={p.tx}>{p.t}</text>
        </g>
      ))}
    </svg>
  );
}
function IllVisual() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <rect x="34" y="20" width="132" height="76" rx="8" fill={F} stroke={E} />
      <circle cx="60" cy="44" r="8" fill="white" stroke={E} /><path d="M44 86l24-24 16 14 20-18 18 16v12H44z" fill="white" stroke={E} />
      {["#0A0A0A", "#737373", "#A3A3A3", "#E5E5E5"].map((c, i) => (<rect key={i} x={48 + i * 24} y={104} width="18" height="18" rx="4" fill={c} stroke={E} />))}
      <rect x="140" y="104" width="22" height="18" rx="4" fill="white" stroke={E} /><text x="151" y="117" fontFamily="monospace" fontSize="8" fontWeight="700" fill={B} textAnchor="middle">AA</text>
    </svg>
  );
}
function IllApproval() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <path d="M100 20l40 14v30c0 28-20 42-40 50-20-8-40-22-40-50V34z" fill="white" stroke={E} />
      <path d="M84 68l12 12 24-26" stroke={B} strokeWidth="4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="150" cy="96" r="14" fill={F} stroke={E} /><circle cx="150" cy="91" r="4.5" fill={G} /><path d="M141 104a9 9 0 0118 0" fill={G} />
    </svg>
  );
}
function IllPassport() {
  return (
    <svg viewBox="0 0 200 140" className="w-full h-full">
      <rect x="40" y="22" width="120" height="96" rx="10" fill="white" stroke={E} />
      <rect x="40" y="22" width="120" height="22" rx="10" fill={B} /><text x="100" y="37" fontFamily="monospace" fontSize="9" fontWeight="700" fill="white" textAnchor="middle">BRAND PASSPORT</text>
      <circle cx="66" cy="70" r="14" fill={F} stroke={E} /><path d="M60 70l4 4 8-9" stroke={B} strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="90" y="60" width="58" height="7" rx="3" fill={F} stroke={E} /><rect x="90" y="74" width="58" height="7" rx="3" fill={F} stroke={E} />
      <text x="50" y="106" fontFamily="monospace" fontSize="7" fill={G}>SHA-256 · a3f9…b1c7</text>
    </svg>
  );
}

/* --------------------------------- steps ---------------------------------- */
type Step = { n: number; icon: any; title: string; summary: string; actions: string[]; ill: ReactNode; shot?: string };

const STEPS: Step[] = [
  {
    n: 1, icon: UserPlus, title: "Create your account or sign in",
    summary: "Open the app and either create an account or use a demo account. New sign-ups join as a Creator, who can submit content for review. Reviewer and Administrator roles — the only roles that can approve content — are granted by an administrator.",
    actions: ["Click Create account, or use a demo button on the sign-in page.", "You can also continue with Google once it is configured on the server."],
    ill: <IllAccount />, shot: "/demo/01-signin.jpg",
  },
  {
    n: 2, icon: Dna, title: "Set up your Brand DNA",
    summary: "Go to Brand DNA Studio. This is your source of truth: the approved rules, verified facts, and prohibited-versus-preferred terminology the system checks every piece of content against. Review the extracted rules and confirm them before they become active.",
    actions: ["Upload a brand guideline PDF or text file, or use the seeded NOVA TECH example.", "Confirm each extracted rule so it is active during analysis."],
    ill: <IllBrandDNA />, shot: "/demo/02-brand-dna.jpg",
  },
  {
    n: 3, icon: FileSearch, title: "Analyse content in Content Intelligence",
    summary: "Paste your marketing copy and run the analysis. The engine flags unsupported claims, pricing conflicts, tone drift, and prohibited terms — each finding comes with the retrieved evidence passage and a suggested correction you can apply.",
    actions: ["Paste copy and click analyse.", "Review each finding's evidence, then apply a suggested correction to re-score."],
    ill: <IllContent />, shot: "/demo/03-content-intelligence.jpg",
  },
  {
    n: 4, icon: CheckCircle2, title: "Verify claims with ClaimDNA",
    summary: "Every factual claim is checked against your approved facts and classified as Supported, Unsupported, Contradicted, Outdated, or Needs Human Review. Nothing is invented: a claim with no matching evidence is marked unsupported rather than guessed.",
    actions: ["Open ClaimDNA to see each claim's status and the fact it was checked against."],
    ill: <IllClaim />, shot: "/demo/04-claim-dna.jpg",
  },
  {
    n: 5, icon: ImageIcon, title: "Check creative assets in Visual DNA — by image",
    summary: "Upload an image of a creative asset (PNG or BMP). Visual DNA measures the real colour palette, dominant colours, and contrast directly from the pixels — a measured analysis, not a guess. Use it to check that artwork stays on-brand.",
    actions: ["Open Visual DNA and upload a PNG or BMP image.", "Read the measured colour palette and contrast metrics."],
    ill: <IllVisual />, shot: "/demo/05-visual-dna.jpg",
  },
  {
    n: 6, icon: UserCheck, title: "Get human approval in the Approval Hub",
    summary: "This is the governance gate. Only a Reviewer or Administrator can approve, reject, or request revision on a submission — the AI never approves anything on its own. A written reviewer comment is required and the decision is attributed to the signed-in reviewer.",
    actions: ["Sign in as a Reviewer or Administrator.", "Add a comment and record your decision; it is logged to the audit trail."],
    ill: <IllApproval />, shot: "/demo/06-approval-hub.jpg",
  },
  {
    n: 7, icon: Award, title: "Issue a Brand Passport",
    summary: "When content is approved, the system issues a Brand Passport: a tamper-evident certificate with a SHA-256 hash of the exact approved content, the guideline version, the final score, and who approved it. If the content changes, the hash no longer matches.",
    actions: ["Find the certificate in the Brand Passport repository.", "Share or archive it as proof the content passed governance."],
    ill: <IllPassport />, shot: "/demo/07-brand-passport.jpg",
  },
];

function buildSpeech(): string {
  const intro = "How to use BrandVault AI. A seven step governance workflow.";
  const body = STEPS.map((s) => `Step ${s.n}. ${s.title}. ${s.summary}`).join(" ");
  return `${intro} ${body}`;
}

export default function GuidePage() {
  const { user } = useAuth();
  const dashHref = user ? "/dashboard" : "/signup";

  return (
    <div className="min-h-screen bg-[#F7F7F7] text-[#0A0A0A] select-none">
      {/* Top bar */}
      <header className="h-16 border-b border-[#E5E5E5] bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto h-full px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-8 h-8 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold text-sm tracking-wider shadow-sm group-hover:scale-105 transition-transform">BV</div>
            <div>
              <div className="font-bold text-sm tracking-tight">BRANDVAULT AI</div>
              <div className="text-[9px] text-[#737373] tracking-widest font-mono uppercase">User Guide</div>
            </div>
          </Link>
          <Link href={dashHref} className="px-4 py-2 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm">
            <span>{user ? "Open dashboard" : "Get started"}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-16 pb-10 text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-[#E5E5E5] bg-white text-[10px] font-mono uppercase tracking-wider text-[#737373] mb-6">
          <ShieldCheck className="w-3.5 h-3.5 text-[#0A0A0A]" />
          <span>Step-by-step user guide</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight leading-[1.1]">How to use BRANDVAULT AI</h1>
        <p className="text-sm text-[#737373] mt-4 max-w-2xl mx-auto leading-relaxed">
          Follow these seven steps to take a piece of marketing content from draft to a certified Brand Passport.
          Prefer to listen? Play the guide as audio with your browser&apos;s built-in voice.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-7">
          <a href="#watch" className="px-5 py-3 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm">
            <PlayCircle className="w-4 h-4" />
            <span>Watch walkthrough</span>
          </a>
          <ReadAloud text={buildSpeech()} label="Play audio guide" />
        </div>
      </section>

      {/* Watch — video / animated walkthrough */}
      <section id="watch" className="max-w-3xl mx-auto px-6 pb-14 scroll-mt-20">
        <div className="text-center mb-5">
          <div className="inline-flex items-center space-x-2 text-[10px] font-mono uppercase tracking-wider text-[#737373]">
            <PlayCircle className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span>{VIDEO_URL ? "Video walkthrough" : "Watch the product demo"}</span>
          </div>
          <p className="text-xs text-[#737373] mt-2">
            {VIDEO_URL
              ? "A recorded walkthrough of the full governance flow."
              : "A narrated demo of the real app — seven steps from draft to certified Brand Passport. Press play."}
          </p>
        </div>
        {VIDEO_URL ? <VideoEmbed url={VIDEO_URL} /> : <WalkthroughPlayer steps={STEPS} />}
      </section>

      {/* Roles */}
      <section className="max-w-5xl mx-auto px-6 pb-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { r: "Creator", d: "Submits content for review. Cannot approve." },
            { r: "Reviewer", d: "Approves, rejects, or requests revision." },
            { r: "Administrator", d: "Full access, incl. approvals & settings." },
          ].map((x) => (
            <div key={x.r} className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-5">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#A3A3A3] font-bold mb-1">Role</div>
              <div className="text-sm font-bold tracking-tight">{x.r}</div>
              <div className="text-[11px] text-[#737373] mt-1 leading-relaxed">{x.d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Steps */}
      <section className="max-w-5xl mx-auto px-6 pb-16 space-y-5">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const flip = i % 2 === 1;
          return (
            <div key={s.n} className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm overflow-hidden">
              <div className={`grid grid-cols-1 md:grid-cols-5 ${flip ? "md:[&>*:first-child]:order-2" : ""}`}>
                {/* Text */}
                <div className="md:col-span-3 p-6 sm:p-7">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-9 h-9 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold text-sm shadow-sm">{s.n}</div>
                      <div className="flex items-center space-x-2">
                        <Icon className="w-4 h-4 text-[#0A0A0A]" />
                        <h3 className="text-base font-bold tracking-tight">{s.title}</h3>
                      </div>
                    </div>
                    <ReadAloud compact text={`Step ${s.n}. ${s.title}. ${s.summary}`} />
                  </div>
                  <p className="text-xs text-[#737373] leading-relaxed">{s.summary}</p>
                  <ul className="mt-3 space-y-1.5">
                    {s.actions.map((a, j) => (
                      <li key={j} className="flex items-start space-x-2 text-xs text-[#404040]">
                        <ArrowRight className="w-3.5 h-3.5 text-[#A3A3A3] mt-0.5 shrink-0" />
                        <span>{a}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                {/* Illustration */}
                <div className="md:col-span-2 bg-[#FAFAFA] border-t md:border-t-0 md:border-l border-[#F0F0F0] p-5 flex items-center justify-center">
                  <div className="w-full max-w-[220px] aspect-[200/140]">{s.ill}</div>
                </div>
              </div>
            </div>
          );
        })}
      </section>

      {/* Voice & image callout */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-6">
            <div className="w-9 h-9 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] flex items-center justify-center mb-3"><Mic className="w-4 h-4 text-[#0A0A0A]" /></div>
            <div className="text-sm font-bold tracking-tight">Listen instead of reading</div>
            <p className="text-[11px] text-[#737373] mt-1 leading-relaxed">
              Every step has a speaker button, and the top of the page plays the whole guide. This uses your browser&apos;s
              own built-in text-to-speech voice — it works offline and sends nothing to any server.
            </p>
          </div>
          <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-6">
            <div className="w-9 h-9 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] flex items-center justify-center mb-3"><ImagePlus className="w-4 h-4 text-[#0A0A0A]" /></div>
            <div className="text-sm font-bold tracking-tight">Work by image</div>
            <p className="text-[11px] text-[#737373] mt-1 leading-relaxed">
              In Visual DNA you upload a creative asset (PNG or BMP) and get a measured colour-palette and contrast
              read-out computed directly from the pixels — a real measurement, not an estimate.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <div className="bg-[#0A0A0A] rounded-2xl p-8 sm:p-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white">Ready to try it?</h2>
          <p className="text-xs text-[#A3A3A3] mt-2 max-w-md mx-auto">Open the dashboard and run the full workflow end to end.</p>
          <div className="flex items-center justify-center gap-3 mt-6">
            <Link href={dashHref} className="inline-flex items-center space-x-2 px-5 py-3 text-xs font-mono font-bold rounded-xl bg-white text-[#0A0A0A] hover:bg-[#E5E5E5] transition-all shadow-sm">
              <span>{user ? "Open dashboard" : "Get started"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link href="/" className="inline-flex items-center space-x-2 px-5 py-3 text-xs font-mono font-bold rounded-xl bg-transparent border border-[#404040] text-white hover:bg-[#171717] transition-all">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to home</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
