/**
 * Soft abstract artwork behind the app (frosted-glass look): a warm amber glow,
 * sweeping navy and sky-blue ribbons and a green haze. The whole layer is blurred
 * with CSS (smooth edges at any size) and sits under a light veil so text on the
 * glass cards stays readable. Pure SVG/CSS — no image download.
 */
export function Backdrop() {
  return (
    <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden bg-[#EDEFF3]">
      <svg className="absolute -inset-[12%] w-[124%] h-[124%] [filter:blur(44px)_saturate(1.2)]"
           viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="bv-amber" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#FEF3C7" /><stop offset="45%" stopColor="#FBBF24" /><stop offset="100%" stopColor="#FB923C" />
          </linearGradient>
          <linearGradient id="bv-navy" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1E3A8A" /><stop offset="55%" stopColor="#0F172A" /><stop offset="100%" stopColor="#312E81" />
          </linearGradient>
          <linearGradient id="bv-sky" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#E0F2FE" /><stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
        </defs>
        <ellipse cx="330" cy="430" rx="330" ry="270" fill="url(#bv-amber)" opacity="0.9" />
        <ellipse cx="1430" cy="880" rx="330" ry="210" fill="#86EFAC" opacity="0.65" />
        <ellipse cx="1500" cy="640" rx="170" ry="150" fill="#FDE68A" opacity="0.6" />
        <path d="M 420 -120 C 580 260, 290 560, 540 1120" stroke="url(#bv-navy)" strokeWidth="110" fill="none" strokeLinecap="round" opacity="0.75" />
        <path d="M 1000 -140 C 830 250, 1200 540, 990 1120" stroke="url(#bv-navy)" strokeWidth="70" fill="none" strokeLinecap="round" opacity="0.5" />
        <path d="M 1200 -80 C 1070 310, 1440 580, 1270 1080" stroke="url(#bv-sky)" strokeWidth="150" fill="none" strokeLinecap="round" opacity="0.7" />
        <path d="M 660 -120 C 780 300, 580 640, 790 1120" stroke="#FFFFFF" strokeWidth="70" fill="none" strokeLinecap="round" opacity="0.85" />
      </svg>
      {/* light veil keeps contrast high for text on glass */}
      <div className="absolute inset-0 bg-white/15" />
    </div>
  );
}
