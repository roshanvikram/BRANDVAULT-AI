"use client";

import { useEffect, useState } from "react";
import { BellRing, BellOff, Loader2, Send } from "lucide-react";
import { fetchPushKey, removePushSubscription, savePushSubscription, sendTestPush } from "@/lib/api";
import { BTN_SECONDARY } from "@/components/engines/ui";

type State = "loading" | "unsupported" | "blocked" | "off" | "on";

function keyBytes(base64url: string): ArrayBuffer {
  const pad = "=".repeat((4 - (base64url.length % 4)) % 4);
  const raw = atob((base64url + pad).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0)).buffer as ArrayBuffer;
}

/** Lets each person turn on browser (Web Push) notifications for review and expiry alerts on this device. */
export function PushToggle() {
  const [state, setState] = useState<State>("loading");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
        setState("unsupported");
        return;
      }
      if (Notification.permission === "denied") { setState("blocked"); return; }
      try {
        const reg = await navigator.serviceWorker.getRegistration("/sw.js");
        const sub = await reg?.pushManager.getSubscription();
        setState(sub ? "on" : "off");
      } catch { setState("off"); }
    })();
  }, []);

  const turnOn = async () => {
    setBusy(true); setMsg(null);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") { setState(permission === "denied" ? "blocked" : "off"); return; }
      const { public_key } = await fetchPushKey();
      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(public_key) });
      await savePushSubscription(sub.toJSON());
      setState("on");
      setMsg("Browser notifications are on for this device.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not turn on browser notifications.");
    } finally { setBusy(false); }
  };

  const turnOff = async () => {
    setBusy(true); setMsg(null);
    try {
      const reg = await navigator.serviceWorker.getRegistration("/sw.js");
      const sub = await reg?.pushManager.getSubscription();
      if (sub) { await removePushSubscription(sub.toJSON()); await sub.unsubscribe(); }
      setState("off");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not turn off browser notifications.");
    } finally { setBusy(false); }
  };

  const test = async () => {
    setBusy(true); setMsg(null);
    try {
      const r = await sendTestPush();
      setMsg(r.sent ? "Test sent. It should appear in a few seconds." : "The push service did not accept the test. Try turning notifications off and on.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not send a test notification.");
    } finally { setBusy(false); }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white/70 p-3.5">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-slate-900 flex items-center gap-1.5">
            {state === "on" ? <BellRing className="w-4 h-4 text-indigo-600" /> : <BellOff className="w-4 h-4 text-slate-400" />}
            Browser notifications on this device
          </p>
          <p className="text-[11.5px] text-slate-500 mt-0.5">
            {state === "unsupported" ? "This browser does not support push notifications."
              : state === "blocked" ? "Notifications are blocked for this site. Allow them in your browser's site settings."
              : "Get review and alert notifications even when BrandVault is closed. Only you see this choice."}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {state === "loading" && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
          {state === "on" && <button disabled={busy} onClick={test} className={BTN_SECONDARY}><Send className="w-3.5 h-3.5" /> Test</button>}
          {(state === "off" || state === "on") && (
            <button disabled={busy} onClick={state === "on" ? turnOff : turnOn} className={BTN_SECONDARY}>
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}{state === "on" ? "Turn off" : "Turn on"}
            </button>
          )}
        </div>
      </div>
      {msg && <p className="text-[11.5px] text-slate-600 mt-2">{msg}</p>}
    </div>
  );
}
