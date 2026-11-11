"use client";

import { useMemo } from "react";

/**
 * Full Radiant Chromatic Dahlia Sculpture for BrandVault AI.
 * Arranged on a phyllotaxis golden-angle spiral with a rich, vibrant chromatic
 * spectrum (electric indigo, radiant violet, vivid fuchsia, ruby rose, golden amber,
 * emerald jade, aqua teal, and bright cyan) plus a luminous warm golden core.
 * Scalable vector graphics with clean drop shadows and crisp white rim contours.
 */
const GOLDEN_ANGLE = 137.508;
const PETALS = 280;

const f = (n: number) => n.toFixed(1);

/** Smooth contoured teardrop petal */
function petalPath(w: number, len: number): string {
  return (
    `M0 0 C ${f(w * 0.95)} ${f(-len * 0.26)} ${f(w * 0.42)} ${f(-len * 0.90)} 0 ${f(-len)} ` +
    `C ${f(-w * 0.42)} ${f(-len * 0.90)} ${f(-w * 0.95)} ${f(-len * 0.26)} 0 0 Z`
  );
}

const GRAD_IDS = [
  "bv-petal-indigo",
  "bv-petal-violet",
  "bv-petal-fuchsia",
  "bv-petal-rose",
  "bv-petal-amber",
  "bv-petal-emerald",
  "bv-petal-teal",
  "bv-petal-cyan",
];

export function HeroSculpture({ className }: { className?: string }) {
  const petals = useMemo(() => {
    const out: {
      x: number;
      y: number;
      rot: number;
      len: number;
      w: number;
      gradId: string;
      isInner: boolean;
      opacity: number;
    }[] = [];

    for (let i = PETALS; i >= 1; i--) {
      const t = i / PETALS; // 1 at outer ring, 0 at center core
      const r = 19.2 * Math.sqrt(i);
      const a = (i * GOLDEN_ANGLE * Math.PI) / 180;
      
      // Calculate angular sector (0..7) for smooth color transitions around the flower
      const deg = ((a * 180) / Math.PI + 360) % 360;
      const sector = Math.floor(deg / 45) % 8;
      const isInner = t < 0.22;

      out.push({
        x: r * Math.cos(a),
        y: r * Math.sin(a),
        rot: (i * GOLDEN_ANGLE) % 360,
        len: 38 + 155 * Math.pow(t, 0.74),
        w: 18 + 44 * Math.pow(t, 0.80),
        gradId: isInner ? "bv-petal-inner" : GRAD_IDS[sector],
        isInner,
        opacity: isInner ? 0.98 : 0.94,
      });
    }
    return out;
  }, []);

  return (
    <svg
      viewBox="-440 -440 880 880"
      className={className}
      aria-hidden
      role="presentation"
      style={{
        filter: "drop-shadow(0 20px 50px rgba(99, 102, 241, 0.35)) drop-shadow(0 8px 24px rgba(244, 63, 94, 0.20))",
      }}
    >
      <defs>
        {/* 1. Electric Indigo & Royal Sapphire */}
        <linearGradient id="bv-petal-indigo" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#1E1B4B" />
          <stop offset="35%" stopColor="#3730A3" />
          <stop offset="70%" stopColor="#4F46E5" />
          <stop offset="95%" stopColor="#818CF8" />
          <stop offset="100%" stopColor="#E0E7FF" />
        </linearGradient>

        {/* 2. Electric Violet & Lavender */}
        <linearGradient id="bv-petal-violet" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#2E1065" />
          <stop offset="35%" stopColor="#6B21A8" />
          <stop offset="70%" stopColor="#9333EA" />
          <stop offset="95%" stopColor="#C084FC" />
          <stop offset="100%" stopColor="#F3E8FF" />
        </linearGradient>

        {/* 3. Radiant Fuchsia & Magenta */}
        <linearGradient id="bv-petal-fuchsia" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#4A044E" />
          <stop offset="35%" stopColor="#86198F" />
          <stop offset="70%" stopColor="#C026D3" />
          <stop offset="95%" stopColor="#E879F9" />
          <stop offset="100%" stopColor="#FAE8FF" />
        </linearGradient>

        {/* 4. Vivid Rose & Ruby Coral */}
        <linearGradient id="bv-petal-rose" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#4C0519" />
          <stop offset="35%" stopColor="#9F1239" />
          <stop offset="70%" stopColor="#E11D48" />
          <stop offset="95%" stopColor="#FB7185" />
          <stop offset="100%" stopColor="#FFE4E6" />
        </linearGradient>

        {/* 5. Golden Amber & Sunset Copper */}
        <linearGradient id="bv-petal-amber" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#451A03" />
          <stop offset="35%" stopColor="#B45309" />
          <stop offset="70%" stopColor="#F59E0B" />
          <stop offset="95%" stopColor="#FBBF24" />
          <stop offset="100%" stopColor="#FEF3C7" />
        </linearGradient>

        {/* 6. Luminous Emerald & Jade */}
        <linearGradient id="bv-petal-emerald" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#022C22" />
          <stop offset="35%" stopColor="#065F46" />
          <stop offset="70%" stopColor="#10B981" />
          <stop offset="95%" stopColor="#34D399" />
          <stop offset="100%" stopColor="#D1FAE5" />
        </linearGradient>

        {/* 7. Radiant Teal & Aqua */}
        <linearGradient id="bv-petal-teal" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#042F2E" />
          <stop offset="35%" stopColor="#0F766E" />
          <stop offset="70%" stopColor="#14B8A6" />
          <stop offset="95%" stopColor="#2DD4BF" />
          <stop offset="100%" stopColor="#CCFBF1" />
        </linearGradient>

        {/* 8. Electric Cyan & Celestial Azure */}
        <linearGradient id="bv-petal-cyan" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#082F49" />
          <stop offset="35%" stopColor="#0369A1" />
          <stop offset="70%" stopColor="#06B6D4" />
          <stop offset="95%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#CFFAFE" />
        </linearGradient>

        {/* Inner Glowing Sun Core Petals */}
        <linearGradient id="bv-petal-inner" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#D97706" />
          <stop offset="40%" stopColor="#F59E0B" />
          <stop offset="75%" stopColor="#FDE047" />
          <stop offset="100%" stopColor="#FFFFFF" />
        </linearGradient>

        {/* Core Glowing Sun Orb */}
        <radialGradient id="bv-core-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="30%" stopColor="#FEF08A" />
          <stop offset="70%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#B45309" />
        </radialGradient>

        {/* Outer Iridescent Ambient Halo */}
        <radialGradient id="bv-halo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#818CF8" stopOpacity="0.32" />
          <stop offset="35%" stopColor="#C084FC" stopOpacity="0.22" />
          <stop offset="65%" stopColor="#F472B6" stopOpacity="0.16" />
          <stop offset="85%" stopColor="#38BDF8" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Atmospheric iridescent ambient halo behind flower */}
      <circle r="425" fill="url(#bv-halo)" />

      {/* Full flower rosette with balanced perspective */}
      <g transform="scale(1 0.86) rotate(-2)">
        <g>
          {petals.map((p, i) => (
            <path
              key={i}
              transform={`translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) rotate(${(p.rot + 90).toFixed(1)})`}
              d={petalPath(p.w, p.len)}
              fill={`url(#${p.gradId})`}
              stroke="rgba(255, 255, 255, 0.85)"
              strokeWidth={p.isInner ? 0.9 : 1.25}
              strokeLinejoin="round"
              opacity={p.opacity}
            />
          ))}
        </g>

        {/* Radiant Golden Center Core */}
        <circle r="30" fill="url(#bv-core-glow)" stroke="#FFFFFF" strokeWidth="3" />
        <circle r="14" fill="#FFFFFF" opacity="0.95" />
        <circle r="6" fill="#FEF08A" />
      </g>
    </svg>
  );
}
