"use client";

import { useEffect, useState } from "react";
import { Copy as CopyIcon, Loader2, Search, Upload, EyeOff, RotateCcw, Layers } from "lucide-react";
import {
  checkSimilarity, fetchSimilarityClusters, dismissSimilarity, restoreSimilarity, checkImageSimilarity,
  SimilarityResult, ImageSimilarity,
} from "@/lib/api";
import { CARD, Badge, Tone, PageHeader, ErrorNote, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const LABEL_TONE: Record<string, Tone> = {
  "Exact duplicate": "bad", "Near-duplicate": "warn", "Reused tagline or sentence": "info", "Similar content": "neutral",
  "Identical file": "bad", "Near-duplicate image": "warn", "Visually similar": "neutral",
};
const KIND: Record<string, string> = { submission: "Campaign", passport: "Approved (passport)", translation_source: "Translation source", asset: "Brand asset", investigation: "Investigated image" };

export default function SimilarityPage() {
  const [text, setText] = useState("");
  const [showDismissed, setShowDismissed] = useState(false);
  const [result, setResult] = useState<SimilarityResult | null>(null);
  const [image, setImage] = useState<ImageSimilarity | null>(null);
  const [clusters, setClusters] = useState<Awaited<ReturnType<typeof fetchSimilarityClusters>>["clusters"]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState<Record<string, string>>({});

  useEffect(() => { fetchSimilarityClusters().then((r) => setClusters(r.clusters)).catch(() => {}); }, []);

  const run = async (include = showDismissed) => {
    if (!text.trim()) return;
    setBusy(true); setError(null); setImage(null);
    try { setResult(await checkSimilarity({ text, include_dismissed: include })); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  const runImage = async (f: File) => {
    setBusy(true); setError(null); setResult(null);
    try { setImage(await checkImageSimilarity(f)); } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };
  const dismiss = async (pk: string) => {
    try { await dismissSimilarity(pk, reason[pk] || "Marked as false positive"); run(); } catch (e: any) { setError(e.message); }
  };
  const restore = async (pk: string) => {
    try { await restoreSimilarity(pk); run(); } catch (e: any) { setError(e.message); }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/content-intelligence", label: "Content Intelligence" }}
        eyebrow="Content Similarity Detector" icon={<CopyIcon className="w-3.5 h-3.5" />}
        title="Has this already been written — or reused?"
        description="Compares copy with every campaign, approved passport and translation source in your workspace using exact hashes, wording overlap, vocabulary similarity and reused sentences. Images are compared by perceptual hash. Similarity is evidence, not a plagiarism ruling."
      />
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-5 space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <label htmlFor="sim-text" className="text-xs font-medium text-slate-600">Marketing copy, headline, tagline or caption</label>
            <textarea id="sim-text" value={text} onChange={(e) => setText(e.target.value)} rows={6} className={`${INPUT} py-3 resize-y`} placeholder="Paste text to compare…" />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className="inline-flex items-center gap-2 text-xs text-slate-600">
                <input type="checkbox" className="w-4 h-4 accent-indigo-600" checked={showDismissed} onChange={(e) => { setShowDismissed(e.target.checked); if (result) run(e.target.checked); }} />
                Show dismissed matches
              </label>
              <button onClick={() => run()} disabled={busy || !text.trim()} className={BTN_PRIMARY}>
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Find similar content
              </button>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <label className={BTN_SECONDARY + " cursor-pointer"}>
                <Upload className="w-3.5 h-3.5" /> Or compare an image
                <input type="file" accept="image/png,image/jpeg,image/webp,image/bmp" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; if (f) runImage(f); e.target.value = ""; }} />
              </label>
            </div>
            <ErrorNote message={error} />
          </div>
          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Layers className="w-4 h-4 text-slate-400" /> Repeated campaigns</h3>
            {clusters.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">No groups of near-identical campaigns.</p> : (
              <ul className="mt-2 space-y-2">
                {clusters.slice(0, 6).map((c, i) => (
                  <li key={i} className="rounded-xl border border-slate-200 p-3">
                    <div className="flex items-center gap-2"><Badge tone={c.exact_duplicates ? "bad" : "warn"}>{c.size} campaigns</Badge><span className="text-[11px] text-slate-500">{c.exact_duplicates ? "identical text" : "near-identical"}</span></div>
                    <p className="mt-1 text-xs text-slate-700 line-clamp-2">“{c.representative}”</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="xl:col-span-7 space-y-3">
          {!result && !image && (
            <div className={`${CARD} p-10 text-center text-[13px] text-slate-500`}>Paste copy or choose an image to see similar existing content.</div>
          )}
          {image && (
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">{image.matches.length} similar image(s) of {image.compared} compared</h3>
              <ul className="mt-3 divide-y divide-slate-100">
                {image.matches.map((m) => (
                  <li key={m.kind + m.id} className="py-2.5 flex items-center justify-between gap-2">
                    <div><div className="text-[13px] font-medium text-slate-800">{m.title}</div><div className="text-[11px] text-slate-500">{KIND[m.kind]} · hash distance {m.phash_distance}/64</div></div>
                    <Badge tone={LABEL_TONE[m.label]}>{m.label}</Badge>
                  </li>
                ))}
                {image.matches.length === 0 && <li className="py-3 text-[13px] text-slate-500">No similar images.</li>}
              </ul>
              <p className="mt-2 text-[11px] text-slate-400">{image.note}</p>
            </div>
          )}
          {result && (
            <>
              <div className="text-xs text-slate-500">{result.matches.length} match(es) among {result.compared} item(s). {result.note}</div>
              {result.matches.length === 0 && <div className={`${CARD} p-8 text-center text-[13px] text-slate-500`}>Nothing similar found.</div>}
              {result.matches.map((m) => (
                <div key={m.pair_key} className={`${CARD} p-4 ${m.dismissed ? "opacity-60" : ""}`}>
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-1.5"><Badge tone={LABEL_TONE[m.label]}>{m.label}</Badge><span className="text-xs text-slate-500">{KIND[m.kind] || m.kind} · {m.status}</span>{m.dismissed && <Badge tone="neutral">dismissed</Badge>}</div>
                      <div className="mt-1 text-[13px] font-semibold text-slate-900 truncate">{m.title}</div>
                      <div className="text-[11px] text-slate-500">{m.date ? new Date(m.date + "Z").toLocaleDateString() : ""}{m.author ? ` · ${m.author}` : ""}</div>
                    </div>
                    <div className="text-right text-[11px] text-slate-500 tabular-nums">
                      <div className="text-lg font-bold text-slate-900">{Math.round(m.similarity * 100)}%</div>
                      words {Math.round(m.methods.shingle_jaccard * 100)}% · vocab {Math.round(m.methods.tfidf_cosine * 100)}%
                    </div>
                  </div>
                  {m.matching_sentences.length > 0 && (
                    <ul className="mt-2 space-y-1">{m.matching_sentences.map((s, i) => <li key={i} className="text-xs text-slate-700 bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-1.5">“{s.existing}”</li>)}</ul>
                  )}
                  {!m.matching_sentences.length && <p className="mt-2 text-xs text-slate-500 line-clamp-2">“{m.excerpt}”</p>}
                  <p className="mt-2 text-xs text-indigo-700">→ {m.recommendation}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {m.dismissed ? (
                      <><span className="text-[11px] text-slate-500">Reason: {m.dismissed_reason}</span><button onClick={() => restore(m.pair_key)} className={BTN_SECONDARY}><RotateCcw className="w-3.5 h-3.5" /> Restore</button></>
                    ) : (
                      <>
                        <input aria-label="Reason for dismissing" value={reason[m.pair_key] || ""} onChange={(e) => setReason({ ...reason, [m.pair_key]: e.target.value })} placeholder="Why is this a false positive?" className={`${INPUT} h-9 max-w-xs text-xs`} />
                        <button onClick={() => dismiss(m.pair_key)} className={BTN_SECONDARY}><EyeOff className="w-3.5 h-3.5" /> Dismiss</button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
