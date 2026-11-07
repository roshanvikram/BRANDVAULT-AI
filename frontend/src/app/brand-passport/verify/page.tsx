"use client";

import { useEffect, useState } from "react";
import { Fingerprint, Loader2, ShieldCheck, Upload, History } from "lucide-react";
import { verifyCampaignIntegrity, fetchIntegrityChecks, IntegrityCheck, IntegrityResult } from "@/lib/api";
import { CARD, Badge, Tone, PageHeader, ErrorNote, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const RESULT_TONE: Record<IntegrityResult, Tone> = {
  "Verified Match": "good",
  "Modified After Approval": "bad",
  "Unknown Version": "warn",
  "New Unapproved Campaign": "warn",
  "Unable to Verify": "neutral",
};
const FP_LABELS: [string, string][] = [
  ["campaign_id", "Campaign ID"], ["brand_id", "Brand ID"], ["content_sha256", "Content SHA-256"],
  ["approved_version", "Approved version"], ["guideline_version", "Guideline version"],
  ["approval_reference", "Approval reference"], ["approver", "Approver"], ["timestamp", "Approved at"],
  ["revision_number", "Revision number"],
];

export default function CampaignIntegrityPage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<IntegrityCheck | null>(null);
  const [history, setHistory] = useState<IntegrityCheck[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = () => fetchIntegrityChecks().then(setHistory).catch(() => setHistory([]));
  useEffect(() => { loadHistory(); }, []);

  const run = async () => {
    setBusy(true); setError(null);
    try {
      setResult(await verifyCampaignIntegrity(file ? { file } : { text }));
      loadHistory();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };

  const fp = result?.details?.fingerprint as Record<string, unknown> | undefined;

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/brand-passport", label: "Brand Passport" }}
        eyebrow="Campaign DNA Fingerprint" icon={<Fingerprint className="w-3.5 h-3.5" />}
        title="Is this exactly what was approved?"
        description="Paste or upload a campaign to compare its SHA-256 fingerprint with every approved version. Spacing and line breaks are ignored; any change to the words is not. Every check is kept in an append-only log."
      />
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-5 space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <label htmlFor="ci-text" className="text-xs font-medium text-slate-600 block">Campaign text</label>
            <textarea id="ci-text" value={text} onChange={(e) => { setText(e.target.value); setFile(null); }} rows={7} disabled={!!file}
                      placeholder="Paste the campaign copy exactly as it will be published…" className={`${INPUT} py-3 resize-y leading-relaxed disabled:opacity-50`} />
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <label className={BTN_SECONDARY + " cursor-pointer"}>
                <Upload className="w-3.5 h-3.5" /> {file ? file.name : "Or upload a .txt / .md file"}
                <input type="file" accept=".txt,.md,text/plain,text/markdown,image/*" className="sr-only"
                       onChange={(e) => setFile(e.target.files?.[0] || null)} />
              </label>
              <button onClick={run} disabled={busy || (!file && !text.trim())} className={BTN_PRIMARY}>
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Verify integrity
              </button>
            </div>
            {file && <button onClick={() => setFile(null)} className="text-xs text-slate-500 hover:underline">Remove file</button>}
            <ErrorNote message={error} />
          </div>

          {result && (
            <div className={`${CARD} p-5 space-y-3`}>
              <div className="flex items-center justify-between gap-2">
                <Badge tone={RESULT_TONE[result.result]} className="text-xs px-2.5 py-1">{result.result}</Badge>
                {result.similarity !== null && result.result !== "Verified Match" && (
                  <span className="text-xs text-slate-500">Closest approved version: {Math.round(result.similarity * 100)}% similar</span>
                )}
              </div>
              <p className="text-[13px] text-slate-700">{result.explanation}</p>
              <div className="text-[11px] text-slate-500 break-all">Submitted SHA-256: <span className="font-code">{result.input_sha256}</span></div>
              {result.matched_passport_number && <div className="text-xs text-slate-600">Passport: <b>{result.matched_passport_number}</b></div>}
            </div>
          )}
        </div>

        <div className="xl:col-span-7 space-y-4">
          {result?.details?.diff && result.details.diff.length > 0 && (
            <div className={`${CARD} overflow-hidden`}>
              <div className="px-5 pt-4 pb-2 text-sm font-bold text-slate-900">What changed after approval</div>
              <table className="w-full text-[13px]">
                <thead><tr className="text-left text-xs text-slate-500 bg-slate-50/60 border-y border-slate-100">
                  <th className="px-5 py-2 font-medium">Approved</th><th className="px-3 py-2 font-medium">Submitted</th><th className="px-5 py-2 font-medium text-right">Change</th>
                </tr></thead>
                <tbody>
                  {result.details.diff.map((d, i) => (
                    <tr key={i} className="border-b border-slate-100 last:border-0">
                      <td className="px-5 py-2.5"><span className="bg-rose-50 text-rose-800 rounded px-1 line-through decoration-rose-300">{d.approved || "—"}</span></td>
                      <td className="px-3 py-2.5"><span className="bg-emerald-50 text-emerald-800 rounded px-1">{d.submitted || "—"}</span></td>
                      <td className="px-5 py-2.5 text-right text-xs text-slate-500">{d.change}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {fp && (
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Fingerprint className="w-4 h-4 text-indigo-500" /> Approved campaign fingerprint</h3>
              <dl className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5">
                {FP_LABELS.map(([k, label]) => (
                  <div key={k} className="min-w-0">
                    <dt className="text-[11px] text-slate-400">{label}</dt>
                    <dd className={`text-[13px] text-slate-800 truncate ${k.includes("sha") || k.endsWith("_id") || k === "approval_reference" ? "font-code text-xs" : ""}`} title={String(fp[k] ?? "")}>
                      {fp[k] === null || fp[k] === undefined || fp[k] === "" ? <span className="text-slate-400">not recorded</span> : String(fp[k])}
                    </dd>
                  </div>
                ))}
              </dl>
              {fp.reconstructed ? <p className="mt-3 text-[11px] text-amber-700">This passport predates fingerprint recording; fields were reconstructed from its stored snapshot.</p> : null}
            </div>
          )}

          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><History className="w-4 h-4 text-slate-400" /> Integrity log <span className="font-normal text-slate-400">(append-only)</span></h3>
            {history.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">No checks yet.</p> : (
              <ul className="mt-3 divide-y divide-slate-100">
                {history.slice(0, 15).map((h) => (
                  <li key={h.id} className="py-2.5 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-[13px] text-slate-800 truncate">{h.input_name || "Pasted text"} <span className="text-slate-400">· {h.checked_by}</span></div>
                      <div className="text-[11px] text-slate-500">{h.created_at ? new Date(h.created_at + "Z").toLocaleString() : ""}{h.matched_passport_number ? ` · ${h.matched_passport_number}` : ""}</div>
                    </div>
                    <Badge tone={RESULT_TONE[h.result]}>{h.result}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
