"use client";

import { useEffect, useState } from "react";
import { Users, UserPlus, ShieldCheck, KeyRound, LogOut, Download, Trash2, Activity, Loader2, Copy, Check, Unlock, AlertTriangle, Database, Cpu } from "lucide-react";
import {
  fetchTeam, updateMember, unlockMember, fetchInvites, createInvite, revokeInvite, fetchSecurityLog,
  TeamMember, TeamInvite, SecurityEventOut,
  changePassword, signOutEverywhere, startMfaSetup, enableMfa, disableMfa,
  fetchPrivacySummary, downloadWorkspaceExport, deleteMyAccount, deleteWorkspace,
  fetchSystemStatus, SystemStatus, clearToken,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useOrganization } from "@/lib/useOrganization";
import { CARD, Badge, Loading, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const ROLES = ["Creator", "Reviewer", "Administrator"];
const when = (s: string | null | undefined) => (s ? new Date(s.endsWith("Z") ? s : s + "Z").toLocaleString() : "never");

function Msg({ ok, text }: { ok?: boolean; text: string | null }) {
  if (!text) return null;
  return <p className={`text-xs mt-2 ${ok ? "text-emerald-700" : "text-rose-700"}`}>{text}</p>;
}

function CopyLine({ value }: { value: string }) {
  const [done, setDone] = useState(false);
  return (
    <div className="flex items-center gap-2 rounded-lg bg-slate-900 text-slate-100 px-3 py-2 text-xs font-code">
      <span className="flex-1 break-all">{value}</span>
      <button aria-label="Copy" onClick={() => { navigator.clipboard?.writeText(value); setDone(true); setTimeout(() => setDone(false), 1500); }}
              className="p-1 rounded hover:bg-white/10 shrink-0">{done ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}</button>
    </div>
  );
}

// ------------------------------------------------------------------- team
export function TeamPanel() {
  const { user } = useAuth();
  const [team, setTeam] = useState<{ members: TeamMember[]; can_manage: boolean } | null>(null);
  const [invites, setInvites] = useState<{ invites: TeamInvite[]; email_configured: boolean } | null>(null);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("Creator");
  const [link, setLink] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    fetchTeam().then((t) => { setTeam(t); if (t.can_manage) fetchInvites().then(setInvites).catch(() => {}); })
      .catch((e) => setMsg({ ok: false, text: e.message }));
  };
  useEffect(load, []);

  const act = async (fn: () => Promise<unknown>, ok?: string) => {
    setBusy(true); setMsg(null);
    try { await fn(); if (ok) setMsg({ ok: true, text: ok }); load(); }
    catch (e: any) { setMsg({ ok: false, text: e.message }); } finally { setBusy(false); }
  };

  const invite = () => act(async () => {
    const r = await createInvite(email.trim(), role);
    setLink(r.link); setEmail("");
  }, "Invitation created.");

  if (!team) return <Loading />;
  const manage = team.can_manage;
  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-4 items-start">
      <div className={`${CARD} p-5`}>
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Users className="w-4 h-4 text-slate-400" /> Members ({team.members.length})</h3>
        <p className="text-xs text-slate-500">Changing someone&apos;s role or turning their access off signs them out on every device.</p>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-[13px] min-w-[560px]">
            <thead className="text-[11px] text-slate-400"><tr><th className="text-left font-medium py-1">Person</th><th className="text-left font-medium">Role</th><th className="text-left font-medium">Two-step</th><th className="text-left font-medium">Last sign-in</th><th /></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {team.members.map((m) => (
                <tr key={m.id} className={m.active ? "" : "opacity-60"}>
                  <td className="py-2"><div className="font-medium text-slate-900">{m.full_name}{m.id === user?.id && <span className="text-slate-400 font-normal"> (you)</span>}</div><div className="text-[11.5px] text-slate-500">{m.email}</div></td>
                  <td>{manage ? (
                    <select aria-label={`Role for ${m.email}`} disabled={busy} value={m.role} onChange={(e) => act(() => updateMember(m.id, { role: e.target.value }), "Role changed.")}
                            className={`${INPUT} h-8 w-36`}>{ROLES.map((r) => <option key={r}>{r}</option>)}</select>
                  ) : <Badge tone="neutral">{m.role}</Badge>}</td>
                  <td>{m.mfa_enabled ? <Badge tone="good">On</Badge> : <Badge tone="neutral">Off</Badge>}</td>
                  <td className="text-[12px] text-slate-500">{when(m.last_login_at)}</td>
                  <td className="text-right whitespace-nowrap">
                    {manage && m.id !== user?.id && (
                      <>
                        <button disabled={busy} title="Clear a sign-in lockout" aria-label={`Unlock ${m.email}`} onClick={() => act(() => unlockMember(m.id), "Lockout cleared.")} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"><Unlock className="w-3.5 h-3.5" /></button>
                        <button disabled={busy} onClick={() => act(() => updateMember(m.id, { active: !m.active }), m.active ? "Access turned off." : "Access turned on.")}
                                className="text-[12px] font-medium text-indigo-700 hover:underline ml-1">{m.active ? "Turn off" : "Turn on"}</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {msg && <Msg ok={msg.ok} text={msg.text} />}
      </div>

      {manage ? (
        <div className="space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><UserPlus className="w-4 h-4 text-slate-400" /> Invite someone</h3>
            <div className="flex flex-col sm:flex-row gap-2">
              <input aria-label="Email to invite" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="colleague@company.com" className={`${INPUT} h-9 flex-1`} />
              <select aria-label="Role" value={role} onChange={(e) => setRole(e.target.value)} className={`${INPUT} h-9 sm:w-36`}>{ROLES.map((r) => <option key={r}>{r}</option>)}</select>
            </div>
            <button disabled={busy || !email.includes("@")} onClick={invite} className={BTN_PRIMARY}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Create invitation</button>
            {link && (
              <div className="space-y-1.5">
                <p className="text-[11.5px] text-slate-600">{invites?.email_configured ? "We emailed this link. You can also share it directly:" : "Email is not set up on the server, so share this link with them yourself. It is shown only once."}</p>
                <CopyLine value={link} />
              </div>
            )}
          </div>
          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-semibold text-slate-900">Invitations</h3>
            {!invites ? <Loading /> : invites.invites.length === 0 ? <p className="text-xs text-slate-500 mt-1">No invitations yet.</p> : (
              <ul className="mt-2 divide-y divide-slate-100">
                {invites.invites.slice(0, 20).map((i) => (
                  <li key={i.id} className="py-2 flex items-center gap-2 text-[12.5px]">
                    <span className="flex-1 min-w-0"><span className="text-slate-900 break-all">{i.email}</span> <span className="text-slate-400">· {i.role}</span></span>
                    <Badge tone={i.status === "accepted" ? "good" : i.status === "pending" ? "info" : "neutral"}>{i.status}</Badge>
                    {i.status === "pending" && <button disabled={busy} onClick={() => act(() => revokeInvite(i.id), "Invitation cancelled.")} className="text-[12px] text-indigo-700 hover:underline">Cancel</button>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : <div className={`${CARD} p-5 text-xs text-slate-500`}>Only Administrators can invite people or change roles.</div>}
    </div>
  );
}

// --------------------------------------------------------------- security
export function SecurityPanel() {
  const { user, setUser } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const google = user?.auth_provider === "google";
  const [cur, setCur] = useState(""); const [next, setNext] = useState(""); const [next2, setNext2] = useState("");
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState(""); const [offPw, setOffPw] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<SecurityEventOut[] | null>(null);

  useEffect(() => { if (isAdmin) fetchSecurityLog().then((r) => setLog(r.events)).catch(() => setLog([])); }, [isAdmin]);

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setBusy(true); setMsg(null);
    try { await fn(); setMsg({ ok: true, text: ok }); } catch (e: any) { setMsg({ ok: false, text: e.message }); } finally { setBusy(false); }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
      <div className="space-y-4">
        <div className={`${CARD} p-5 space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-slate-400" /> Two-step sign-in</h3>
          {user?.mfa_enabled ? (
            <>
              <p className="text-xs text-slate-600"><Badge tone="good">On</Badge> Signing in needs your password and a code from your authenticator app.</p>
              <div className="flex flex-col sm:flex-row gap-2">
                <input aria-label="Current code" inputMode="numeric" value={code} onChange={(e) => setCode(e.target.value)} placeholder="Current 6-digit code" className={`${INPUT} h-9`} />
                {!google && <input aria-label="Password" type="password" value={offPw} onChange={(e) => setOffPw(e.target.value)} placeholder="Password" className={`${INPUT} h-9`} />}
              </div>
              <button disabled={busy || code.length < 6} onClick={() => run(async () => { setUser(await disableMfa(code.trim(), offPw)); setCode(""); setOffPw(""); }, "Two-step sign-in is off.")} className={BTN_SECONDARY}>Turn off</button>
            </>
          ) : !setup ? (
            <>
              <p className="text-xs text-slate-600">Protect your account with a code from an authenticator app (Google Authenticator, Microsoft Authenticator, 1Password and others).</p>
              <button disabled={busy} onClick={() => run(async () => setSetup(await startMfaSetup()), "Add the key below to your app.")} className={BTN_PRIMARY}>Set up</button>
            </>
          ) : (
            <>
              <ol className="text-xs text-slate-600 list-decimal pl-4 space-y-1">
                <li>In your authenticator app, add an account and choose <b>enter a setup key</b>.</li>
                <li>Enter this key (time-based):</li>
              </ol>
              <CopyLine value={setup.secret.replace(/(.{4})/g, "$1 ").trim()} />
              <p className="text-[11.5px] text-slate-500">On a phone with the app installed, you can <a href={setup.otpauth_uri} className="text-indigo-600 underline">open it directly</a>.</p>
              <div className="flex gap-2">
                <input aria-label="Code from the app" inputMode="numeric" value={code} onChange={(e) => setCode(e.target.value)} placeholder="6-digit code from the app" className={`${INPUT} h-9`} />
                <button disabled={busy || code.replace(/\s/g, "").length !== 6} onClick={() => run(async () => { setUser(await enableMfa(code.replace(/\s/g, ""))); setSetup(null); setCode(""); }, "Two-step sign-in is on. Other devices must sign in again.")} className={BTN_PRIMARY}>Confirm</button>
              </div>
            </>
          )}
        </div>

        <div className={`${CARD} p-5 space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><KeyRound className="w-4 h-4 text-slate-400" /> Password</h3>
          {google ? <p className="text-xs text-slate-500">You sign in with Google, so there is no BrandVault password to change.</p> : (
            <>
              <input aria-label="Current password" type="password" value={cur} onChange={(e) => setCur(e.target.value)} placeholder="Current password" autoComplete="current-password" className={`${INPUT} h-9`} />
              <input aria-label="New password" type="password" value={next} onChange={(e) => setNext(e.target.value)} placeholder="New password (10+ characters, letters and numbers)" autoComplete="new-password" className={`${INPUT} h-9`} />
              <input aria-label="Repeat new password" type="password" value={next2} onChange={(e) => setNext2(e.target.value)} placeholder="Repeat new password" autoComplete="new-password" className={`${INPUT} h-9`} />
              <button disabled={busy || !cur || next.length < 10 || next !== next2} onClick={() => run(async () => { setUser(await changePassword(cur, next)); setCur(""); setNext(""); setNext2(""); }, "Password changed. Other devices were signed out.")} className={BTN_PRIMARY}>Change password</button>
            </>
          )}
        </div>

        <div className={`${CARD} p-5 space-y-2`}>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><LogOut className="w-4 h-4 text-slate-400" /> Sessions</h3>
          <p className="text-xs text-slate-600">Lost a laptop or signed in on a shared computer? End every other session. This one stays signed in.</p>
          <button disabled={busy} onClick={() => run(async () => setUser(await signOutEverywhere()), "Every other session was signed out.")} className={BTN_SECONDARY}>Sign out everywhere else</button>
        </div>
        {msg && <Msg ok={msg.ok} text={msg.text} />}
      </div>

      <div className={`${CARD} p-5`}>
        <h3 className="text-sm font-semibold text-slate-900">Security log</h3>
        {!isAdmin ? <p className="text-xs text-slate-500 mt-1">Administrators can see the workspace&apos;s sign-ins, lockouts, role changes, exports and deletions.</p>
          : !log ? <Loading /> : log.length === 0 ? <p className="text-xs text-slate-500 mt-1">No events yet.</p> : (
            <ul className="mt-2 divide-y divide-slate-100 max-h-[560px] overflow-y-auto">
              {log.map((e) => (
                <li key={e.id} className="py-2 text-[12.5px]">
                  <div className="flex items-center gap-2"><Badge tone={/failed|locked/.test(e.action) ? "bad" : /deleted|disabled|revoked/.test(e.action) ? "warn" : "neutral"}>{e.action}</Badge>
                    <span className="text-slate-400 text-[11.5px] ml-auto">{when(e.created_at)}</span></div>
                  <div className="text-slate-600 mt-0.5 break-all">{e.actor}{e.target ? ` → ${e.target}` : ""}{e.ip ? <span className="text-slate-400"> · {e.ip}</span> : null}</div>
                </li>
              ))}
            </ul>
          )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- privacy
export function PrivacyPanel() {
  const { user, logout } = useAuth();
  const org = useOrganization();
  const isAdmin = user?.role === "Administrator";
  const [summary, setSummary] = useState<{ tables: Record<string, number>; total_records: number; demo_workspace: boolean } | null>(null);
  const [files, setFiles] = useState(true);
  const [pw, setPw] = useState(""); const [wsName, setWsName] = useState(""); const [wsPw, setWsPw] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (isAdmin) fetchPrivacySummary().then(setSummary).catch(() => {}); }, [isAdmin]);

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    setBusy(true); setMsg(null);
    try { await fn(); if (ok) setMsg({ ok: true, text: ok }); } catch (e: any) { setMsg({ ok: false, text: e.message }); } finally { setBusy(false); }
  };
  const leave = () => { clearToken(); logout(); window.location.href = "/"; };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
      {isAdmin && (
        <div className={`${CARD} p-5 space-y-3`}>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Download className="w-4 h-4 text-slate-400" /> Export workspace data</h3>
          <p className="text-xs text-slate-600">A ZIP with every record your workspace holds{summary ? ` (${summary.total_records.toLocaleString()} records)` : ""} as JSON, plus uploaded files. Use it for data requests, audits or moving away. Passwords and secret keys are never included.</p>
          <label className="flex items-center gap-2 text-xs text-slate-600"><input type="checkbox" checked={files} onChange={(e) => setFiles(e.target.checked)} className="accent-indigo-600" /> Include uploaded files</label>
          <button disabled={busy} onClick={() => run(() => downloadWorkspaceExport(files), "Export downloaded.")} className={BTN_PRIMARY}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Download export</button>
        </div>
      )}

      <div className={`${CARD} p-5 space-y-3`}>
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Trash2 className="w-4 h-4 text-slate-400" /> Close my account</h3>
        <p className="text-xs text-slate-600">Removes your name, email and sign-in. Reviews and approvals you made stay in the workspace&apos;s records as &ldquo;Deleted user&rdquo;. This cannot be undone.</p>
        {user?.auth_provider !== "google" && <input aria-label="Password to confirm" type="password" value={pw} onChange={(e) => setPw(e.target.value)} placeholder="Your password" className={`${INPUT} h-9`} />}
        <button disabled={busy || (user?.auth_provider !== "google" && !pw)}
                onClick={() => { if (window.confirm("Close your account permanently?")) run(async () => { await deleteMyAccount(pw); leave(); }); }}
                className={BTN_SECONDARY + " text-rose-700"}>Close my account</button>
      </div>

      {isAdmin && (
        <div className={`${CARD} p-5 space-y-3 border-rose-200`}>
          <h3 className="text-sm font-semibold text-rose-800 flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Delete the whole workspace</h3>
          {summary?.demo_workspace ? <p className="text-xs text-slate-500">The shared demo workspace cannot be deleted.</p> : (
            <>
              <p className="text-xs text-slate-600">Permanently erases every member, guideline, check, approval, passport and file in <b>{org?.name || "this workspace"}</b>. Download an export first. This cannot be undone.</p>
              <input aria-label="Workspace name" value={wsName} onChange={(e) => setWsName(e.target.value)} placeholder={`Type ${org?.name || "the workspace name"} to confirm`} className={`${INPUT} h-9`} />
              {user?.auth_provider !== "google" && <input aria-label="Your password" type="password" value={wsPw} onChange={(e) => setWsPw(e.target.value)} placeholder="Your password" className={`${INPUT} h-9`} />}
              <button disabled={busy || !org || wsName !== org.name}
                      onClick={() => run(async () => { await deleteWorkspace(wsName, wsPw); leave(); })}
                      className="inline-flex items-center gap-2 h-9 px-4 rounded-xl text-sm font-semibold bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50">Delete workspace forever</button>
            </>
          )}
        </div>
      )}
      {msg && <div className="xl:col-span-2"><Msg ok={msg.ok} text={msg.text} /></div>}
    </div>
  );
}

// ----------------------------------------------------------------- system
export function SystemPanel() {
  const [s, setS] = useState<SystemStatus | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const load = () => fetchSystemStatus().then(setS).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <Msg text={err} />;
  if (!s) return <Loading />;
  const t = s.traffic;
  const up = t.uptime_seconds > 3600 ? `${Math.floor(t.uptime_seconds / 3600)} h ${Math.floor((t.uptime_seconds % 3600) / 60)} min` : `${Math.floor(t.uptime_seconds / 60)} min`;
  const stat = (label: string, value: React.ReactNode, tone?: string) => (
    <div className="rounded-xl bg-white/70 border border-slate-200 px-3 py-2.5"><div className="text-[11px] text-slate-500">{label}</div><div className={`text-lg font-semibold tabular-nums ${tone || "text-slate-900"}`}>{value}</div></div>
  );
  return (
    <div className="space-y-4">
      <div className={`${CARD} p-5`}>
        <div className="flex items-center gap-2"><h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Activity className="w-4 h-4 text-slate-400" /> Service since last restart ({up})</h3>
          <button onClick={load} className={BTN_SECONDARY + " ml-auto"}>Refresh</button></div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-3">
          {stat("Requests", t.requests.toLocaleString())}
          {stat("Server errors", t.server_errors, t.server_errors ? "text-rose-600" : "text-emerald-600")}
          {stat("Median response", t.latency_ms.p50 != null ? `${t.latency_ms.p50} ms` : "—")}
          {stat("95% under", t.latency_ms.p95 != null ? `${t.latency_ms.p95} ms` : "—")}
          {stat("Error rate", `${(t.error_rate * 100).toFixed(2)}%`)}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 text-[12.5px]">
          <div className="flex items-start gap-2"><Database className="w-4 h-4 text-slate-400 mt-0.5" /><span>Database <b>{s.database.engine}</b> {s.database.ok ? <Badge tone="good">answering</Badge> : <Badge tone="bad">down</Badge>}</span></div>
          <div className="flex items-start gap-2"><Cpu className="w-4 h-4 text-slate-400 mt-0.5" /><span>AI providers: {s.ai.available ? s.ai.chain.join(" → ") : "none configured (rule-based checks only)"}{s.ai.chain.length > 1 && <span className="text-slate-500"> (falls back in this order)</span>}</span></div>
          <div className="flex items-start gap-2"><Activity className="w-4 h-4 text-slate-400 mt-0.5" /><span>Error tracking: {t.sentry ? "Sentry on" : "stored here only"} · Metrics endpoint: {t.metrics_endpoint ? "on" : "off"}</span></div>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        <div className={`${CARD} p-5`}>
          <h3 className="text-sm font-semibold text-slate-900">Server errors in your workspace (7 days)</h3>
          {s.recent_errors.length === 0 ? <p className="text-xs text-emerald-700 mt-1">None.</p> : (
            <ul className="mt-2 divide-y divide-slate-100">
              {s.recent_errors.map((e) => (
                <li key={e.id} className="py-2 text-[12.5px]">
                  <div className="flex gap-2"><b className="text-slate-900">{e.method} {e.path}</b><span className="ml-auto text-slate-400 text-[11.5px]">{when(e.at)}</span></div>
                  <div className="text-rose-700 break-all">{e.error_type}: {e.message}</div>
                  <div className="text-[11px] text-slate-400 font-code">ref {e.request_id}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className={`${CARD} p-5`}>
          <h3 className="text-sm font-semibold text-slate-900">Busiest and slowest</h3>
          <table className="w-full mt-2 text-[12.5px]"><tbody className="divide-y divide-slate-100">
            {t.busiest_routes.map((r) => <tr key={r.route}><td className="py-1.5 font-code text-[11.5px] break-all">{r.route}</td><td className="text-right tabular-nums">{r.requests}</td></tr>)}
          </tbody></table>
          {t.slowest_routes.length > 0 && <p className="text-[11.5px] text-slate-500 mt-3">Slowest on average: {t.slowest_routes.map((r) => `${r.route} (${r.avg_ms} ms)`).join(", ")}</p>}
        </div>
      </div>
    </div>
  );
}
