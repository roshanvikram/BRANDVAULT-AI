"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Send, Loader2, CheckCircle2, XCircle, ArrowRight, KeyRound, ShieldCheck } from "lucide-react";
import { checkChannels, fetchWorkspaceSettings, ChannelReport } from "@/lib/api";
import { CARD, Badge, PageHeader, ErrorNote, BTN_PRIMARY, INPUT } from "@/components/engines/ui";

const REGIONS = [{ v: "IN", l: "India" }, { v: "US", l: "United States" }, { v: "", l: "Any region" }];

export default function PublishingPage() {
  const [channels, setChannels] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<string[]>(["x", "instagram"]);
  const [region, setRegion] = useState("IN");
  const [text, setText] = useState("");
  const [dims, setDims] = useState({ w: "", h: "" });
  const [report, setReport] = useState<ChannelReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkspaceSettings().then((d) => setChannels(Object.fromEntries(Object.entries(d.settings.channels).map(([k, v]) => [k, v.label])))).catch((e) => setError(e.message));
  }, []);

  const run = async () => {
    setBusy(true); setError(null);
    try {
      setReport(await checkChannels({ text, channels: selected, region: region || undefined,
        width: dims.w ? Number(dims.w) : undefined, height: dims.h ? Number(dims.h) : undefined }));
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };

  return (
    <div className="space-y-6">
      <PageHeader back={{ href: "/approval-hub", label: "Approval Hub" }} eyebrow="Publishing Gate" icon={<Send className="w-3.5 h-3.5" />}
        title="Ready for the channel — and allowed to go out?"
        description="Check copy against each channel's limits and the mandatory disclaimers for its region. When you publish from a CMS or CI pipeline, the publishing gate only lets through copy that exactly matches a current Brand Passport." />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-5 space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <label className="block text-xs text-slate-600">Copy to publish
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={6} className={`${INPUT} py-2.5 mt-1 resize-y`}
                        placeholder="Paste the post, ad or email subject…" /></label>
            <div className="text-[11px] text-slate-400 text-right tabular-nums">{text.length} characters</div>
            <div>
              <div className="text-xs text-slate-600 mb-1.5">Channels</div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(channels).map(([k, label]) => {
                  const on = selected.includes(k);
                  return <button key={k} onClick={() => setSelected(on ? selected.filter((x) => x !== k) : [...selected, k])}
                                 className={`h-8 px-3 rounded-lg text-xs font-medium ring-1 ${on ? "bg-indigo-50 text-indigo-700 ring-indigo-200" : "bg-white text-slate-500 ring-slate-200"}`}>{label}</button>;
                })}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <label className="text-xs text-slate-600">Region
                <select value={region} onChange={(e) => setRegion(e.target.value)} className={`${INPUT} h-9 mt-1`}>{REGIONS.map((r) => <option key={r.v} value={r.v}>{r.l}</option>)}</select></label>
              <label className="text-xs text-slate-600">Image width
                <input inputMode="numeric" value={dims.w} onChange={(e) => setDims({ ...dims, w: e.target.value.replace(/\D/g, "") })} placeholder="px" className={`${INPUT} h-9 mt-1`} /></label>
              <label className="text-xs text-slate-600">Image height
                <input inputMode="numeric" value={dims.h} onChange={(e) => setDims({ ...dims, h: e.target.value.replace(/\D/g, "") })} placeholder="px" className={`${INPUT} h-9 mt-1`} /></label>
            </div>
            <button onClick={run} disabled={busy || !text.trim() || !selected.length} className={BTN_PRIMARY + " w-full"}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Check channels & disclaimers
            </button>
            <ErrorNote message={error} />
            <p className="text-[11px] text-slate-500">Channel limits and disclaimer wordings are set by Administrators in <Link href="/settings" className="text-indigo-600">Settings</Link>.</p>
          </div>

          <div className={`${CARD} p-5 space-y-2`}>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-slate-400" /> How the publishing gate works</h3>
            <ol className="text-xs text-slate-600 space-y-1 list-decimal pl-4">
              <li>Your CMS or CI pipeline sends the exact copy to <span className="font-code">POST /api/v1/public/gate</span> with an API key.</li>
              <li>BrandVault compares it with every Brand Passport. Only an identical, current approved version returns <b>allowed: true</b>.</li>
              <li>Edited or never-approved copy is blocked, logged, and reviewers are notified.</li>
            </ol>
            <div className="flex flex-wrap gap-2 pt-1">
              <Link href="/settings" className="text-xs font-semibold text-indigo-600 inline-flex items-center gap-1"><KeyRound className="w-3.5 h-3.5" /> Create an API key</Link>
              <Link href="/brand-passport/verify" className="text-xs font-semibold text-indigo-600 inline-flex items-center gap-1">Try the same check by hand <ArrowRight className="w-3.5 h-3.5" /></Link>
            </div>
          </div>
        </div>

        <div className="xl:col-span-7 space-y-4">
          {!report ? (
            <div className={`${CARD} p-10 text-center text-[13px] text-slate-500`}>Paste copy and pick channels to see what each channel needs.</div>
          ) : (
            <>
              <div className={`rounded-2xl border px-5 py-4 flex items-center gap-3 ${report.ok ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}>
                {report.ok ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <XCircle className="w-5 h-5 text-amber-600" />}
                <div className="text-[13px]"><b>{report.ok ? "Fits every selected channel and disclaimer rule." : "Changes needed before publishing."}</b>
                  <span className="text-slate-600"> Brand and claim checks still run in Content Intelligence, and publishing still needs an approved passport.</span></div>
              </div>
              <div className={`${CARD} p-5`}>
                <h4 className="text-sm font-semibold text-slate-900">Channels</h4>
                <ul className="mt-2 space-y-2">
                  {report.channels.map((c) => (
                    <li key={c.channel} className="rounded-xl border border-slate-200 p-3">
                      <div className="flex items-center gap-2 text-[13px]"><Badge tone={c.ok ? "good" : "warn"}>{c.ok ? "OK" : "Fix"}</Badge><b>{c.label}</b>
                        {c.max_chars && <span className="ml-auto text-xs tabular-nums text-slate-500">{c.chars} / {c.max_chars}</span>}</div>
                      {c.max_chars ? <div className="mt-2 h-1.5 rounded-full bg-slate-100 overflow-hidden"><div className={`h-full rounded-full ${c.ok ? "bg-emerald-500" : "bg-amber-500"}`} style={{ width: `${Math.min(100, ((c.chars || 0) / c.max_chars) * 100)}%` }} /></div> : null}
                      {c.issues.map((i, k) => <p key={k} className="mt-1 text-xs text-amber-800">• {i}</p>)}
                    </li>
                  ))}
                </ul>
              </div>
              <div className={`${CARD} p-5`}>
                <h4 className="text-sm font-semibold text-slate-900">Mandatory disclaimers</h4>
                {report.disclaimers.length === 0 ? <p className="mt-1 text-[13px] text-slate-500">No disclaimer rule is triggered by this copy.</p> : (
                  <ul className="mt-2 space-y-2">
                    {report.disclaimers.map((d) => (
                      <li key={d.id} className="text-xs flex items-start gap-2"><Badge tone={d.ok ? "good" : "bad"}>{d.ok ? "Present" : "Missing"}</Badge>
                        <span><b className="text-slate-800">{d.label}</b>{d.ok ? <span className="text-slate-500"> — found “{d.present?.[0]}”</span> : <span className="text-rose-700"> — {d.issue}</span>}</span></li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
