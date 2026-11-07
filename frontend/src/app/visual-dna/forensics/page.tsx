"use client";

import { useEffect, useState } from "react";
import { ScanSearch, Upload, Loader2, Library, History, AlertOctagon, AlertTriangle, CheckCircle2, Info, ArrowRight } from "lucide-react";
import {
  fetchAssets, uploadBrandAsset, investigateAsset, fetchInvestigations, fetchInvestigation,
  BrandAssetOut, Investigation, ForensicMatch,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, Tone, PageHeader, ErrorNote, Loading, ProtectedImage, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const RISK_TONE: Record<string, Tone> = { high: "bad", medium: "warn", low: "good", none: "neutral" };
const RISK_LABEL: Record<string, string> = { high: "High risk", medium: "Medium risk", low: "Low risk", none: "No official asset found" };
const SEV = {
  high: { Icon: AlertOctagon, cls: "text-rose-600", box: "border-rose-200 bg-rose-50/40" },
  medium: { Icon: AlertTriangle, cls: "text-amber-600", box: "border-amber-200 bg-amber-50/40" },
  low: { Icon: CheckCircle2, cls: "text-emerald-600", box: "border-emerald-200 bg-emerald-50/40" },
  info: { Icon: Info, cls: "text-slate-500", box: "border-slate-200 bg-slate-50" },
};
const KINDS = ["logo", "product_image", "creative", "template", "illustration", "other"];

/** Uploaded image with the located logo outline drawn on top. */
function AnnotatedImage({ inv, match }: { inv: Investigation; match?: ForensicMatch }) {
  const poly = match?.logo_match?.polygon;
  return (
    <div className="relative w-full rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
      <ProtectedImage path={`/assets/investigations/${inv.id}/file`} alt={`Uploaded image ${inv.file_name}`} className="w-full h-auto block" />
      {poly && (
        <svg viewBox={`0 0 ${inv.width} ${inv.height}`} className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden>
          <polygon points={poly.map((p) => p.join(",")).join(" ")} fill="rgba(244,63,94,0.12)" stroke="#f43f5e"
                   strokeWidth={Math.max(2, inv.width / 300)} strokeDasharray={`${inv.width / 80} ${inv.width / 160}`} />
        </svg>
      )}
    </div>
  );
}

export default function ForensicsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const [tab, setTab] = useState<"investigate" | "library">("investigate");
  const [assets, setAssets] = useState<BrandAssetOut[] | null>(null);
  const [history, setHistory] = useState<Investigation[]>([]);
  const [inv, setInv] = useState<Investigation | null>(null);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<{ file: File | null; name: string; kind: string; version: string; supersedes: string }>(
    { file: null, name: "", kind: "logo", version: "v1", supersedes: "" });

  const loadAssets = () => fetchAssets().then(setAssets).catch((e) => setError(e.message));
  const loadHistory = () => fetchInvestigations().then(setHistory).catch(() => setHistory([]));
  useEffect(() => { loadAssets(); loadHistory(); }, []);

  const investigate = async (file: File) => {
    setBusy(true); setError(null);
    try { const r = await investigateAsset(file); setInv(r); setSelected(0); loadHistory(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  const open = async (id: string) => {
    setError(null);
    try { setInv(await fetchInvestigation(id)); setSelected(0); setTab("investigate"); } catch (e: any) { setError(e.message); }
  };
  const upload = async () => {
    if (!form.file) return;
    setBusy(true); setError(null);
    try {
      await uploadBrandAsset({ file: form.file, name: form.name.trim(), kind: form.kind, version_label: form.version.trim() || "v1", supersedes_id: form.supersedes || undefined });
      setForm({ file: null, name: "", kind: "logo", version: "v1", supersedes: "" });
      loadAssets();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };

  const match = inv?.matches?.[selected];
  const currentAssets = assets?.filter((a) => a.current).length || 0;

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/visual-dna", label: "Visual DNA" }}
        eyebrow="Brand Asset Forensics" icon={<ScanSearch className="w-3.5 h-3.5" />}
        title="Find official assets in any image — and how they were changed"
        description="Upload an ad, banner or social post. BrandVault locates your official logos and assets with computer vision and measures stretching, rotation, cropping, recolouring, outdated versions and near-duplicates. Similarity is evidence for review, not proof of misuse."
      />

      <div className="flex gap-2" role="tablist" aria-label="Forensics sections">
        {([["investigate", "Investigate an image", ScanSearch], ["library", `Asset Library (${assets?.length ?? "…"})`, Library]] as const).map(([k, label, Icon]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
                  className={`h-10 px-4 inline-flex items-center gap-2 rounded-xl text-[13px] font-semibold border transition-colors ${tab === k ? "bg-indigo-50 border-indigo-200 text-indigo-800" : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"}`}>
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>
      <ErrorNote message={error} />

      {tab === "investigate" && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          <div className="xl:col-span-4 space-y-4">
            <div className={`${CARD} p-5 space-y-3`}>
              <h3 className="text-sm font-bold text-slate-900">Upload an image to investigate</h3>
              <p className="text-xs text-slate-500">PNG, JPEG, WebP or BMP, up to 10 MB. Compared with {assets?.length ?? 0} asset(s) in your library ({currentAssets} current).</p>
              <label className={`flex flex-col items-center justify-center gap-2 h-36 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/40 transition-colors ${busy ? "opacity-60 pointer-events-none" : "cursor-pointer"}`}>
                {busy ? <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" /> : <Upload className="w-6 h-6 text-slate-400" />}
                <span className="text-[13px] font-medium text-slate-600">{busy ? "Analysing image…" : "Choose an image"}</span>
                <input type="file" accept="image/png,image/jpeg,image/webp,image/bmp" className="sr-only"
                       onChange={(e) => { const f = e.target.files?.[0]; if (f) investigate(f); e.target.value = ""; }} />
              </label>
              {assets && assets.length === 0 && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  Your Asset Library is empty, so there is nothing official to compare against. {isAdmin ? "Add your logo files in the Asset Library tab first." : "Ask an administrator to upload official logos."}
                </p>
              )}
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><History className="w-4 h-4 text-slate-400" /> Recent investigations</h3>
              {history.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">None yet.</p> : (
                <ul className="mt-2 divide-y divide-slate-100">
                  {history.slice(0, 10).map((h) => (
                    <li key={h.id}>
                      <button onClick={() => open(h.id)} className="w-full py-2.5 flex items-center justify-between gap-2 text-left group">
                        <div className="min-w-0">
                          <div className="text-[13px] font-medium text-slate-800 truncate group-hover:text-indigo-700">{h.file_name}</div>
                          <div className="text-[11px] text-slate-500 truncate">{h.summary}</div>
                        </div>
                        <Badge tone={RISK_TONE[h.risk]}>{h.risk}</Badge>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="xl:col-span-8 space-y-4">
            {!inv ? (
              <div className={`${CARD} p-10 text-center`}>
                <ScanSearch className="w-8 h-8 text-indigo-400 mx-auto" />
                <h3 className="mt-3 text-base font-bold text-slate-900">No investigation open</h3>
                <p className="mt-1 text-[13px] text-slate-500 max-w-md mx-auto">Upload an image to see the matched official asset side by side, the located logo region and every measured modification.</p>
              </div>
            ) : (
              <>
                <div className={`${CARD} p-5`}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-xs text-slate-500">{inv.file_name} · {inv.width}×{inv.height}{inv.elapsed_ms ? ` · analysed in ${Math.round(inv.elapsed_ms)} ms` : ""}</div>
                      <div className="text-[15px] font-bold text-slate-900">{inv.summary}</div>
                    </div>
                    <Badge tone={RISK_TONE[inv.risk]} className="text-xs px-2.5 py-1">{RISK_LABEL[inv.risk]}</Badge>
                  </div>
                  {inv.matches && inv.matches.length > 1 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {inv.matches.map((m, i) => (
                        <button key={i} onClick={() => setSelected(i)}
                                className={`h-8 px-3 rounded-lg text-xs font-semibold border ${i === selected ? "bg-indigo-50 border-indigo-200 text-indigo-800" : "bg-white border-slate-200 text-slate-600"}`}>
                          {m.asset_name} {m.version_label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className={`${CARD} p-4 space-y-2`}>
                    <div className="text-xs font-semibold text-slate-500">Uploaded image {match?.logo_match ? "· detected region outlined" : ""}</div>
                    <AnnotatedImage inv={inv} match={match} />
                  </div>
                  <div className={`${CARD} p-4 space-y-2`}>
                    <div className="text-xs font-semibold text-slate-500">
                      {match ? <>Matched official asset · {match.asset_name} {match.version_label} <Badge tone={match.current ? "good" : "neutral"}>{match.asset_status}</Badge></> : "No official asset matched"}
                    </div>
                    {match ? (
                      <div className="rounded-xl overflow-hidden border border-slate-200 bg-[repeating-conic-gradient(#f1f5f9_0%_25%,#fff_0%_50%)] bg-[length:16px_16px]">
                        <ProtectedImage path={`/assets/${match.asset_id}/file`} alt={`Official ${match.asset_name}`} className="w-full h-auto block" />
                      </div>
                    ) : <div className="h-40 rounded-xl bg-slate-50 border border-slate-200" />}
                    {match && (
                      <div className="text-[11px] text-slate-500">
                        Perceptual similarity {Math.round(match.similarity * 100)}%{match.identical_file ? " · identical file (SHA-256)" : ""}
                        {match.logo_match && ` · located by ${match.logo_match.method}, outline agreement ${Math.round(match.logo_match.verification * 100)}%`}
                      </div>
                    )}
                    {match?.replacement && (
                      <div className="text-xs text-indigo-700 inline-flex items-center gap-1">
                        <ArrowRight className="w-3.5 h-3.5" /> Use the current approved version: {match.replacement.name} {match.replacement.version_label}
                      </div>
                    )}
                  </div>
                </div>

                {match && (
                  <div className={`${CARD} p-5`}>
                    <h4 className="text-sm font-bold text-slate-900">Findings</h4>
                    {match.logo_match && (
                      <dl className="mt-3 grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                        {[["Rotation", `${match.logo_match.rotation_deg.toFixed(1)}°`],
                          ["Width scale", match.logo_match.scale_x.toFixed(2)],
                          ["Height scale", match.logo_match.scale_y.toFixed(2)],
                          ["Outside frame", `${Math.round(match.logo_match.out_of_frame * 100)}%`],
                          ["Colour ΔE", match.logo_match.delta_e === null ? "n/a" : match.logo_match.delta_e.toFixed(1)]].map(([k, v]) => (
                          <div key={k} className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2"><dt className="text-slate-400">{k}</dt><dd className="font-semibold text-slate-900 tabular-nums">{v}</dd></div>
                        ))}
                      </dl>
                    )}
                    <ul className="mt-3 space-y-2.5">
                      {match.findings.map((f, i) => {
                        const s = SEV[f.severity];
                        return (
                          <li key={i} className={`rounded-xl border p-3.5 ${s.box}`}>
                            <div className="flex items-start gap-2.5">
                              <s.Icon className={`w-4 h-4 mt-0.5 shrink-0 ${s.cls}`} aria-hidden />
                              <div className="min-w-0">
                                <div className="text-[13px] font-semibold text-slate-900">{f.title}</div>
                                <div className="text-xs text-slate-500 mt-0.5">Measured: {f.measurement} · confidence {Math.round(f.confidence * 100)}%</div>
                                <p className="text-xs text-slate-600 mt-1">{f.explanation}</p>
                                <p className="text-xs font-medium text-indigo-700 mt-1">→ {f.recommendation}</p>
                              </div>
                            </div>
                          </li>
                        );
                      })}
                      {match.findings.length === 0 && <li className="text-[13px] text-slate-500">Visually similar, but no specific modification was measured.</li>}
                    </ul>
                    {inv.note && <p className="mt-3 text-[11px] text-slate-400">{inv.note}</p>}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {tab === "library" && (
        <div className="space-y-4">
          {isAdmin && (
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Add an official asset</h3>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-6 gap-2">
                <label className={BTN_SECONDARY + " h-10 cursor-pointer md:col-span-2 truncate"}>
                  <Upload className="w-3.5 h-3.5" /> {form.file ? form.file.name : "Choose image"}
                  <input type="file" accept="image/png,image/jpeg,image/webp,image/bmp" className="sr-only" onChange={(e) => setForm({ ...form, file: e.target.files?.[0] || null })} />
                </label>
                <input aria-label="Asset name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name, e.g. Primary logo" className={`${INPUT} h-10 md:col-span-2`} />
                <select aria-label="Asset kind" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })} className={`${INPUT} h-10`}>
                  {KINDS.map((k) => <option key={k} value={k}>{k.replace("_", " ")}</option>)}
                </select>
                <input aria-label="Version" value={form.version} onChange={(e) => setForm({ ...form, version: e.target.value })} placeholder="v2" className={`${INPUT} h-10`} />
                <select aria-label="Supersedes" value={form.supersedes} onChange={(e) => setForm({ ...form, supersedes: e.target.value })} className={`${INPUT} h-10 md:col-span-4`}>
                  <option value="">Does not replace an existing asset</option>
                  {assets?.filter((a) => a.current).map((a) => <option key={a.id} value={a.id}>Replaces {a.name} {a.version_label} (it becomes superseded)</option>)}
                </select>
                <button onClick={upload} disabled={busy || !form.file || form.name.trim().length < 2} className={BTN_PRIMARY + " md:col-span-2"}>
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Upload as approved
                </button>
              </div>
            </div>
          )}
          {!assets ? <Loading /> : assets.length === 0 ? (
            <div className={`${CARD} p-8 text-center text-[13px] text-slate-500`}>No official assets yet.</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {assets.map((a) => (
                <div key={a.id} className={`${CARD} overflow-hidden ${a.current ? "" : "opacity-80"}`}>
                  <div className="aspect-video bg-[repeating-conic-gradient(#f1f5f9_0%_25%,#fff_0%_50%)] bg-[length:16px_16px] flex items-center justify-center">
                    <ProtectedImage path={`/assets/${a.id}/file`} alt={a.name} className="max-h-full max-w-full object-contain" />
                  </div>
                  <div className="p-3.5 space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-[13px] font-semibold text-slate-900 truncate">{a.name} <span className="text-slate-400 font-medium">{a.version_label}</span></div>
                      <Badge tone={a.current ? "good" : "neutral"}>{a.status}</Badge>
                    </div>
                    <div className="text-[11px] text-slate-500">{a.kind.replace("_", " ")} · {a.width}×{a.height}</div>
                    {a.colours?.dominant && (
                      <div className="flex gap-1" aria-label="Dominant colours">
                        {a.colours.dominant.slice(0, 5).map((c) => <span key={c.hex} title={`${c.hex} · ${Math.round(c.share * 100)}%`} className="w-4 h-4 rounded ring-1 ring-slate-200" style={{ background: c.hex }} />)}
                      </div>
                    )}
                    {a.replacement && <div className="text-[11px] text-indigo-700">Replaced by {a.replacement.version_label}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
