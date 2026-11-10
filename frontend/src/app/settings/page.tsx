"use client";

import { useEffect, useState } from "react";
import { Settings2, KeyRound, Webhook, Bell, Megaphone, Plug, Copy, Check, Trash2, Send, Loader2, Plus, ShieldCheck } from "lucide-react";
import {
  fetchWorkspaceSettings, saveWorkspaceSettings, WorkspaceSettings,
  fetchApiKeys, createApiKey, revokeApiKey, ApiKeyOut,
  fetchWebhooks, createWebhook, disableWebhook, testWebhook, WebhookOut, fetchDeliveries, DeliveryOut,
  API_BASE_URL, fetchCapabilities, Capabilities,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PushToggle } from "@/components/layout/PushToggle";
import { TeamPanel, SecurityPanel, PrivacyPanel, SystemPanel } from "@/components/settings/CompanyPanels";
import { CARD, Badge, PageHeader, ErrorNote, Loading, Segmented, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

type Tab = "workspace" | "team" | "security" | "privacy" | "system" | "channels" | "notifications" | "keys" | "webhooks" | "mcp";
const TABS: { value: Tab; label: string; admin?: boolean }[] = [
  { value: "workspace", label: "Workspace" }, { value: "team", label: "Team" }, { value: "security", label: "Security" },
  { value: "privacy", label: "Data & privacy" }, { value: "system", label: "System", admin: true },
  { value: "channels", label: "Channels & disclaimers" },
  { value: "notifications", label: "Notifications" }, { value: "keys", label: "API keys" },
  { value: "webhooks", label: "Webhooks" }, { value: "mcp", label: "MCP" },
];
const fmt = (s: string | null) => (s ? new Date(s.endsWith("Z") ? s : s + "Z").toLocaleString() : "—");

function CopyBox({ value, label }: { value: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <div className="rounded-xl bg-slate-900 text-slate-100 p-3 text-xs font-code flex items-start gap-2">
      <pre className="flex-1 whitespace-pre-wrap break-all">{value}</pre>
      <button aria-label={label || "Copy"} onClick={() => { navigator.clipboard?.writeText(value); setDone(true); setTimeout(() => setDone(false), 1500); }}
              className="p-1.5 rounded-lg hover:bg-white/10 shrink-0">{done ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}</button>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const [tab, setTab] = useState<Tab>("workspace");
  const [data, setData] = useState<{ settings: WorkspaceSettings; defaults: WorkspaceSettings; editable: boolean } | null>(null);
  const [draft, setDraft] = useState<WorkspaceSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchWorkspaceSettings().then((d) => { setData(d); setDraft(structuredClone(d.settings)); }).catch((e) => setError(e.message)); }, []);
  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("tab") as Tab | null;
    if (t && TABS.some((x) => x.value === t)) setTab(t);
  }, []);
  const tabs = TABS.filter((t) => !t.admin || isAdmin);

  const save = async (changes: Partial<WorkspaceSettings>) => {
    setSaving(true); setError(null); setNotice(null);
    try { const r = await saveWorkspaceSettings(changes); setData((d) => d && { ...d, settings: r.settings }); setDraft(structuredClone(r.settings)); setNotice("Saved."); }
    catch (e: any) { setError(e.message); } finally { setSaving(false); }
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Settings" icon={<Settings2 className="w-3.5 h-3.5" />} title="Workspace settings"
        description="Rules used by the engines, notifications and integrations for your organisation. Administrators can edit; everyone else sees the current values."
        actions={!isAdmin ? <Badge tone="neutral">Read-only for {user?.role}</Badge> : undefined} />
      <div className="overflow-x-auto"><Segmented label="Settings section" value={tab} options={tabs} onChange={(t) => { setTab(t); setNotice(null); setError(null); }} /></div>
      <ErrorNote message={error} />
      {notice && <div className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">{notice}</div>}

      {tab === "team" ? <TeamPanel /> : tab === "security" ? <SecurityPanel /> : tab === "privacy" ? <PrivacyPanel />
        : tab === "system" ? <SystemPanel /> : !draft ? <Loading /> : tab === "workspace" ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        <ServerEngines />
        <div className={`${CARD} p-5 space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900">Logo clear space</h3>
          <p className="text-xs text-slate-500">Empty space required around a logo, as a share of the logo&apos;s shorter side. Used by Creative Inspection.</p>
          <div className="flex items-center gap-3">
            <input type="range" min={0} max={1} step={0.05} disabled={!isAdmin} value={draft.logo_clear_space_ratio}
                   onChange={(e) => setDraft({ ...draft, logo_clear_space_ratio: Number(e.target.value) })} className="flex-1 accent-indigo-600" aria-label="Clear space ratio" />
            <span className="w-14 text-right text-sm font-semibold tabular-nums">{draft.logo_clear_space_ratio.toFixed(2)}×</span>
          </div>
          {isAdmin && <button disabled={saving} onClick={() => save({ logo_clear_space_ratio: draft.logo_clear_space_ratio })} className={BTN_PRIMARY}>{saving && <Loader2 className="w-4 h-4 animate-spin" />} Save</button>}
        </div>
        </div>
      ) : tab === "channels" ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Megaphone className="w-4 h-4 text-slate-400" /> Channel rules</h3>
            <p className="text-xs text-slate-500">Used by the Channel Adapter agent (Publishing page and the Check API).</p>
            <table className="w-full mt-3 text-[13px]">
              <thead className="text-[11px] text-slate-400"><tr><th className="text-left font-medium py-1">Channel</th><th className="text-left font-medium">Max characters</th><th className="text-left font-medium">Aspect ratios</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {Object.entries(draft.channels).map(([k, c]) => (
                  <tr key={k}>
                    <td className="py-2 text-slate-800">{c.label}</td>
                    <td><input type="number" min={1} disabled={!isAdmin} value={c.max_chars} aria-label={`${c.label} max characters`}
                               onChange={(e) => setDraft({ ...draft, channels: { ...draft.channels, [k]: { ...c, max_chars: Number(e.target.value) } } })}
                               className={`${INPUT} h-8 w-24`} /></td>
                    <td><input disabled={!isAdmin} value={c.aspect_ratios.join(", ")} aria-label={`${c.label} aspect ratios`}
                               onChange={(e) => setDraft({ ...draft, channels: { ...draft.channels, [k]: { ...c, aspect_ratios: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) } } })}
                               className={`${INPUT} h-8`} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {isAdmin && <button disabled={saving} onClick={() => save({ channels: draft.channels })} className={BTN_PRIMARY + " mt-3"}>Save channels</button>}
          </div>
          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-slate-400" /> Mandatory disclaimers</h3>
            <p className="text-xs text-slate-500">When the trigger pattern appears, at least one of the listed wordings must be present.</p>
            <ul className="mt-3 space-y-3">
              {draft.disclaimers.map((d, i) => (
                <li key={d.id} className="rounded-xl border border-slate-200 p-3 space-y-2">
                  <div className="flex items-center gap-2"><b className="text-[13px] text-slate-900">{d.label}</b><Badge tone="neutral">{d.region === "*" ? "all regions" : d.region}</Badge></div>
                  <label className="block text-[11px] text-slate-500">Trigger (regular expression)
                    <input disabled={!isAdmin} value={d.trigger} onChange={(e) => { const x = [...draft.disclaimers]; x[i] = { ...d, trigger: e.target.value }; setDraft({ ...draft, disclaimers: x }); }} className={`${INPUT} h-8 mt-0.5 font-code text-xs`} /></label>
                  <label className="block text-[11px] text-slate-500">Accepted wordings (comma separated)
                    <input disabled={!isAdmin} value={d.required_any.join(", ")} onChange={(e) => { const x = [...draft.disclaimers]; x[i] = { ...d, required_any: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }; setDraft({ ...draft, disclaimers: x }); }} className={`${INPUT} h-8 mt-0.5`} /></label>
                </li>
              ))}
            </ul>
            {isAdmin && <button disabled={saving} onClick={() => save({ disclaimers: draft.disclaimers })} className={BTN_PRIMARY + " mt-3"}>Save disclaimers</button>}
          </div>
        </div>
      ) : tab === "notifications" ? (
        <div className={`${CARD} p-5 max-w-2xl space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Bell className="w-4 h-4 text-slate-400" /> Notifications</h3>
          <p className="text-xs text-slate-500">In-app notifications are always on. Browser, Slack and email notifications are optional copies.</p>
          <PushToggle />
          <label className="block text-xs text-slate-600">Slack incoming-webhook URL
            <input disabled={!isAdmin} value={draft.notifications.slack_webhook_url} placeholder="https://hooks.slack.com/services/…"
                   onChange={(e) => setDraft({ ...draft, notifications: { ...draft.notifications, slack_webhook_url: e.target.value } })} className={`${INPUT} h-9 mt-1`} /></label>
          <label className="block text-xs text-slate-600">Email address
            <input disabled={!isAdmin} value={draft.notifications.email} placeholder="brand-team@company.com"
                   onChange={(e) => setDraft({ ...draft, notifications: { ...draft.notifications, email: e.target.value } })} className={`${INPUT} h-9 mt-1`} /></label>
          <p className="text-[11px] text-amber-700">Email is sent only when the server has SMTP settings (SMTP_HOST, SMTP_FROM). Otherwise each notification shows “email not configured”.</p>
          <div className="flex flex-wrap gap-2">
            {["analysis.completed", "review.decided", "passport.issued", "passport.superseded", "publish_gate.blocked", "incident.opened"].map((ev) => {
              const on = draft.notifications.events.includes(ev);
              return <button key={ev} disabled={!isAdmin} onClick={() => setDraft({ ...draft, notifications: { ...draft.notifications, events: on ? draft.notifications.events.filter((x) => x !== ev) : [...draft.notifications.events, ev] } })}
                             className={`h-8 px-3 rounded-lg text-xs font-medium ring-1 ${on ? "bg-indigo-50 text-indigo-700 ring-indigo-200" : "bg-white text-slate-500 ring-slate-200"}`}>{ev}</button>;
            })}
          </div>
          {isAdmin && <button disabled={saving} onClick={() => save({ notifications: draft.notifications })} className={BTN_PRIMARY}>Save notifications</button>}
        </div>
      ) : tab === "keys" ? <ApiKeys isAdmin={isAdmin} onError={setError} /> : tab === "webhooks" ? <Webhooks isAdmin={isAdmin} onError={setError} /> : <McpSetup />}
    </div>
  );
}

function ApiKeys({ isAdmin, onError }: { isAdmin: boolean; onError: (m: string | null) => void }) {
  const [keys, setKeys] = useState<ApiKeyOut[] | null>(null);
  const [name, setName] = useState("");
  const [created, setCreated] = useState<string | null>(null);
  const load = () => fetchApiKeys().then((r) => setKeys(r.keys)).catch((e) => onError(e.message));
  useEffect(() => { if (isAdmin) load(); }, [isAdmin]);
  if (!isAdmin) return <div className={`${CARD} p-5 text-[13px] text-slate-500`}>Only Administrators can manage API keys.</div>;
  return (
    <div className="space-y-4 max-w-3xl">
      <div className={`${CARD} p-5 space-y-3`}>
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><KeyRound className="w-4 h-4 text-slate-400" /> Create an API key</h3>
        <p className="text-xs text-slate-500">For CMS/CI scripts and the MCP server. Keys can check copy and query the publishing gate; they can never approve or publish.</p>
        <div className="flex gap-2">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Website CMS" className={`${INPUT} h-10`} aria-label="Key name" />
          <button disabled={name.trim().length < 2} onClick={async () => { try { const r = await createApiKey(name.trim(), ["check", "gate", "read"]); setCreated(r.key); setName(""); load(); } catch (e: any) { onError(e.message); } }} className={BTN_PRIMARY}><Plus className="w-4 h-4" /> Create</button>
        </div>
        {created && <div className="space-y-1.5"><p className="text-xs font-semibold text-amber-800">Copy this key now — it will not be shown again.</p><CopyBox value={created} label="Copy API key" /></div>}
      </div>
      <div className={`${CARD} overflow-hidden`}>
        {!keys ? <Loading /> : (
          <table className="w-full text-[13px]">
            <thead className="text-[11px] text-slate-400 border-b border-slate-100"><tr><th className="text-left font-medium px-4 py-2">Name</th><th className="text-left font-medium">Key</th><th className="text-left font-medium">Last used</th><th className="text-left font-medium">Uses</th><th /></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {keys.map((k) => (
                <tr key={k.id} className={k.revoked ? "text-slate-400" : ""}>
                  <td className="px-4 py-2.5 font-medium">{k.name}</td><td className="font-code text-xs">{k.prefix}…</td>
                  <td className="text-xs">{fmt(k.last_used_at)}</td><td className="tabular-nums">{k.use_count}</td>
                  <td className="pr-4 text-right">{k.revoked ? <Badge tone="neutral">Revoked</Badge> :
                    <button onClick={async () => { if (confirm(`Revoke “${k.name}”? Scripts using it will stop working.`)) { await revokeApiKey(k.id); load(); } }} className={BTN_SECONDARY}><Trash2 className="w-3.5 h-3.5" /> Revoke</button>}</td>
                </tr>
              ))}
              {keys.length === 0 && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">No API keys yet.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
      <div className={`${CARD} p-5 space-y-2`}>
        <h4 className="text-sm font-semibold text-slate-900">Example: block publishing unless approved</h4>
        <CopyBox value={`curl -s -X POST ${API_BASE_URL}/public/gate \\\n  -H "X-API-Key: $BRANDVAULT_API_KEY" -H "Content-Type: application/json" \\\n  -d '{"text": "<the exact copy you are about to publish>"}'\n# → {"allowed": true, "passport_number": "BV-2026-…"} only for approved copy`} />
        <CopyBox value={`curl -s -X POST ${API_BASE_URL}/public/check \\\n  -H "X-API-Key: $BRANDVAULT_API_KEY" -H "Content-Type: application/json" \\\n  -d '{"text": "Now only ₹69,999!", "channels": ["x"], "region": "IN", "persist": false}'`} />
      </div>
    </div>
  );
}

function Webhooks({ isAdmin, onError }: { isAdmin: boolean; onError: (m: string | null) => void }) {
  const [hooks, setHooks] = useState<WebhookOut[] | null>(null);
  const [eventsList, setEventsList] = useState<Record<string, string>>({});
  const [deliveries, setDeliveries] = useState<DeliveryOut[]>([]);
  const [url, setUrl] = useState("");
  const [secret, setSecret] = useState<string | null>(null);
  const load = () => { fetchWebhooks().then((r) => { setHooks(r.webhooks); setEventsList(r.events); }).catch((e) => onError(e.message)); fetchDeliveries().then(setDeliveries).catch(() => {}); };
  useEffect(() => { if (isAdmin) load(); }, [isAdmin]);
  if (!isAdmin) return <div className={`${CARD} p-5 text-[13px] text-slate-500`}>Only Administrators can manage webhooks.</div>;
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
      <div className="space-y-4">
        <div className={`${CARD} p-5 space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Webhook className="w-4 h-4 text-slate-400" /> Add a webhook</h3>
          <p className="text-xs text-slate-500">BrandVault POSTs signed JSON for every event: {Object.keys(eventsList).join(", ")}. Public HTTPS URLs only.</p>
          <div className="flex gap-2">
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/brandvault-hook" className={`${INPUT} h-10`} aria-label="Webhook URL" />
            <button disabled={url.trim().length < 8} onClick={async () => { try { const r = await createWebhook(url.trim(), Object.keys(eventsList)); setSecret(r.secret); setUrl(""); load(); } catch (e: any) { onError(e.message); } }} className={BTN_PRIMARY}><Plus className="w-4 h-4" /> Add</button>
          </div>
          {secret && <div className="space-y-1.5"><p className="text-xs font-semibold text-amber-800">Signing secret — copy it now.</p><CopyBox value={secret} label="Copy signing secret" />
            <p className="text-[11px] text-slate-500">Verify: <span className="font-code">X-BrandVault-Signature == "sha256=" + HMAC_SHA256(secret, timestamp + "." + body)</span> using the X-BrandVault-Timestamp header.</p></div>}
        </div>
        <div className={`${CARD} overflow-hidden`}>
          {!hooks ? <Loading /> : (
            <ul className="divide-y divide-slate-100">
              {hooks.map((h) => (
                <li key={h.id} className="px-4 py-3 flex items-center gap-2 text-[13px]">
                  <div className="min-w-0 flex-1"><div className="truncate font-medium">{h.url}</div><div className="text-[11px] text-slate-500">{h.events.length} event(s) · last {h.last_status || "—"}</div></div>
                  {h.active ? <>
                    <button onClick={async () => { await testWebhook(h.id); setTimeout(load, 1500); }} className={BTN_SECONDARY}><Send className="w-3.5 h-3.5" /> Test</button>
                    <button onClick={async () => { await disableWebhook(h.id); load(); }} className={BTN_SECONDARY} aria-label="Disable webhook"><Trash2 className="w-3.5 h-3.5" /></button>
                  </> : <Badge tone="neutral">Disabled</Badge>}
                </li>
              ))}
              {hooks.length === 0 && <li className="px-4 py-6 text-center text-[13px] text-slate-500">No webhooks yet.</li>}
            </ul>
          )}
        </div>
      </div>
      <div className={`${CARD} p-5`}>
        <h3 className="text-sm font-semibold text-slate-900">Delivery log</h3>
        <ul className="mt-2 divide-y divide-slate-100">
          {deliveries.map((d) => (
            <li key={d.id} className="py-2 text-xs flex items-start gap-2">
              <Badge tone={d.status === "delivered" ? "good" : d.status === "failed" ? "bad" : "neutral"}>{d.status}</Badge>
              <div className="min-w-0 flex-1"><b className="text-slate-800">{d.event}</b> · {d.attempts} attempt(s){d.status_code ? ` · HTTP ${d.status_code}` : ""}
                {d.error && <div className="text-rose-700 truncate">{d.error}</div>}</div>
              <span className="text-slate-400 shrink-0">{fmt(d.created_at)}</span>
            </li>
          ))}
          {deliveries.length === 0 && <li className="py-3 text-[13px] text-slate-500">No deliveries yet.</li>}
        </ul>
      </div>
    </div>
  );
}

function McpSetup() {
  const base = API_BASE_URL.replace(/\/api\/v1$/, "");
  return (
    <div className={`${CARD} p-5 max-w-3xl space-y-3`}>
      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Plug className="w-4 h-4 text-slate-400" /> Use BrandVault from AI assistants (MCP)</h3>
      <p className="text-xs text-slate-500">The MCP server in <span className="font-code">backend/mcp_server.py</span> exposes five read-only tools — get_brand_profile, search_brand_guidelines, check_copy, check_publish_gate, get_review_status — to Claude, Cursor or any MCP client. It uses an API key and cannot approve or publish.</p>
      <CopyBox value={`pip install "mcp>=2.3" httpx`} />
      <CopyBox value={JSON.stringify({ mcpServers: { brandvault: { command: "python", args: ["backend/mcp_server.py"], env: { BRANDVAULT_URL: base, BRANDVAULT_API_KEY: "bv_…" } } } }, null, 2)} />
    </div>
  );
}

function ServerEngines() {
  const [c, setC] = useState<Capabilities | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { fetchCapabilities().then(setC).catch((e) => setErr(e.message)); }, []);
  const row = (label: string, ok: boolean, detail: string) => (
    <li className="flex items-start justify-between gap-3 py-2 text-[13px]">
      <span className="text-slate-700">{label}</span>
      <span className="text-right"><Badge tone={ok ? "good" : "neutral"}>{ok ? "On" : "Off"}</Badge><span className="block text-[11px] text-slate-500 mt-0.5">{detail}</span></span>
    </li>
  );
  return (
    <div className={`${CARD} p-5`}>
      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-slate-400" /> Engines on this server</h3>
      <p className="text-xs text-slate-500">Measured live from the server, never assumed. The first check can take a few seconds while models load.</p>
      {err ? <ErrorNote message={err} /> : !c ? <Loading label="Checking engines…" /> : (
        <ul className="mt-2 divide-y divide-slate-100">
          {row("Database", true, c.database === "postgresql" ? `PostgreSQL${c.pgvector ? " + pgvector" : ""}` : "SQLite (local / demo)")}
          {row("Creative OCR", c.ocr.available, c.ocr.available ? c.ocr.engine || "" : c.ocr.reason || "not installed")}
          {row("Meaning-based evidence search", c.embeddings.available, c.embeddings.available ? `${c.embeddings.provider} · ${c.embeddings.dim} dims · ${c.retrieval_mode}` : c.embeddings.reason || "off")}
          {row("Email notifications", c.email_notifications, c.email_notifications ? "SMTP configured" : "SMTP not configured — in-app only")}
          {row("Demo sign-ins", c.demo_accounts, c.demo_accounts ? "Published demo accounts can sign in" : "Disabled")}
        </ul>
      )}
    </div>
  );
}
