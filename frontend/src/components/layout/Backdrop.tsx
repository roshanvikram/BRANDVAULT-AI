/**
 * Soft abstract artwork behind the app (frosted-glass look) in the brand palette:
 * a signal-red glow, sweeping charcoal ribbons,
 * and moonlit-silver highlights. The whole layer is blurred with CSS (smooth edges at
 * any size) and sits under a light veil so text on the glass cards stays readable.
 * Pure SVG/CSS — no image download.
 */
export function Backdrop() {
  return (
    <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden bg-[#E4E7EB]">
      <svg className="absolute -inset-[12%] w-[124%] h-[124%] [filter:blur(46px)_saturate(1.1)]"
           viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="bv-signal" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#DBE8FE" /><stop offset="45%" stopColor="#6093F6" /><stop offset="100%" stopColor="#1D42B8" />
          </linearGradient>
          <linearGradient id="bv-charcoal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#222427" /><stop offset="50%" stopColor="#1E3375" /><stop offset="100%" stopColor="#222427" />
          </linearGradient>
          <linearGradient id="bv-moon" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#FCFCFD" /><stop offset="100%" stopColor="#C9D1DB" />
          </linearGradient>
        </defs>
        <ellipse cx="330" cy="430" rx="340" ry="280" fill="url(#bv-signal)" opacity="0.32" />
        <ellipse cx="1420" cy="860" rx="340" ry="220" fill="#B8C0CA" opacity="0.55" />
        <ellipse cx="1500" cy="620" rx="180" ry="150" fill="#DCE0E5" opacity="0.7" />
        <path d="M 420 -120 C 580 260, 290 560, 540 1120" stroke="url(#bv-charcoal)" strokeWidth="105" fill="none" strokeLinecap="round" opacity="0.7" />
        <path d="M 1000 -140 C 830 250, 1200 540, 990 1120" stroke="url(#bv-charcoal)" strokeWidth="64" fill="none" strokeLinecap="round" opacity="0.45" />
        <path d="M 1200 -80 C 1070 310, 1440 580, 1270 1080" stroke="url(#bv-moon)" strokeWidth="150" fill="none" strokeLinecap="round" opacity="0.8" />
        <path d="M 660 -120 C 780 300, 580 640, 790 1120" stroke="#FCFCFD" strokeWidth="70" fill="none" strokeLinecap="round" opacity="0.85" />
      </svg>
      {/* Soft organic shapes (morphism). Static on purpose: anything moving behind the glass
          forces every blurred panel to be redrawn each frame, which made the app lag. Radial
          gradients give the soft edge without a costly blur filter. */}
      <div className="absolute left-[6%] top-[14%] w-[38vw] h-[38vw] max-w-[600px] max-h-[600px] rounded-[46%_54%_60%_40%/50%_42%_58%_50%] bg-[radial-gradient(closest-side,rgba(96,147,246,0.32),rgba(96,147,246,0))]" />
      <div className="absolute right-[4%] top-[4%] w-[32vw] h-[32vw] max-w-[500px] max-h-[500px] rounded-[60%_40%_38%_62%/40%_60%_40%_60%] bg-[radial-gradient(closest-side,rgba(28,44,75,0.22),rgba(28,44,75,0))]" />
      <div className="absolute right-[20%] bottom-[0%] w-[34vw] h-[34vw] max-w-[520px] max-h-[520px] bg-[radial-gradient(closest-side,rgba(252,252,253,0.8),rgba(252,252,253,0))]" />
      {/* light veil keeps contrast high for text on glass */}
      <div className="absolute inset-0 bg-[#FCFCFD]/20" />
    </div>
  );
}
