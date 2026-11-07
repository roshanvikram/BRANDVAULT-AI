"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, Loader2, Upload, Globe, Trash2, Plus, History } from "lucide-react";
import {
  investigateFraud, fetchIncidents, fetchIncident, setIncidentStatus, fetchOfficialDomains, addOfficialDomain, removeOfficialDomain,
  FraudIncident, IncidentStatus,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, Tone, PageHeader, ErrorNote, ProtectedImage, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const RISK: Record<string, Tone> = { high: "bad", medium: "warn", low: "good" };
const SEV: Record<string, Tone> = { high: "bad", medium: "warn", low: "neutral", info: "info" };
const STATUSES: IncidentStatus[] = ["Under Investigation", "Confirmed", "False Positive", "Resolved", "Escalated"];
const STATUS_TONE: Record<IncidentStatus, Tone> = { "Under Investigation": "ai", Confirmed: "bad", "False Positive": "neutral", Resolved: "good", Escalated: "warn" };

export default function FraudPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const canDecide = isAdmin || user?.role === "Reviewer";
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [incident, setIncident] = useState<FraudIncident | null>(null);
  const [list, setList] = useState<FraudIncident[]>([]);
  const [domains, setDomains] = useState<{ id: string; domain: string }[]>([]);
  const [newDomain, setNewDomain] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => { fetchIncidents().then(setList).catch(() => {}); fetchOfficialDomains().then(setDomains).catch(() => {}); };
  useEffect(load, []);

  const run = async () => {
    setBusy(true); setError(null);
    try { setIncident(await investigateFraud({ url: url.trim() || undefined, text: text.trim() || undefined, file: file || undefined })); load(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  const decide = async (s: IncidentStatus) => {
    if (!incident) return;
    try { setIncident(await setIncidentStatus(incident.id, s, note)); setNote(""); load(); } catch (e: any) { setError(e.message); }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/risk-radar", label: "Risk Radar" }}
        eyebrow="Brand Fraud Intelligence" icon={<ShieldAlert className="w-3.5 h-3.5" />}
        title="Investigate suspected impersonation"
        description="Check a reported link, page text or screenshot for look-alike domains, unauthorised prices, phishing requests, copied campaigns and misuse of your logo. Only what you submit is analysed — BrandVault does not monitor the internet. Findings stay “suspected” until a reviewer confirms them."
      />
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-5 space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <label className="block text-xs text-slate-600">Reported link
              <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" className={`${INPUT} h-10 mt-1`} />
            </label>
            <label className="block text-xs text-slate-600">Page or ad text (copy from the page)
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4} className={`${INPUT} py-2.5 mt-1 resize-y`} placeholder="Paste what the page says…" />
            </label>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className={BTN_SECONDARY + " cursor-pointer"}><Upload className="w-3.5 h-3.5" /> {file ? file.name : "Attach screenshot"}
                <input type="file" accept="image/png,image/jpeg,image/webp,image/bmp" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              </label>
              <button onClick={run} disabled={busy || !(url.trim() || text.trim() || file)} className={BTN_PRIMARY}>
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldAlert className="w-4 h-4" />} Investigate
              </button>
            </div>
            <ErrorNote message={error} />
          </div>

          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Globe className="w-4 h-4 text-slate-400" /> Official domains</h3>
            <p className="text-xs text-slate-500 mt-0.5">Look-alikes are measured against these.</p>
            <ul className="mt-2 space-y-1">
              {domains.map((d) => (
                <li key={d.id} className="flex items-center justify-between text-[13px] text-slate-700">
                  {d.domain}
                  {isAdmin && <button aria-label={`Remove ${d.domain}`} onClick={async () => setDomains(await removeOfficialDomain(d.id))} className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50"><Trash2 className="w-3.5 h-3.5" /></button>}
                </li>
              ))}
              {domains.length === 0 && <li className="text-xs text-amber-700">None registered yet{isAdmin ? " — add your real domains." : "."}</li>}
            </ul>
            {isAdmin && (
              <div className="mt-2 flex gap-2">
                <input aria-label="New official domain" value={newDomain} onChange={(e) => setNewDomain(e.target.value)} placeholder="example.com" className={`${INPUT} h-9`} />
                <button onClick={async () => { try { setDomains(await addOfficialDomain(newDomain)); setNewDomain(""); } catch (e: any) { setError(e.message); } }} disabled={newDomain.trim().length < 3} className={BTN_SECONDARY}><Plus className="w-3.5 h-3.5" /> Add</button>
              </div>
            )}
          </div>

          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><History className="w-4 h-4 text-slate-400" /> Incidents</h3>
            <ul className="mt-2 divide-y divide-slate-100">
              {list.map((i) => (
                <li key={i.id}>
                  <button onClick={async () => setIncident(await fetchIncident(i.id))} className="w-full py-2.5 text-left flex items-center justify-between gap-2">
                    <div className="min-w-0"><div className="text-[13px] font-medium text-slate-800">{i.number}</div><div className="text-[11px] text-slate-500 truncate">{i.source_url || i.detected_issue}</div></div>
                    <div className="flex gap-1 shrink-0"><Badge tone={RISK[i.risk]}>{i.risk}</Badge><Badge tone={STATUS_TONE[i.status]}>{i.status}</Badge></div>
                  </button>
                </li>
              ))}
              {list.length === 0 && <li className="py-3 text-[13px] text-slate-500">No incidents yet.</li>}
            </ul>
          </div>
        </div>

        <div className="xl:col-span-7 space-y-4">
          {!incident ? (
            <div className={`${CARD} p-10 text-center text-[13px] text-slate-500`}>Submit a link, text or screenshot to open an incident.</div>
          ) : (
            <>
              <div className={`${CARD} p-5`}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-xs text-slate-500">{incident.number} · {incident.source_kind} · {incident.created_at ? new Date(incident.created_at + "Z").toLocaleString() : ""}</div>
                    <h3 className="text-[15px] font-bold text-slate-900">{incident.detected_issue}</h3>
                    {incident.source_url && <div className="text-xs text-slate-500 break-all">{incident.source_url}</div>}
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge tone={RISK[incident.risk]} className="text-xs px-2.5 py-1">{incident.risk} risk · {Math.round(incident.confidence * 100)}%</Badge>
                    <Badge tone={STATUS_TONE[incident.status]}>{incident.status}</Badge>
                  </div>
                </div>
                <p className="mt-3 text-[13px] text-indigo-700">→ {incident.recommended_response}</p>
              </div>
              <div className={`${CARD} p-5`}>
                <h4 className="text-sm font-bold text-slate-900">Signals</h4>
                <ul className="mt-2 space-y-2">
                  {(incident.findings || []).map((f, i) => (
                    <li key={i} className="rounded-xl border border-slate-200 p-3">
                      <div className="flex flex-wrap items-center gap-1.5"><Badge tone={SEV[f.severity]}>{f.severity}</Badge><span className="text-[13px] font-semibold text-slate-900">{f.title}</span></div>
                      {f.evidence && <div className="mt-1 text-xs text-slate-500 break-words">{f.evidence}</div>}
                    </li>
                  ))}
                </ul>
              </div>
              {incident.has_evidence_file && (
                <div className={`${CARD} p-4`}>
                  <div className="text-xs font-semibold text-slate-500 mb-2">Preserved screenshot · SHA-256 <span className="font-code">{incident.evidence_sha256?.slice(0, 16)}…</span></div>
                  <ProtectedImage path={`/fraud/incidents/${incident.id}/evidence`} alt="Incident evidence" className="w-full h-auto rounded-xl border border-slate-200" />
                </div>
              )}
              <div className={`${CARD} p-5`}>
                <h4 className="text-sm font-bold text-slate-900">Investigation status</h4>
                {canDecide ? (
                  <div className="mt-2 space-y-2">
                    <input aria-label="Status note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (what you checked, who you contacted)" className={`${INPUT} h-9`} />
                    <div className="flex flex-wrap gap-2">
                      {STATUSES.filter((s) => s !== incident.status).map((s) => <button key={s} onClick={() => decide(s)} className={BTN_SECONDARY}>{s}</button>)}
                    </div>
                  </div>
                ) : <p className="mt-1 text-xs text-slate-500">A Reviewer or Administrator updates the status.</p>}
                <ul className="mt-3 space-y-1">
                  {(incident.history || []).map((h, i) => <li key={i} className="text-[11px] text-slate-500">{new Date(h.at).toLocaleString()} · <b className="text-slate-700">{h.status}</b> · {h.by}{h.note ? ` — ${h.note}` : ""}</li>)}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
