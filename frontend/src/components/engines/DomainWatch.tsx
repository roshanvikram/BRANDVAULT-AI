"use client";

import { useEffect, useState } from "react";
import { Radar, Loader2, ExternalLink } from "lucide-react";
import { fetchWatch, runWatchScan, setWatchStatus, WatchHit } from "@/lib/api";
import { CARD, Badge, Tone, BTN_PRIMARY, Loading } from "@/components/engines/ui";

const RISK: Record<string, Tone> = { high: "bad", medium: "warn", low: "neutral" };

/** New look-alike domains found in public Certificate Transparency logs. */
export function DomainWatch({ canDecide, onIncident }: { canDecide: boolean; onIncident?: () => void }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchWatch>> | null>(null);
  const [filter, setFilter] = useState<"new" | "all">("new");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = () => fetchWatch().then((d) => { setData(d); return d; });
  useEffect(() => { load().then((d) => { if (d.scan?.running) poll(); }).catch((e) => setMsg({ ok: false, text: e.message })); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  // The search runs on the server in the background (crt.sh can take minutes); check every 5 s.
  const poll = () => {
    setBusy(true);
    const tick = async () => {
      try {
        const d = await load();
        if (d.scan?.running) { setTimeout(tick, 5000); return; }
        const r = d.scan?.summary;
        if (r) {
          const text = r.errors.length && !r.certificates ? r.errors.join(" ")
            : `Searched ${r.terms.join(", ")} and similar spellings: ${r.certificates.toLocaleString()} certificates, ${r.domains_checked.toLocaleString()} domains checked, ${r.new_hits} new look-alike(s).`
              + (r.errors.length ? ` Some searches failed: ${r.errors.join("; ")}` : "");
          setMsg({ ok: !r.errors.length || r.certificates > 0, text });
        }
        setBusy(false);
      } catch (e: any) { setMsg({ ok: false, text: e.message }); setBusy(false); }
    };
    setTimeout(tick, 4000);
  };
  const scan = async () => {
    setBusy(true); setMsg(null);
    try { await runWatchScan(); poll(); }
    catch (e: any) { setMsg({ ok: false, text: e.message }); setBusy(false); }
  };
  const mark = async (h: WatchHit, status: "dismissed" | "incident" | "new") => {
    try { await setWatchStatus(h.id, status); if (status === "incident") onIncident?.(); load(); }
    catch (e: any) { setMsg({ ok: false, text: e.message }); }
  };

  if (!data) return <div className={`${CARD} p-5`}><Loading /></div>;
  const hits = data.hits.filter((h) => filter === "all" || h.status === "new");
  return (
    <div className={`${CARD} p-5`}>
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Radar className="w-4 h-4 text-slate-400" /> Look-alike domain watch</h3>
          <p className="text-xs text-slate-500 mt-0.5 max-w-3xl">
            Searches public Certificate Transparency logs (crt.sh) for new HTTPS sites using your names{data.terms.length ? <>: <b>{data.terms.join(", ")}</b></> : null}.
            Most phishing sites get a certificate, so they show up here within hours. Social media pages, ads and sites without HTTPS are not covered.
            {data.scan?.last_scan && <> Last search {new Date(data.scan.last_scan).toLocaleString()}.</>}
          </p>
        </div>
        {canDecide && <button onClick={scan} disabled={busy || !data.terms.length} className={BTN_PRIMARY}>{busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Radar className="w-4 h-4" />} {busy ? "Searching logs…" : "Search now"}</button>}
        {busy && <p className="basis-full text-[11.5px] text-slate-500">Searching in the background. This can take a few minutes; you can leave this page.</p>}
      </div>
      {!data.official_domains.length && <p className="text-xs text-amber-700 mt-2">Add your official domains above so the watch can tell your sites from look-alikes.</p>}
      {msg && <p className={`text-xs mt-2 ${msg.ok ? "text-emerald-700" : "text-rose-700"}`}>{msg.text}</p>}
      <div className="flex gap-2 mt-3 text-xs">
        {(["new", "all"] as const).map((f) => <button key={f} onClick={() => setFilter(f)} className={`h-7 px-2.5 rounded-lg ring-1 ${filter === f ? "bg-indigo-50 text-indigo-700 ring-indigo-200" : "bg-white text-slate-500 ring-slate-200"}`}>{f === "new" ? "To review" : "All"}</button>)}
      </div>
      {hits.length === 0 ? <p className="text-[13px] text-slate-500 mt-3">{data.hits.length ? "Nothing left to review." : "No look-alike domains found yet."}</p> : (
        <ul className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-2">
          {hits.slice(0, 60).map((h) => (
            <li key={h.id} className="rounded-xl border border-slate-200 bg-white/70 p-3">
              <div className="flex flex-wrap items-center gap-1.5">
                <b className="text-[13px] text-slate-900 break-all">{h.host}</b>
                <Badge tone={RISK[h.risk] || "neutral"}>{h.risk}</Badge>
                {h.status !== "new" && <Badge tone="neutral">{h.status === "incident" ? "incident opened" : "dismissed"}</Badge>}
              </div>
              <div className="text-[11.5px] text-slate-600 mt-1">{h.findings[0]?.title}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Certificate {h.not_before ? `issued ${new Date(h.not_before).toLocaleDateString()}` : ""} · {h.issuer.replace(/^.*O=([^,]+).*$/, "$1")}
                {h.cert_url && <> · <a href={h.cert_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline inline-flex items-center gap-0.5">record <ExternalLink className="w-3 h-3" /></a></>}
              </div>
              {canDecide && h.status === "new" && (
                <div className="flex gap-3 mt-2 text-[12px] font-medium">
                  <button onClick={() => mark(h, "incident")} className="text-indigo-700 hover:underline">Open incident</button>
                  <button onClick={() => mark(h, "dismissed")} className="text-slate-500 hover:underline">Not a threat</button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
