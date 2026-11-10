"use client";

import { useMemo } from "react";

/**
 * Geometric Brand Vault Rose / Dahlia Sculpture.
 * Arranged on a phyllotaxis golden-angle spiral in the brand palette (signal red,
 * deep red, moonlit silver, charcoal grey). Static (no animation). Pure scalable SVG.
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
      style={{ filter: "drop-shadow(0 20px 45px rgba(59,111,239, 0.25))" }}
    >
      <defs>
        {/* 1. Indigo / Royal Blue */}
        <linearGradient id="bv-petal-indigo" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#1E3375" />
          <stop offset="35%" stopColor="#2554D9" />
          <stop offset="70%" stopColor="#6093F6" />
          <stop offset="100%" stopColor="#DBE8FE" />
        </linearGradient>

        {/* 2. Electric Violet */}
        <linearGradient id="bv-petal-violet" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#151618" />
          <stop offset="40%" stopColor="#222427" />
          <stop offset="75%" stopColor="#1C2C4B" />
          <stop offset="100%" stopColor="#B8C0CA" />
        </linearGradient>

        {/* 3. Radiant Fuchsia / Magenta */}
        <linearGradient id="bv-petal-fuchsia" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#16233C" />
          <stop offset="40%" stopColor="#2E4675" />
          <stop offset="75%" stopColor="#5F7BAD" />
          <stop offset="100%" stopColor="#DDE6F2" />
        </linearGradient>

        {/* 4. Vivid Rose / Coral */}
        <linearGradient id="bv-petal-rose" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#1E3894" />
          <stop offset="40%" stopColor="#3B6FEF" />
          <stop offset="75%" stopColor="#93B8FB" />
          <stop offset="100%" stopColor="#EFF5FF" />
        </linearGradient>

        {/* 5. Golden Amber / Sunset */}
        <linearGradient id="bv-petal-amber" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#4E5560" />
          <stop offset="40%" stopColor="#9AA7B6" />
          <stop offset="75%" stopColor="#C9D1DB" />
          <stop offset="100%" stopColor="#FCFCFD" />
        </linearGradient>

        {/* 6. Luminous Emerald */}
        <linearGradient id="bv-petal-emerald" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#222427" />
          <stop offset="40%" stopColor="#2E3135" />
          <stop offset="75%" stopColor="#555A62" />
          <stop offset="100%" stopColor="#C3C8CF" />
        </linearGradient>

        {/* 7. Radiant Teal */}
        <linearGradient id="bv-petal-teal" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#1D42B8" />
          <stop offset="40%" stopColor="#6093F6" />
          <stop offset="75%" stopColor="#BFD5FD" />
          <stop offset="100%" stopColor="#FCFCFD" />
        </linearGradient>

        {/* 8. Electric Cyan / Azure */}
        <linearGradient id="bv-petal-cyan" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#151618" />
          <stop offset="40%" stopColor="#2A2C30" />
          <stop offset="75%" stopColor="#24385E" />
          <stop offset="100%" stopColor="#B8C0CA" />
        </linearGradient>

        {/* Inner Glowing Core Petals */}
        <linearGradient id="bv-petal-inner" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#2554D9" />
          <stop offset="50%" stopColor="#BFD5FD" />
          <stop offset="100%" stopColor="#FCFCFD" />
        </linearGradient>

        {/* Core Glowing Orb */}
        <radialGradient id="bv-core-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FCFCFD" />
          <stop offset="35%" stopColor="#DBE8FE" />
          <stop offset="75%" stopColor="#3B6FEF" />
          <stop offset="100%" stopColor="#1E3894" />
        </radialGradient>

        {/* Outer Halo */}
        <radialGradient id="bv-halo" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#6093F6" stopOpacity="0.28" />
          <stop offset="50%" stopColor="#222427" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#C9D1DB" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Atmospheric ambient halo behind flower */}
      <circle r="410" fill="url(#bv-halo)" />

      {/* Full flower rosette with isometric perspective */}
      <g transform="scale(1 0.78) rotate(-4)">
        <g>
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

        </g>

        {/* Radiant Center Core */}
        <circle r="26" fill="url(#bv-core-glow)" stroke="#FFFFFF" strokeWidth="2.5" />
        <circle r="12" fill="#FFFFFF" opacity="0.9" />
      </g>
    </svg>
  );
}
