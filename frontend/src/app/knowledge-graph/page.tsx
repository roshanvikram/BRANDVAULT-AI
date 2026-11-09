"use client";

import { Network as NetworkHdr } from "lucide-react";
import { PageHeader } from "@/components/engines/ui";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Network, RotateCcw, ArrowUpRight, Loader2, Info } from "lucide-react";
import { fetchBrandGraph, BrandGraph, GraphNode, GraphNodeType } from "@/lib/api";

/* ----------------------------- node styling ------------------------------- */
const STYLE: Record<GraphNodeType, { r: number; fill: string; stroke: string; text: string; label: string }> = {
  brand:     { r: 26, fill: "#4F46E5", stroke: "#818CF8", text: "#FFFFFF", label: "Brand" },
  category:  { r: 17, fill: "#7C3AED", stroke: "#C084FC", text: "#FFFFFF", label: "Category" },
  guideline: { r: 12, fill: "#0284C7", stroke: "#38BDF8", text: "#FFFFFF", label: "Guideline" },
  campaign:  { r: 12, fill: "#6366F1", stroke: "#A5B4FC", text: "#FFFFFF", label: "Campaign" },
  rule:      { r: 10, fill: "#F59E0B", stroke: "#FDE68A", text: "#FFFFFF", label: "Rule" },
  fact:      { r: 10, fill: "#10B981", stroke: "#A7F3D0", text: "#FFFFFF", label: "Fact" },
  term:      { r: 10, fill: "#EC4899", stroke: "#FBCFE8", text: "#FFFFFF", label: "Term" },
  evidence:  { r: 8,  fill: "#06B6D4", stroke: "#BAE6FD", text: "#FFFFFF", label: "Evidence" },
  finding:   { r: 8,  fill: "#F43F5E", stroke: "#FECDD3", text: "#FFFFFF", label: "Finding" },
  claim:     { r: 8,  fill: "#8B5CF6", stroke: "#DDD6FE", text: "#FFFFFF", label: "Claim" },
  passport:  { r: 13, fill: "#059669", stroke: "#6EE7B7", text: "#FFFFFF", label: "Passport" },
};
const RING = 165;

type Pos = { x: number; y: number; depth: number };

export default function KnowledgeGraphPage() {
  const [graph, setGraph] = useState<BrandGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["brand"]));
  const [selected, setSelected] = useState<GraphNode | null>(null);

  useEffect(() => {
    fetchBrandGraph()
      .then((g) => { setGraph(g); setExpanded(new Set(["brand"])); })
      .catch((e) => setError(e?.message || "Failed to load graph"));
  }, []);

  const byId = useMemo(() => {
    const m = new Map<string, GraphNode>();
    graph?.nodes.forEach((n) => m.set(n.id, n));
    return m;
  }, [graph]);

  const childrenMap = useMemo(() => {
    const m = new Map<string, GraphNode[]>();
    graph?.nodes.forEach((n) => {
      if (n.parent) {
        const arr = m.get(n.parent) || [];
        arr.push(n);
        m.set(n.parent, arr);
      }
    });
    return m;
  }, [graph]);

  const hasChildren = (id: string) => (childrenMap.get(id)?.length || 0) > 0;

  // Visible positions via a weighted radial-tree layout over the expanded set.
  const positions = useMemo(() => {
    const pos = new Map<string, Pos>();
    if (!graph) return pos;

    const leafCount = (id: string): number => {
      const kids = expanded.has(id) ? childrenMap.get(id) || [] : [];
      if (!kids.length) return 1;
      return kids.reduce((s, k) => s + leafCount(k.id), 0);
    };

    const assign = (id: string, depth: number, a0: number, a1: number) => {
      const mid = (a0 + a1) / 2;
      const r = depth * RING;
      pos.set(id, { x: Math.cos(mid - Math.PI / 2) * r, y: Math.sin(mid - Math.PI / 2) * r, depth });
      const kids = expanded.has(id) ? childrenMap.get(id) || [] : [];
      if (!kids.length) return;
      const weights = kids.map((k) => leafCount(k.id));
      const total = weights.reduce((a, b) => a + b, 0) || kids.length;
      let a = a0;
      kids.forEach((k, i) => {
        const span = (a1 - a0) * (weights[i] / total);
        // Keep a tiny gap between sibling slices for readability.
        assign(k.id, depth + 1, a + span * 0.04, a + span * 0.96);
        a += span;
      });
    };
    assign("brand", 0, 0, Math.PI * 2);
    return pos;
  }, [graph, expanded, childrenMap]);

  // Auto-fit viewBox to the visible nodes.
  const viewBox = useMemo(() => {
    if (positions.size === 0) return "-400 -300 800 600";
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    positions.forEach((p, id) => {
      const r = STYLE[byId.get(id)?.type || "finding"].r + 46;
      minX = Math.min(minX, p.x - r); maxX = Math.max(maxX, p.x + r);
      minY = Math.min(minY, p.y - r); maxY = Math.max(maxY, p.y + r);
    });
    const w = Math.max(maxX - minX, 300);
    const h = Math.max(maxY - minY, 240);
    return `${minX} ${minY} ${w} ${h}`;
  }, [positions, byId]);

  const onNodeClick = (n: GraphNode) => {
    setSelected(n);
    if (hasChildren(n.id)) {
      setExpanded((prev) => {
        const next = new Set(prev);
        if (next.has(n.id)) {
          // collapse this node and all descendants
          const collapse = (id: string) => {
            next.delete(id);
            (childrenMap.get(id) || []).forEach((c) => collapse(c.id));
          };
          collapse(n.id);
          next.add("brand");
        } else {
          next.add(n.id);
        }
        return next;
      });
    }
  };

  const visibleEdges = useMemo(() => {
    if (!graph) return [];
    return graph.edges.filter((e) => positions.has(e.source) && positions.has(e.target));
  }, [graph, positions]);

  const legend: GraphNodeType[] = ["brand", "category", "guideline", "rule", "fact", "term", "campaign", "finding", "claim", "passport"];

  return (
    <div className="space-y-5 select-none">
      {/* Header */}
      <PageHeader
        eyebrow="Knowledge Graph"
        icon={<NetworkHdr />}
        title={<>{graph ? graph.brand.name : "Brand"} — connected knowledge</>}
        description="Every node and link is built from real records. Click a node to expand its connections or inspect its details."
        stats={graph ? [{ label: "Nodes", value: graph.stats.nodes }, { label: "Links", value: graph.stats.edges }] : undefined}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Graph canvas */}
        <div className="lg:col-span-8 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden relative" style={{ height: 620 }}>
          {!graph && !error && (
            <div className="absolute inset-0 flex items-center justify-center text-[#737373]">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-[#737373] text-xs font-mono px-6 text-center">
              <Info className="w-5 h-5 mb-2 text-[#A3A3A3]" />
              {error}. Is the backend running?
            </div>
          )}
          {graph && (
            <svg viewBox={viewBox} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
              {/* edges */}
              {visibleEdges.map((e, i) => {
                const a = positions.get(e.source)!;
                const b = positions.get(e.target)!;
                const ref = e.kind === "references";
                return (
                  <line
                    key={i}
                    x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke={ref ? "#A3A3A3" : "#E5E5E5"}
                    strokeWidth={ref ? 1 : 1.2}
                    strokeDasharray={ref ? "4 3" : undefined}
                  />
                );
              })}
              {/* nodes */}
              {Array.from(positions.entries()).map(([id, p]) => {
                const n = byId.get(id);
                if (!n) return null;
                const s = STYLE[n.type];
                const isSel = selected?.id === id;
                const expandable = hasChildren(id);
                const isOpen = expanded.has(id);
                const short = n.label.length > 20 ? n.label.slice(0, 19) + "…" : n.label;
                return (
                  <g key={id} transform={`translate(${p.x} ${p.y})`} className="cursor-pointer" onClick={() => onNodeClick(n)}>
                    {isSel && <circle r={s.r + 5} fill="none" stroke="#0A0A0A" strokeWidth={1.5} />}
                    <circle r={s.r} fill={s.fill} stroke={s.stroke} strokeWidth={1.5} />
                    {n.type === "category" && typeof n.count === "number" && (
                      <text textAnchor="middle" dy="4" fontSize="11" fontFamily="monospace" fontWeight="700" fill={s.text}>{n.count}</text>
                    )}
                    {n.type === "brand" && (
                      <text textAnchor="middle" dy="4" fontSize="10" fontFamily="monospace" fontWeight="700" fill={s.text}>BV</text>
                    )}
                    {/* label */}
                    <text textAnchor="middle" y={s.r + 13} fontSize={p.depth === 1 || n.type === "brand" ? 11 : 9}
                          fontFamily="ui-sans-serif, system-ui" fontWeight={n.type === "category" || n.type === "brand" ? 700 : 500}
                          fill={n.type === "category" || n.type === "brand" ? "#0A0A0A" : "#404040"}>
                      {short}
                    </text>
                    {expandable && (
                      <text textAnchor="middle" dy={-s.r - 5} fontSize="10" fontFamily="monospace" fill="#A3A3A3">
                        {isOpen ? "–" : "+"}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          )}

          {/* Legend */}
          <div className="absolute bottom-3 left-3 bg-white backdrop-blur-sm border border-[#E5E5E5] rounded-lg px-3 py-2 flex flex-wrap gap-x-3 gap-y-1 max-w-[88%]">
            {legend.map((t) => (
              <div key={t} className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full border" style={{ background: STYLE[t].fill, borderColor: STYLE[t].stroke }} />
                <span className="text-[11px] font-mono text-[#737373]">{STYLE[t].label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-4 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm p-5 flex flex-col" style={{ minHeight: 620 }}>
          {!selected ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-[#737373]">
              <Network className="w-9 h-9 mb-3 text-[#A3A3A3]" />
              <p className="text-xs font-mono">Select any node to inspect its real record and open it in its module.</p>
              <p className="text-[11px] text-[#A3A3A3] mt-3 leading-relaxed max-w-[220px]">
                Dark links are containment. Dashed links show a finding referencing the brand rule it was checked against.
              </p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col">
              <div className="text-[11px] font-mono uppercase tracking-wider text-[#A3A3A3] font-bold">{STYLE[selected.type].label}</div>
              <h3 className="text-base font-bold tracking-tight text-[#0A0A0A] mt-1 break-words">{selected.label}</h3>
              {typeof selected.count === "number" && (
                <div className="text-[11px] font-mono text-[#737373] mt-1">{selected.count} item{selected.count === 1 ? "" : "s"}</div>
              )}

              <div className="mt-4 space-y-2.5 overflow-y-auto flex-1">
                {Object.entries(selected.meta || {}).filter(([, v]) => v !== null && v !== undefined && v !== "").map(([k, v]) => (
                  <div key={k} className="text-xs">
                    <div className="text-[11px] font-mono uppercase text-[#A3A3A3] font-semibold">{k}</div>
                    <div className="text-[#0A0A0A] break-words leading-relaxed">{String(v)}</div>
                  </div>
                ))}
                {Object.keys(selected.meta || {}).length === 0 && (
                  <div className="text-xs text-[#737373]">No additional detail for this node.</div>
                )}
              </div>

              {selected.href && (
                <Link
                  href={selected.href}
                  className="mt-4 inline-flex items-center justify-center space-x-1.5 px-4 py-2.5 text-xs font-medium rounded-lg bg-[#0A0A0A] text-white hover:bg-[#27272A] transition-all"
                >
                  <span>Open in module</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              )}
              {hasChildren(selected.id) && (
                <button
                  onClick={() => onNodeClick(selected)}
                  className="mt-2 inline-flex items-center justify-center px-4 py-2 text-xs font-mono font-semibold rounded-lg border border-[#E5E5E5] bg-white text-[#0A0A0A] hover:bg-[#F5F5F5] transition-all"
                >
                  {expanded.has(selected.id) ? "Collapse connections" : "Expand connections"}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
