import { ReactNode } from "react";

/**
 * Decorative glass illustration for page headers. Every page gets its own scene,
 * drawn to match what the page does (a radar for Risk Radar, a helix for Brand
 * DNA, a passport for Brand Passport…), over a morphing orb whose size, place
 * and colour also change per page. Purely visual.
 */

const A = "#2554D9";   // azure
const A2 = "#6093F6";  // light azure
const N = "#1C2C4B";   // navy
const S = "#9AA1AA";   // silver
const GLASS = { fill: "url(#ha-glass)", stroke: "rgba(255,255,255,0.9)", strokeWidth: 1.2 } as const;

function Panel({ x, y, w, h, r = 14, rot = 0 }: { x: number; y: number; w: number; h: number; r?: number; rot?: number }) {
  return <rect x={x} y={y} width={w} height={h} rx={r} {...GLASS} filter="url(#ha-shadow)"
    transform={rot ? `rotate(${rot} ${x + w / 2} ${y + h / 2})` : undefined} />;
}
const Bar = ({ x, y, w, c = "rgba(28,44,75,0.28)" }: { x: number; y: number; w: number; c?: string }) => (
  <line x1={x} y1={y} x2={x + w} y2={y} stroke={c} strokeWidth={5} strokeLinecap="round" />
);
const Check = ({ x, y, s = 1, c = "#10B981" }: { x: number; y: number; s?: number; c?: string }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <circle r="10" fill={c} opacity="0.9" />
    <path d="M-4.5 0 L-1 3.5 L5 -3.5" stroke="white" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </g>
);
const Cross = ({ x, y }: { x: number; y: number }) => (
  <g transform={`translate(${x} ${y})`}>
    <circle r="10" fill="#E11D48" opacity="0.85" />
    <path d="M-3.5 -3.5 L3.5 3.5 M3.5 -3.5 L-3.5 3.5" stroke="white" strokeWidth="2.4" strokeLinecap="round" />
  </g>
);
const Dot = ({ x, y, r = 6, c = A }: { x: number; y: number; r?: number; c?: string }) => (
  <circle cx={x} cy={y} r={r} fill={c} stroke="white" strokeWidth="1.5" />
);

const SCENES: Record<string, () => ReactNode> = {
  copy: () => (<>
    <Panel x={40} y={34} w={200} h={120} rot={-3} />
    <Bar x={62} y={62} w={120} /><Bar x={62} y={82} w={150} /><Bar x={62} y={102} w={90} />
    <rect x={62} y={118} width={62} height={20} rx={10} fill="#E11D48" opacity="0.18" />
    <line x1={68} y1={128} x2={118} y2={128} stroke="#E11D48" strokeWidth="2.5" />
    <path d="M132 128 h16 m-6 -5 l6 5 l-6 5" stroke={N} strokeWidth="2" fill="none" strokeLinecap="round" />
    <rect x={156} y={118} width={70} height={20} rx={10} fill={A} opacity="0.85" />
    <g transform="translate(250 60) rotate(40)"><rect x={-5} y={-40} width={10} height={70} rx={5} fill={N} /><rect x={-5} y={-40} width={10} height={16} rx={5} fill={A2} /></g>
    <path d="M272 30 l3 7 l7 3 l-7 3 l-3 7 l-3 -7 l-7 -3 l7 -3z" fill={A2} />
    <path d="M292 70 l2 4 l4 2 l-4 2 l-2 4 l-2 -4 l-4 -2 l4 -2z" fill={A} />
  </>),
  reviewer: () => (<>
    {[0, 1, 2].map((i) => (
      <g key={i} transform={`translate(${46 + i * 82} ${50 + (i % 2) * 18})`}>
        <Panel x={0} y={0} w={72} h={100} />
        <circle cx={36} cy={30} r={14} fill={i === 1 ? A : S} opacity="0.85" />
        <rect x={14} y={58} width={44} height={8} rx={4} fill="rgba(28,44,75,0.15)" />
        <rect x={14} y={58} width={[38, 26, 18][i]} height={8} rx={4} fill={i === 1 ? A : N} opacity="0.8" />
        <Bar x={16} y={80} w={40} />
      </g>
    ))}
  </>),
  agents: () => (<>
    <Panel x={110} y={60} w={90} h={70} r={22} />
    {[[50, 40], [270, 46], [46, 160], [268, 158], [158, 22]].map(([x, y], i) => (
      <g key={i}><line x1={155} y1={95} x2={x} y2={y} stroke={A2} strokeWidth="2" strokeDasharray="4 5" /><Dot x={x} y={y} r={11} c={i % 2 ? N : A} /></g>
    ))}
    <circle cx={155} cy={95} r={18} fill={A} /><circle cx={155} cy={95} r={28} fill="none" stroke={A2} strokeWidth="2" opacity="0.6" />
  </>),
  approval: () => (<>
    <Panel x={70} y={58} w={170} h={100} rot={6} /><Panel x={58} y={46} w={170} h={100} rot={-2} />
    <Bar x={82} y={76} w={100} /><Bar x={82} y={96} w={130} /><Bar x={82} y={116} w={70} />
    <Check x={226} y={136} s={2.2} />
  </>),
  lifecycle: () => (<>
    <Panel x={40} y={40} w={120} h={116} />
    <rect x={40} y={40} width={120} height={28} rx={14} fill={A} opacity="0.8" />
    {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => <rect key={i} x={54 + (i % 3) * 32} y={80 + Math.floor(i / 3) * 24} width={22} height={14} rx={4} fill={i === 7 ? "#F59E0B" : "rgba(28,44,75,0.18)"} />)}
    <circle cx={232} cy={98} r={52} {...GLASS} filter="url(#ha-shadow)" />
    <circle cx={232} cy={98} r={40} fill="none" stroke="rgba(28,44,75,0.15)" strokeWidth="8" />
    <path d="M232 58 A40 40 0 0 1 270 110" fill="none" stroke={A} strokeWidth="8" strokeLinecap="round" />
    <path d="M232 98 L232 74 M232 98 L248 106" stroke={N} strokeWidth="3" strokeLinecap="round" />
  </>),
  forensics: () => (<>
    <Panel x={40} y={36} w={190} h={124} />
    <rect x={64} y={60} width={70} height={34} rx={8} fill={A} opacity="0.85" />
    <path d="M58 140 l40 -30 l30 20 l30 -26 l50 36" fill="none" stroke={S} strokeWidth="3" />
    <circle cx={232} cy={110} r={40} fill="rgba(255,255,255,0.35)" stroke="white" strokeWidth="3" filter="url(#ha-shadow)" />
    <line x1={260} y1={140} x2={290} y2={172} stroke={N} strokeWidth="10" strokeLinecap="round" />
    <path d="M232 92 v36 M214 110 h36" stroke={A} strokeWidth="2" />
  </>),
  assistant: () => (<>
    <path d="M40 46 h150 a14 14 0 0 1 14 14 v40 a14 14 0 0 1 -14 14 h-110 l-22 18 v-18 h-18 a14 14 0 0 1 -14 -14 v-40 a14 14 0 0 1 14 -14z" {...GLASS} filter="url(#ha-shadow)" />
    <Bar x={60} y={72} w={110} /><Bar x={60} y={92} w={70} />
    <path d="M140 108 h140 a14 14 0 0 1 14 14 v34 a14 14 0 0 1 -14 14 h-12 v16 l-20 -16 h-108 a14 14 0 0 1 -14 -14 v-34 a14 14 0 0 1 14 -14z" fill={A} opacity="0.9" filter="url(#ha-shadow)" />
    {[0, 1, 2].map((i) => <circle key={i} cx={190 + i * 18} cy={139} r={5} fill="white" opacity={1 - i * 0.25} />)}
  </>),
  heatmap: () => (<>
    <Panel x={50} y={28} w={220} h={144} />
    {[0.15, 0.35, 0.8, 0.5, 0.2, 0.65, 0.9, 0.3, 0.55, 0.1, 0.45, 0.75, 0.25, 0.6, 0.95, 0.4, 0.7, 0.2, 0.5, 0.85, 0.3, 0.6, 0.15, 0.45].map((v, i) => (
      <rect key={i} x={68 + (i % 6) * 32} y={44 + Math.floor(i / 6) * 30} width={26} height={24} rx={6} fill={A} opacity={v} />
    ))}
  </>),
  dna: () => (<>
    <Panel x={56} y={30} w={210} h={140} r={24} />
    {Array.from({ length: 11 }).map((_, i) => {
      const x = 76 + i * 17, t = (i / 10) * Math.PI * 2;
      const y1 = 100 + Math.sin(t) * 42, y2 = 100 - Math.sin(t) * 42;
      return <g key={i}><line x1={x} y1={y1} x2={x} y2={y2} stroke="rgba(28,44,75,0.22)" strokeWidth="3" />
        <circle cx={x} cy={y1} r={6.5} fill={A} /><circle cx={x} cy={y2} r={6.5} fill={N} opacity="0.85" /></g>;
    })}
  </>),
  fraud: () => (<>
    <path d="M160 26 l70 24 v46 c0 42 -30 66 -70 82 c-40 -16 -70 -40 -70 -82 v-46z" {...GLASS} filter="url(#ha-shadow)" />
    <path d="M160 70 l30 54 h-60z" fill="#F59E0B" opacity="0.9" />
    <path d="M160 88 v18" stroke="white" strokeWidth="4" strokeLinecap="round" /><circle cx={160} cy={114} r={2.6} fill="white" />
    <g opacity="0.8"><path d="M40 70 a14 14 0 0 1 0 -28 h22" fill="none" stroke={N} strokeWidth="5" strokeLinecap="round" />
      <path d="M86 42 h12 a14 14 0 0 1 0 28 h-12" fill="none" stroke={N} strokeWidth="5" strokeLinecap="round" strokeDasharray="6 6" /></g>
    <Dot x={270} y={150} r={9} c="#E11D48" /><Dot x={252} y={60} r={6} c={A2} />
  </>),
  memory: () => (<>
    <Panel x={30} y={44} w={260} h={112} r={20} />
    <path d="M48 128 C 90 70, 130 140, 170 92 S 250 60, 274 82" fill="none" stroke={A2} strokeWidth="4" />
    {[[66, 108], [124, 116], [170, 92], [226, 74], [272, 82]].map(([x, y], i) => (
      <g key={i}><line x1={x} y1={y} x2={x} y2={y - 30} stroke={S} strokeWidth="2" /><Dot x={x} y={y - 34} r={7} c={i === 2 ? A : N} /></g>
    ))}
  </>),
  passport: () => (<>
    <rect x={70} y={28} width={140} height={150} rx={16} fill={N} opacity="0.92" filter="url(#ha-shadow)" transform="rotate(-6 140 103)" />
    <Panel x={88} y={30} w={140} h={150} r={16} rot={4} />
    <circle cx={158} cy={86} r={28} fill="none" stroke={A} strokeWidth="3" />
    <path d="M144 86 a14 14 0 0 1 28 0 M150 86 a8 8 0 0 1 16 0 M156 86 a2 2 0 0 1 4 0" stroke={A} strokeWidth="2.2" fill="none" />
    <Bar x={118} y={136} w={80} /><Bar x={118} y={154} w={54} />
    <Check x={236} y={58} s={1.8} />
  </>),
  reputation: () => (<>
    <Panel x={36} y={40} w={248} h={120} />
    {[0, 1, 2, 3, 4].map((i) => <path key={i} transform={`translate(${62 + i * 26} 64)`} d="M0 -9 l2.6 6 l6.4 .6 l-4.9 4.2 l1.5 6.3 l-5.6 -3.4 l-5.6 3.4 l1.5 -6.3 l-4.9 -4.2 l6.4 -.6z" fill={i < 3 ? "#F59E0B" : "rgba(28,44,75,0.2)"} />)}
    <path d="M56 130 L96 112 L136 120 L176 96 L216 128 L256 142" fill="none" stroke={A} strokeWidth="3.5" strokeLinejoin="round" />
    <circle cx={256} cy={142} r={6} fill="#E11D48" />
    <path d="M246 60 a14 14 0 0 1 28 0 v10 l5 6 h-38 l5 -6z" fill={N} opacity="0.85" /><circle cx={260} cy={82} r={3.5} fill={N} />
  </>),
  fingerprint: () => (<>
    <Panel x={84} y={22} w={152} h={156} r={30} />
    {[14, 24, 34, 44, 54].map((r, i) => (
      <path key={r} d={`M${160 - r} 110 a${r} ${r * 1.15} 0 0 1 ${r * 2} 0`} fill="none" stroke={i % 2 ? N : A} strokeWidth="3.2" strokeLinecap="round"
        strokeDasharray={i === 3 ? "14 6" : undefined} opacity="0.85" />
    ))}
    <path d="M118 130 c10 18 30 28 42 28 s32 -10 42 -28" fill="none" stroke={A2} strokeWidth="3.2" strokeLinecap="round" />
  </>),
  readiness: () => (<>
    <Panel x={40} y={30} w={240} h={140} r={22} />
    <path d="M90 140 A70 70 0 0 1 230 140" fill="none" stroke="rgba(28,44,75,0.15)" strokeWidth="16" strokeLinecap="round" />
    <path d="M90 140 A70 70 0 0 1 206 92" fill="none" stroke={A} strokeWidth="16" strokeLinecap="round" />
    <line x1={160} y1={140} x2={200} y2={96} stroke={N} strokeWidth="4" strokeLinecap="round" /><circle cx={160} cy={140} r={8} fill={N} />
    <Check x={256} y={56} s={1.3} />
  </>),
  stress: () => (<>
    <Panel x={36} y={30} w={248} h={140} />
    {[40, 62, 50, 88, 70, 104, 58, 94, 78].map((h, i) => <rect key={i} x={58 + i * 24} y={152 - h} width={16} height={h} rx={5} fill={h > 85 ? "#E11D48" : A} opacity={h > 85 ? 0.8 : 0.75} />)}
    <line x1={50} y1={66} x2={270} y2={66} stroke="#F59E0B" strokeWidth="2.5" strokeDasharray="7 6" />
  </>),
  claim: () => (<>
    <Panel x={56} y={22} w={210} h={156} />
    {([["#10B981", 120], ["#E11D48", 90], ["#F59E0B", 110], ["#10B981", 70]] as [string, number][]).map(([c, w], i) => (
      <g key={i}>{c === "#E11D48" ? <Cross x={84} y={52 + i * 34} /> : <Check x={84} y={52 + i * 34} c={c} />}
        <Bar x={106} y={52 + i * 34} w={w} /></g>
    ))}
  </>),
  content: () => (<>
    <Panel x={44} y={22} w={170} h={156} r={12} />
    <Bar x={64} y={50} w={120} /><rect x={62} y={64} width={92} height={14} rx={4} fill="#F59E0B" opacity="0.35" /><Bar x={64} y={71} w={88} />
    <Bar x={64} y={94} w={130} /><rect x={62} y={108} width={70} height={14} rx={4} fill="#E11D48" opacity="0.25" /><Bar x={64} y={115} w={66} /><Bar x={64} y={138} w={110} />
    <circle cx={236} cy={112} r={42} fill="rgba(255,255,255,0.3)" stroke="white" strokeWidth="3" filter="url(#ha-shadow)" />
    <line x1={266} y1={142} x2={292} y2={170} stroke={A} strokeWidth="10" strokeLinecap="round" />
  </>),
  similarity: () => (<>
    <Panel x={36} y={36} w={140} h={130} rot={-5} /><Panel x={146} y={36} w={140} h={130} rot={5} />
    <rect x={118} y={70} width={86} height={14} rx={7} fill={A} opacity="0.75" />
    <rect x={124} y={104} width={74} height={14} rx={7} fill={A} opacity="0.5" />
    <Bar x={56} y={140} w={70} /><Bar x={200} y={140} w={70} />
  </>),
  creative: () => (<>
    <Panel x={30} y={34} w={260} h={132} r={16} />
    <rect x={30} y={34} width={260} height={132} rx={16} fill="url(#ha-azure)" opacity="0.22" />
    <rect x={56} y={58} width={150} height={26} rx={4} fill="none" stroke={A} strokeWidth="2.5" strokeDasharray="6 4" />
    <Bar x={66} y={71} w={120} c={N} />
    <rect x={56} y={98} width={110} height={22} rx={4} fill="none" stroke="#E11D48" strokeWidth="2.5" strokeDasharray="6 4" />
    <Bar x={66} y={109} w={88} c={N} />
    <rect x={226} y={56} width={44} height={44} rx={10} fill={N} opacity="0.85" />
    <path d="M56 148 l36 -20 l28 12 l30 -18 l40 26" fill="none" stroke={S} strokeWidth="3" />
  </>),
  gaps: () => (<>
    {([[60, 40, false], [140, 40, false], [60, 110, false], [140, 110, true]] as [number, number, boolean][]).map(([x, y, missing], i) => (
      missing ? <rect key={i} x={x} y={y} width={72} height={62} rx={12} fill="none" stroke={A} strokeWidth="2.5" strokeDasharray="7 6" />
        : <Panel key={i} x={x} y={y} w={72} h={62} r={12} />
    ))}
    <g transform="translate(246 128) rotate(14)"><rect x={-36} y={-31} width={72} height={62} rx={12} fill={A} opacity="0.88" filter="url(#ha-shadow)" />
      <text x={0} y={8} textAnchor="middle" fontSize="24" fontWeight="700" fill="white">?</text></g>
  </>),
  graph: () => (<>
    <Panel x={30} y={24} w={260} h={152} r={24} />
    {[[70, 60, 140, 96], [140, 96, 220, 54], [140, 96, 120, 150], [220, 54, 262, 120], [120, 150, 220, 142], [220, 142, 262, 120], [70, 60, 120, 150]].map(([a, b, c, d], i) => (
      <line key={i} x1={a} y1={b} x2={c} y2={d} stroke="rgba(28,44,75,0.3)" strokeWidth="2" />
    ))}
    {([[70, 60, 9, N], [140, 96, 15, A], [220, 54, 10, A2], [120, 150, 8, N], [262, 120, 9, A], [220, 142, 7, S]] as [number, number, number, string][]).map(([x, y, r, c], i) => <Dot key={i} x={x} y={y} r={r} c={c} />)}
  </>),
  truth: () => (<>
    <rect x={70} y={60} width={150} height={92} rx={8} {...GLASS} filter="url(#ha-shadow)" />
    <rect x={80} y={70} width={130} height={72} rx={4} fill="url(#ha-azure)" opacity="0.5" />
    <path d="M52 156 h186 l-14 14 h-158z" fill={N} opacity="0.85" />
    {([["45 TOPS", 244, 48], ["18 h", 256, 92], ["₹79,999", 238, 136]] as [string, number, number][]).map(([t, x, y], i) => (
      <g key={i}><rect x={x - 4} y={y - 15} width={66} height={22} rx={11} fill="white" stroke={A} strokeWidth="1.5" />
        <text x={x + 29} y={y + 0.5} textAnchor="middle" fontSize="10.5" fontWeight="700" fill={A}>{t}</text></g>
    ))}
  </>),
  gate: () => (<>
    <path d="M86 176 v-96 a74 74 0 0 1 148 0 v96" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth={14} filter="url(#ha-shadow)" />
    <path d="M86 176 v-96 a74 74 0 0 1 148 0 v96" fill="none" stroke={A} strokeWidth="3" opacity="0.6" />
    <rect x={136} y={96} width={48} height={40} rx={8} fill={N} opacity="0.9" />
    <path d="M146 96 v-12 a14 14 0 0 1 28 0 v12" fill="none" stroke={N} strokeWidth="5" />
    <path d="M30 156 h66 m-12 -10 l12 10 l-12 10" stroke={A} strokeWidth="4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    <Check x={268} y={150} s={1.4} />
  </>),
  radar: () => (<>
    <circle cx={160} cy={100} r={78} {...GLASS} filter="url(#ha-shadow)" />
    {[56, 36, 16].map((r) => <circle key={r} cx={160} cy={100} r={r} fill="none" stroke="rgba(28,44,75,0.2)" strokeWidth="1.5" />)}
    <path d="M160 100 L160 22 A78 78 0 0 1 228 62 Z" fill="url(#ha-azure)" opacity="0.55" />
    <Dot x={196} y={62} r={6} c="#E11D48" /><Dot x={126} y={124} r={5} c="#F59E0B" /><Dot x={182} y={138} r={4} c={A} />
  </>),
  settings: () => (<>
    <Panel x={40} y={40} w={150} h={120} />
    {[0, 1, 2].map((i) => (<g key={i}><line x1={62} y1={70 + i * 32} x2={170} y2={70 + i * 32} stroke="rgba(28,44,75,0.2)" strokeWidth="5" strokeLinecap="round" />
      <circle cx={[90, 140, 112][i]} cy={70 + i * 32} r={9} fill={i === 1 ? A : N} stroke="white" strokeWidth="2" /></g>))}
    <g transform="translate(240 98)">
      {Array.from({ length: 8 }).map((_, i) => <rect key={i} x={-7} y={-48} width={14} height={20} rx={4} fill={N} opacity="0.85" transform={`rotate(${i * 45})`} />)}
      <circle r="34" fill={N} opacity="0.85" /><circle r="14" {...GLASS} />
    </g>
  </>),
  setup: () => (<>
    <path d="M44 156 C 100 156, 90 100, 150 100 S 210 44, 276 44" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="18" strokeLinecap="round" filter="url(#ha-shadow)" />
    <path d="M44 156 C 100 156, 90 100, 150 100 S 210 44, 276 44" fill="none" stroke={A2} strokeWidth="4" strokeDasharray="2 10" strokeLinecap="round" />
    {([[52, 156, "1"], [150, 100, "2"], [270, 44, "3"]] as [number, number, string][]).map(([x, y, t], i) => (
      <g key={i}><circle cx={x} cy={y} r={16} fill={i < 2 ? A : N} stroke="white" strokeWidth="3" />
        <text x={x} y={y + 5} textAnchor="middle" fontSize="14" fontWeight="700" fill="white">{t}</text></g>
    ))}
  </>),
  translation: () => (<>
    <path d="M36 40 h110 a16 16 0 0 1 16 16 v50 a16 16 0 0 1 -16 16 h-74 l-20 18 v-18 h-16 a16 16 0 0 1 -16 -16 v-50 a16 16 0 0 1 16 -16z" {...GLASS} filter="url(#ha-shadow)" />
    <text x={90} y={94} textAnchor="middle" fontSize="34" fontWeight="700" fill={N}>Aa</text>
    <path d="M174 78 h112 a16 16 0 0 1 16 16 v50 a16 16 0 0 1 -16 16 h-16 v18 l-20 -18 h-76 a16 16 0 0 1 -16 -16 v-50 a16 16 0 0 1 16 -16z" fill={A} opacity="0.9" filter="url(#ha-shadow)" />
    <text x={230} y={132} textAnchor="middle" fontSize="34" fontWeight="700" fill="white">अ</text>
    <path d="M150 140 h20 M150 150 h20" stroke={N} strokeWidth="3" strokeLinecap="round" />
  </>),
  visual: () => (<>
    {([[-30, N], [-15, "#3F5B8F"], [0, A], [15, A2], [30, "#DCE0E5"]] as [number, string][]).map(([rot, c], i) => (
      <rect key={i} x={120} y={30} width={44} height={130} rx={12} fill={c} opacity="0.92" stroke="white" strokeWidth="1.5"
        transform={`rotate(${rot} 142 160)`} filter="url(#ha-shadow)" />
    ))}
    <circle cx={252} cy={70} r={32} {...GLASS} filter="url(#ha-shadow)" />
    <path d="M252 38 a32 32 0 0 1 0 64z" fill={N} opacity="0.85" />
  </>),
};

// eyebrow -> [scene, orb right (px), orb top (px), orb size (px), orb gradient]
const PAGE: Record<string, [string, number, number, number, string]> = {
  "AI Copy Studio": ["copy", 30, 10, 130, "from-[#6093F6] to-[#1C2C4B]"],
  "AI Reviewer Intelligence": ["reviewer", 200, 40, 120, "from-[#93B8FB] to-[#2554D9]"],
  "Agent Control": ["agents", 110, 50, 110, "from-[#2554D9] to-[#0D1626]"],
  "Approval Hub": ["approval", 40, 70, 140, "from-[#BFD5FD] to-[#2554D9]"],
  "Asset Lifecycle & Expiry": ["lifecycle", 20, 20, 120, "from-[#C3C8CF] to-[#3E4248]"],
  "Brand Asset Forensics": ["forensics", 160, 10, 130, "from-[#6093F6] to-[#1E3894]"],
  "Brand Assistant": ["assistant", 60, 80, 120, "from-[#93B8FB] to-[#1C2C4B]"],
  "Brand Consistency Heatmap": ["heatmap", 230, 70, 110, "from-[#2554D9] to-[#152147]"],
  "Brand DNA Studio": ["dna", 120, 20, 150, "from-[#6093F6] to-[#1D42B8]"],
  "Brand Fraud Intelligence": ["fraud", 150, 60, 130, "from-[#F59E0B] to-[#1C2C4B]"],
  "Brand Memory": ["memory", 30, 30, 120, "from-[#BCCBE3] to-[#24385E]"],
  "Brand Passport": ["passport", 200, 30, 140, "from-[#6093F6] to-[#152147]"],
  "Brand Reputation Early Warning": ["reputation", 20, 60, 130, "from-[#FDE68A] to-[#2554D9]"],
  "Campaign DNA Fingerprint": ["fingerprint", 100, 40, 150, "from-[#93B8FB] to-[#1E3375]"],
  "Campaign Launch Readiness": ["readiness", 180, 70, 120, "from-[#6EE7B7] to-[#2554D9]"],
  "Campaign Stress Testing": ["stress", 60, 10, 120, "from-[#FDA4AF] to-[#1C2C4B]"],
  "ClaimDNA": ["claim", 210, 60, 130, "from-[#6093F6] to-[#1C2C4B]"],
  "Content Intelligence": ["content", 40, 20, 150, "from-[#BFD5FD] to-[#1D42B8]"],
  "Content Similarity Detector": ["similarity", 130, 80, 120, "from-[#93B8FB] to-[#24385E]"],
  "Creative Inspection": ["creative", 190, 20, 140, "from-[#6093F6] to-[#0D1626]"],
  "Knowledge Gap Detector": ["gaps", 60, 50, 130, "from-[#C3C8CF] to-[#2554D9]"],
  "Knowledge Graph": ["graph", 150, 30, 150, "from-[#2554D9] to-[#16233C]"],
  "Product Truth Engine": ["truth", 210, 40, 120, "from-[#93B8FB] to-[#1E3894]"],
  "Publishing Gate": ["gate", 120, 60, 130, "from-[#6EE7B7] to-[#1C2C4B]"],
  "Risk Radar": ["radar", 120, 30, 160, "from-[#FDA4AF] to-[#1D42B8]"],
  "Settings": ["settings", 30, 60, 120, "from-[#C3C8CF] to-[#2E3135]"],
  "Setup Guide": ["setup", 200, 60, 120, "from-[#93B8FB] to-[#2554D9]"],
  "Translation Guard": ["translation", 110, 10, 130, "from-[#6093F6] to-[#24385E]"],
  "Visual DNA": ["visual", 40, 40, 150, "from-[#FDE68A] to-[#1D42B8]"],
};

export function HeroArt({ eyebrow }: { eyebrow: string }) {
  const [scene, right, top, size, orb] = PAGE[eyebrow] ?? ["content", 60, 30, 130, "from-[#6093F6] to-[#1C2C4B]"];
  const draw = SCENES[scene] ?? SCENES.content;
  return (
    <div aria-hidden className="pointer-events-none absolute right-2 top-2 h-[200px] w-[330px] hidden xl:block">
      <div className={`bv-morph absolute bg-gradient-to-br ${orb} opacity-60`} style={{ right, top, width: size, height: size }} />
      <svg viewBox="0 0 320 200" className="bv-float relative w-full h-full">
        <defs>
          <linearGradient id="ha-glass" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.82" /><stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.32" />
          </linearGradient>
          <linearGradient id="ha-azure" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={A2} /><stop offset="100%" stopColor={A} />
          </linearGradient>
          <filter id="ha-shadow" x="-20%" y="-20%" width="140%" height="150%">
            <feDropShadow dx="0" dy="8" stdDeviation="8" floodColor="#1C2C4B" floodOpacity="0.22" />
          </filter>
        </defs>
        {draw()}
      </svg>
    </div>
  );
}
