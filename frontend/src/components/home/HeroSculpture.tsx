"use client";

import { useMemo } from "react";

/**
 * Geometric Brand Vault Rose / Dahlia Sculpture.
 * Arranged on a phyllotaxis golden-angle spiral with a rich,
 * iridescent chromatic palette (Indigo, Violet, Cyan, Emerald, Rose, Amber, Gold).
 * Pure scalable SVG with 360-degree chromatic spectrum and luminous core.
 */
const GOLDEN_ANGLE = 137.508;
const PETALS = 260;

const f = (n: number) => n.toFixed(1);

/** Teardrop petal pointing up from the origin, with a smooth contoured curvature. */
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
    }[] = [];

    for (let i = PETALS; i >= 1; i--) {
      const t = i / PETALS; // 1 at outer, 0 at inner
      const r = 20.5 * Math.sqrt(i);
      const a = (i * GOLDEN_ANGLE * Math.PI) / 180;
      
      // Calculate angular sector (0..7) for smooth color transitions around the flower
      const deg = ((a * 180) / Math.PI + 360) % 360;
      const sector = Math.floor(deg / 45) % 8;
      const isInner = t < 0.25;

      out.push({
        x: r * Math.cos(a),
        y: r * Math.sin(a),
        rot: (i * GOLDEN_ANGLE) % 360,
        len: 44 + 170 * Math.pow(t, 0.76),
        w: 20 + 50 * Math.pow(t, 0.82),
        gradId: isInner ? "bv-petal-inner" : GRAD_IDS[sector],
        isInner,
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
      style={{ filter: "drop-shadow(0 20px 45px rgba(99, 102, 241, 0.25))" }}
    >
      <defs>
        {/* 1. Indigo / Royal Blue */}
        <linearGradient id="bv-petal-indigo" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#312E81" />
          <stop offset="35%" stopColor="#4F46E5" />
          <stop offset="70%" stopColor="#818CF8" />
          <stop offset="100%" stopColor="#E0E7FF" />
        </linearGradient>

        {/* 2. Electric Violet */}
        <linearGradient id="bv-petal-violet" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#4C1D95" />
          <stop offset="40%" stopColor="#7C3AED" />
          <stop offset="75%" stopColor="#A855F7" />
          <stop offset="100%" stopColor="#F3E8FF" />
        </linearGradient>

        {/* 3. Radiant Fuchsia / Magenta */}
        <linearGradient id="bv-petal-fuchsia" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#701A75" />
          <stop offset="40%" stopColor="#C026D3" />
          <stop offset="75%" stopColor="#E879F9" />
          <stop offset="100%" stopColor="#FDF4FF" />
        </linearGradient>

        {/* 4. Vivid Rose / Coral */}
        <linearGradient id="bv-petal-rose" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#881337" />
          <stop offset="40%" stopColor="#E11D48" />
          <stop offset="75%" stopColor="#FB7185" />
          <stop offset="100%" stopColor="#FFE4E6" />
        </linearGradient>

        {/* 5. Golden Amber / Sunset */}
        <linearGradient id="bv-petal-amber" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#78350F" />
          <stop offset="40%" stopColor="#D97706" />
          <stop offset="75%" stopColor="#FBBF24" />
          <stop offset="100%" stopColor="#FEF3C7" />
        </linearGradient>

        {/* 6. Luminous Emerald */}
        <linearGradient id="bv-petal-emerald" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#064E3B" />
          <stop offset="40%" stopColor="#059669" />
          <stop offset="75%" stopColor="#34D399" />
          <stop offset="100%" stopColor="#D1FAE5" />
        </linearGradient>

        {/* 7. Radiant Teal */}
        <linearGradient id="bv-petal-teal" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#134E4A" />
          <stop offset="40%" stopColor="#0D9488" />
          <stop offset="75%" stopColor="#2DD4BF" />
          <stop offset="100%" stopColor="#CCFBF1" />
        </linearGradient>

        {/* 8. Electric Cyan / Azure */}
        <linearGradient id="bv-petal-cyan" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#0C4A6E" />
          <stop offset="40%" stopColor="#0284C7" />
          <stop offset="75%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#E0F2FE" />
        </linearGradient>

        {/* Inner Glowing Core Petals */}
        <linearGradient id="bv-petal-inner" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#F59E0B" />
          <stop offset="50%" stopColor="#FDE047" />
          <stop offset="100%" stopColor="#FFFFFF" />
        </linearGradient>

        {/* Core Glowing Orb */}
        <radialGradient id="bv-core-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="35%" stopColor="#FEF08A" />
          <stop offset="75%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#D97706" />
        </radialGradient>

        {/* Outer Halo */}
        <radialGradient id="bv-halo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#818CF8" stopOpacity="0.28" />
          <stop offset="50%" stopColor="#C084FC" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#67E8F9" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Atmospheric ambient halo behind flower */}
      <circle r="410" fill="url(#bv-halo)" />

      {/* Full flower rosette with isometric perspective */}
      <g transform="scale(1 0.78) rotate(-4)">
        {petals.map((p, i) => (
          <path
            key={i}
            transform={`translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) rotate(${(p.rot + 90).toFixed(1)})`}
            d={petalPath(p.w, p.len)}
            fill={`url(#${p.gradId})`}
            stroke="rgba(255, 255, 255, 0.75)"
            strokeWidth={p.isInner ? 0.75 : 1.1}
            strokeLinejoin="round"
            opacity={p.isInner ? 0.98 : 0.92}
          />
        ))}

        {/* Radiant Center Core */}
        <circle r="26" fill="url(#bv-core-glow)" stroke="#FFFFFF" strokeWidth="2.5" />
        <circle r="12" fill="#FFFFFF" opacity="0.9" />
      </g>
    </svg>
  );
}
