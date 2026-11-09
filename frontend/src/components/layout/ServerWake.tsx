"use client";

import { useEffect, useState } from "react";
import { Loader2, CloudOff } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

/**
 * Free hosting puts the API to sleep after ~15 idle minutes; the first request then
 * takes up to a minute. Instead of looking broken, say so while the server wakes up.
 */
export function ServerWake() {
  const [state, setState] = useState<"ok" | "waking" | "down">("ok");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let done = false;
    const slow = setTimeout(() => { if (!done) setState("waking"); }, 2500);
    const ctrl = new AbortController();
    const giveUp = setTimeout(() => ctrl.abort(), 90_000);
    fetch(`${API_BASE_URL}/health`, { cache: "no-store", signal: ctrl.signal })
      .then((r) => { done = true; setState(r.ok ? "ok" : "down"); })
      .catch(() => { done = true; setState("down"); })
      .finally(() => { clearTimeout(slow); clearTimeout(giveUp); });
    return () => { done = true; clearTimeout(slow); clearTimeout(giveUp); ctrl.abort(); };
  }, [attempt]);

  if (state === "ok") return null;
  return (
    <div role="status" className={`fixed top-3 left-1/2 -translate-x-1/2 z-[60] rounded-xl px-4 py-2.5 text-[13px] shadow-lg ring-1 flex items-center gap-2.5
      ${state === "waking" ? "bg-white text-slate-700 ring-slate-200" : "bg-rose-50 text-rose-800 ring-rose-200"}`}>
      {state === "waking" ? (
        <><Loader2 className="w-4 h-4 animate-spin text-indigo-600" /> Waking up the server — free hosting sleeps when idle, this can take up to a minute.</>
      ) : (
        <><CloudOff className="w-4 h-4" /> The BrandVault server is not reachable.
          <button onClick={() => { setState("waking"); setAttempt((a) => a + 1); }} className="font-semibold underline">Try again</button></>
      )}
    </div>
  );
}
