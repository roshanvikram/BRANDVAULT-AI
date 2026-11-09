"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ScanText, Upload, Loader2, FileText, Film, Image as ImageIcon, ArrowRight, Wand2, Frame } from "lucide-react";
import {
  fetchCreativeStatus, fetchCreativeInspections, fetchCreativeInspection, inspectCreative,
  CreativeInspectionOut, CreativeRegion,
} from "@/lib/api";
import { CARD, Badge, Tone, PageHeader, ErrorNote, Loading, ProtectedImage, BTN_PRIMARY, INPUT } from "@/components/engines/ui";

const SEV_TONE: Record<string, Tone> = {
  CRITICAL: "bad", WARNING: "warn", SUGGESTION: "info", Contradicted: "bad", Outdated: "warn",
  Unsupported: "neutral", "Needs Human Review": "ai", Supported: "good", OK: "good",
};
const BOX: Record<string, string> = {
  bad: "border-rose-500 bg-rose-500/10", warn: "border-amber-500 bg-amber-400/10", good: "border-emerald-500 bg-emerald-500/10",
  neutral: "border-slate-500 bg-slate-400/10", info: "border-sky-500 bg-sky-400/10", ai: "border-violet-500 bg-violet-500/10",
};
const KIND_ICON = { image: ImageIcon, pdf: FileText, video: Film };

function scoreTone(s: number | null): Tone { return s === null ? "neutral" : s >= 80 ? "good" : s >= 50 ? "warn" : "bad"; }

export default function CreativeInspectionPage() {
  const [status, setStatus] = useState<Awaited<ReturnType<typeof fetchCreativeStatus>> | null>(null);
  const [list, setList] = useState<CreativeInspectionOut[] | null>(null);
  const [current, setCurrent] = useState<CreativeInspectionOut | null>(null);
  const [page, setPage] = useState(0);
  const [focus, setFocus] = useState<string | null>(null);
  const [department, setDepartment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => fetchCreativeInspections().then(setList).catch((e) => setError(e.message));
  useEffect(() => { fetchCreativeStatus().then(setStatus).catch(() => {}); load(); }, []);

  const run = async (file: File) => {
    setBusy(true); setError(null); setCurrent(null);
    try { const r = await inspectCreative(file, department.trim() || undefined); setCurrent(r); setPage(0); load(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  const open = async (id: string) => {
    setError(null);
    try { setCurrent(await fetchCreativeInspection(id)); setPage(0); setFocus(null); } catch (e: any) { setError(e.message); }
  };

  const pg = current?.pages?.[page];
  // Most severe last, so it is drawn on top when several issues share one line.
  const RANK: Record<string, number> = { CRITICAL: 4, Contradicted: 4, WARNING: 3, Outdated: 3, Unsupported: 2, "Needs Human Review": 2, SUGGESTION: 1 };
  const regions = useMemo(() => (current?.regions || []).filter((r) => r.page === page)
    .sort((a, b) => (RANK[a.severity] || 0) - (RANK[b.severity] || 0)), [current, page]);
  const regionFor = (id: string) => (current?.regions || []).find((r) => r.id === id);

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/visual-dna", label: "Visual DNA" }}
        eyebrow="Creative Inspection" icon={<ScanText className="w-3.5 h-3.5" />}
        title="Check the words inside your creatives"
        description="Upload a banner, social image, PDF deck or short video. BrandVault reads the text (exact text layer for PDFs, OCR for images and video frames), runs the same Brand DNA, Product Truth and ClaimDNA checks as typed copy, marks each issue on the creative, and checks logo clear space."
        actions={status && (status.ocr.available
          ? <Badge tone="good">OCR ready · {status.ocr.engine}</Badge>
          : <Badge tone="warn">OCR unavailable — PDFs with a text layer still work</Badge>)}
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-4 space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <input ref={fileRef} type="file" className="sr-only"
                   accept="image/png,image/jpeg,image/webp,image/bmp,application/pdf,video/mp4,video/webm,video/quicktime"
                   onChange={(e) => { const f = e.target.files?.[0]; if (f) run(f); e.target.value = ""; }} />
            <button onClick={() => fileRef.current?.click()} disabled={busy}
                    className="w-full rounded-2xl border-2 border-dashed border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/40 transition-colors p-6 text-center disabled:opacity-60">
              {busy ? <Loader2 className="w-6 h-6 mx-auto text-indigo-500 animate-spin" /> : <Upload className="w-6 h-6 mx-auto text-indigo-500" />}
              <div className="mt-2 text-sm font-semibold text-slate-900">{busy ? "Reading and checking…" : "Choose a creative"}</div>
              <div className="text-xs text-slate-500 mt-0.5">PNG, JPEG, WebP, PDF, MP4/WebM/MOV</div>
            </button>
            <label className="block text-xs text-slate-600">Department (optional)
              <input value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="e.g. Social" className={`${INPUT} h-9 mt-1`} />
            </label>
            {status && (
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Limits: images {status.limits.max_mb.image} MB · PDFs {status.limits.max_mb.pdf} MB (first {status.limits.pdf_pages} pages; scanned pages OCR&apos;d up to {status.limits.ocr_pdf_pages}) · video {status.limits.max_mb.video} MB ({status.limits.video_frames} key frames). Videos take 10–20 seconds.
              </p>
            )}
            <ErrorNote message={error} />
          </div>

          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-semibold text-slate-900">Recent inspections</h3>
            {!list ? <Loading /> : list.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">None yet.</p> : (
              <ul className="mt-2 divide-y divide-slate-100">
                {list.map((i) => {
                  const Icon = KIND_ICON[i.kind];
                  return (
                    <li key={i.id}>
                      <button onClick={() => open(i.id)} className={`w-full py-2.5 text-left flex items-center gap-2.5 ${current?.id === i.id ? "text-indigo-700" : ""}`}>
                        <Icon className="w-4 h-4 text-slate-400 shrink-0" />
                        <div className="min-w-0 flex-1"><div className="text-[13px] font-medium truncate">{i.file_name}</div>
                          <div className="text-[11px] text-slate-500">{i.page_count} page(s) · {i.text_found ? "text found" : "no readable text"}</div></div>
                        {i.score !== null && <Badge tone={scoreTone(i.score)}>{i.score}</Badge>}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        <div className="xl:col-span-8 space-y-4">
          {!current ? (
            <div className={`${CARD} p-10 text-center`}>
              <ScanText className="w-8 h-8 text-indigo-400 mx-auto" />
              <h3 className="mt-3 text-base font-semibold text-slate-900">No creative open</h3>
              <p className="mt-1 text-[13px] text-slate-500 max-w-md mx-auto">Upload a creative or pick a recent inspection. Issues are drawn directly on the page.</p>
            </div>
          ) : (
            <>
              <div className={`${CARD} p-5 flex flex-wrap items-center gap-3 justify-between`}>
                <div className="min-w-0">
                  <div className="text-xs text-slate-500">{current.kind.toUpperCase()} · {current.page_count} page(s) · {(current.elapsed_ms / 1000).toFixed(1)}s · {current.engine}</div>
                  <h3 className="text-[15px] font-semibold text-slate-900 truncate">{current.file_name}</h3>
                  {current.note && <p className="text-xs text-amber-700 mt-0.5">{current.note}</p>}
                </div>
                <div className="flex items-center gap-2">
                  {current.score !== null && <Badge tone={scoreTone(current.score)} className="text-xs px-2.5 py-1">Score {current.score}/100</Badge>}
                  {current.submission_id && (
                    <Link href={`/content-intelligence?submissionId=${current.submission_id}`} className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1">
                      Open in Content Intelligence <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  )}
                </div>
              </div>

              {!current.text_found && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] text-amber-900">
                  No readable text was found, so no claims were checked. Nothing has been guessed.
                </div>
              )}

              {current.pages && current.pages.length > 1 && (
                <div className="flex flex-wrap gap-1.5">
                  {current.pages.map((p) => (
                    <button key={p.index} onClick={() => { setPage(p.index); setFocus(null); }}
                            className={`h-8 px-3 rounded-lg text-xs font-semibold ring-1 ${p.index === page ? "bg-indigo-600 text-white ring-indigo-600" : "bg-white text-slate-600 ring-slate-200 hover:ring-indigo-300"}`}>
                      {p.label}{(current.regions || []).some((r) => r.page === p.index && r.kind !== "logo") ? " •" : ""}
                    </button>
                  ))}
                </div>
              )}

              {pg && (
                <div className={`${CARD} p-3`}>
                  {pg.has_image ? (
                    <div className="relative">
                      <ProtectedImage path={`/creative/inspections/${current.id}/pages/${pg.index}/image`} alt={pg.label} className="w-full h-auto rounded-xl" />
                      {regions.map((r, k) => <RegionBox key={k} r={r} w={pg.width} h={pg.height} active={focus === r.id} onClick={() => setFocus(r.id)} />)}
                    </div>
                  ) : <p className="p-6 text-center text-[13px] text-slate-500">Page image not available.</p>}
                  <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-500 px-1">
                    <span className="inline-flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-rose-500" /> critical / contradicted</span>
                    <span className="inline-flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-amber-500" /> warning / outdated</span>
                    <span className="inline-flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-slate-500" /> unsupported</span>
                    <span className="inline-flex items-center gap-1"><span className="w-3 h-3 rounded border-2 border-emerald-500" /> supported / logo OK</span>
                    <span className="ml-auto">Text source: {pg.source === "pdf-text" ? "PDF text layer (exact)" : pg.source === "ocr" ? "OCR" : "not read"}</span>
                  </div>
                </div>
              )}

              {current.submission && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div className={`${CARD} p-5`}>
                    <h4 className="text-sm font-semibold text-slate-900">Findings ({current.submission.findings.length})</h4>
                    <ul className="mt-2 space-y-2">
                      {current.submission.findings.map((f) => {
                        const reg = regionFor(f.id);
                        return (
                          <li key={f.id}>
                            <button onClick={() => { if (reg) { setPage(reg.page); setFocus(f.id); } }}
                                    className={`w-full text-left rounded-xl border p-3 transition-colors ${focus === f.id ? "border-indigo-400 bg-indigo-50/50" : "border-slate-200 hover:border-slate-300"}`}>
                              <div className="flex flex-wrap items-center gap-1.5"><Badge tone={SEV_TONE[f.severity] || "neutral"}>{f.severity}</Badge>
                                <span className="text-xs text-slate-500">{f.category}</span>
                                {reg ? <span className="text-[11px] text-indigo-600 ml-auto">{current.pages?.[reg.page]?.label}</span> : <span className="text-[11px] text-slate-400 ml-auto">not located</span>}</div>
                              <div className="mt-1 text-[13px] font-medium text-slate-900">“{f.text}”</div>
                              <p className="text-xs text-slate-600">{f.explanation}</p>
                              {f.suggestion && <p className="text-xs text-emerald-700 mt-0.5">→ {f.suggestion}</p>}
                            </button>
                          </li>
                        );
                      })}
                      {current.submission.findings.length === 0 && <li className="text-[13px] text-slate-500">No issues found.</li>}
                    </ul>
                  </div>
                  <div className="space-y-4">
                    <div className={`${CARD} p-5`}>
                      <h4 className="text-sm font-semibold text-slate-900">Claims ({current.submission.claims.length})</h4>
                      <ul className="mt-2 space-y-1.5">
                        {current.submission.claims.map((c) => (
                          <li key={c.id} className="text-xs flex items-start gap-2"><Badge tone={SEV_TONE[c.status] || "neutral"}>{c.status}</Badge><span className="text-slate-700">{c.text}</span></li>
                        ))}
                        {current.submission.claims.length === 0 && <li className="text-[13px] text-slate-500">No factual claims found.</li>}
                      </ul>
                    </div>
                    {(current.corrections || []).length > 0 && (
                      <div className={`${CARD} p-5`}>
                        <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5"><Wand2 className="w-4 h-4 text-slate-400" /> OCR corrections ({current.corrections!.length})</h4>
                        <p className="text-[11px] text-slate-500">Only fixes that match your brand vocabulary or a clear price context are applied.</p>
                        <ul className="mt-2 space-y-1 text-xs text-slate-700">
                          {current.corrections!.slice(0, 8).map((c, i) => <li key={i}><span className="line-through text-slate-400">{c.from}</span> → <b>{c.to}</b> <span className="text-slate-400">· {c.reason}</span></li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className={`${CARD} p-5`}>
                <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5"><Frame className="w-4 h-4 text-slate-400" /> Logo clear space</h4>
                {(current.logo_checks || []).length === 0 ? (
                  <p className="mt-1 text-[13px] text-slate-500">No official logo from the Asset Library was found in this creative. Add logos in Asset Forensics to enable this check.</p>
                ) : (
                  <ul className="mt-2 space-y-2">
                    {current.logo_checks!.map((l, i) => (
                      <li key={i} className="rounded-xl border border-slate-200 p-3 text-xs">
                        <div className="flex items-center gap-2"><Badge tone={l.clear_space.ok ? "good" : "warn"}>{l.clear_space.ok ? "Clear space OK" : "Clear space too small"}</Badge>
                          <b className="text-slate-800">{l.asset_name} {l.version_label}</b><span className="text-slate-400">· {current.pages?.[l.page]?.label}</span></div>
                        <p className="mt-1 text-slate-600">Needs {l.clear_space.required_px}px; closest edge {l.clear_space.min_margin_px}px{l.clear_space.tight_edges.length ? ` (${l.clear_space.tight_edges.join(", ")})` : ""}.
                          {l.clear_space.intruding_text.length > 0 && <> Text inside the clear zone: “{l.clear_space.intruding_text.join("”, “")}”.</>}</p>
                        {l.findings.filter((f) => f.type !== "official_logo").map((f, k) => <p key={k} className="text-rose-700">• {f.title} — {f.measurement}</p>)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {pg && pg.lines.length > 0 && (
                <div className={`${CARD} p-5`}>
                  <h4 className="text-sm font-semibold text-slate-900">Text read from {pg.label.toLowerCase()}</h4>
                  <ul className="mt-2 space-y-1 text-[13px]">
                    {pg.lines.map((l, i) => (
                      <li key={i} className="flex items-baseline gap-2">
                        <span className={`tabular-nums text-[11px] w-10 shrink-0 ${l.low_confidence ? "text-amber-600" : "text-slate-400"}`}>{Math.round(l.confidence * 100)}%</span>
                        <span className="text-slate-800">{l.text}</span>
                        {l.ocr_text && <span className="text-[11px] text-slate-400">(read as “{l.ocr_text}”)</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function RegionBox({ r, w, h, active, onClick }: { r: CreativeRegion; w: number; h: number; active: boolean; onClick: () => void }) {
  const tone = SEV_TONE[r.severity] || "neutral";
  const [x, y, bw, bh] = r.box;
  const pad = 4;
  return (
    <button onClick={onClick} title={`${r.category}: ${r.label}`} aria-label={`${r.category}: ${r.label}`}
            className={`absolute rounded-md border-2 transition-all ${BOX[tone]} ${active ? "ring-4 ring-indigo-400/50 z-10" : "hover:ring-2 hover:ring-indigo-300/50"}`}
            style={{ left: `${((x - pad) / w) * 100}%`, top: `${((y - pad) / h) * 100}%`, width: `${((bw + pad * 2) / w) * 100}%`, height: `${((bh + pad * 2) / h) * 100}%` }} />
  );
}
