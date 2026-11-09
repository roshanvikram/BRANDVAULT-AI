"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, Clock, Award, AlertTriangle, ShieldAlert, CheckCircle2, Loader2 } from "lucide-react";
import { fetchNotifications, markNotificationsRead, NotificationOut } from "@/lib/api";
import { useClickOutside } from "@/lib/useClickOutside";

const ICON: Record<string, JSX.Element> = {
  "analysis.completed": <Clock className="w-3.5 h-3.5" />,
  "review.decided": <CheckCircle2 className="w-3.5 h-3.5" />,
  "passport.issued": <Award className="w-3.5 h-3.5" />,
  "passport.superseded": <AlertTriangle className="w-3.5 h-3.5" />,
  "publish_gate.blocked": <ShieldAlert className="w-3.5 h-3.5" />,
  "incident.opened": <ShieldAlert className="w-3.5 h-3.5" />,
};

/** In-app notifications from the event hub (backend /notifications), filtered to the user's role. */
export function NotificationsMenu() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<{ unread: number; items: NotificationOut[] } | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => setOpen(false), open);

  const load = () => fetchNotifications().then(setData).catch(() => setData({ unread: 0, items: [] }));
  useEffect(() => {
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, []);

  const go = async (n: NotificationOut) => {
    setOpen(false);
    if (!n.read) markNotificationsRead([n.id]).then(load).catch(() => {});
    if (n.link) router.push(n.link);
  };

  const unread = data?.unread || 0;
  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen((v) => !v)} title="Notifications" aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
              className="relative p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors">
        <Bell className="w-4 h-4" />
        {unread > 0 && (
          <span className="absolute top-1 right-1 min-w-[15px] h-[15px] px-0.5 rounded-full bg-indigo-600 ring-2 ring-white text-[9px] font-semibold text-white flex items-center justify-center">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-[340px] rounded-2xl border border-slate-200 bg-white shadow-[0_16px_40px_-12px_rgba(15,23,42,0.22)] z-50 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[13px] font-semibold text-slate-900">Notifications</span>
            {unread > 0 && <button onClick={() => markNotificationsRead().then(load)} className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800">Mark all read</button>}
          </div>
          <div className="max-h-[420px] overflow-y-auto">
            {data === null ? (
              <div className="px-4 py-8 flex justify-center text-slate-400"><Loader2 className="w-4 h-4 animate-spin" /></div>
            ) : data.items.length === 0 ? (
              <div className="px-4 py-8 text-center text-xs text-slate-500">You&apos;re all caught up.</div>
            ) : data.items.map((n) => (
              <button key={n.id} onClick={() => go(n)}
                      className={`w-full text-left px-4 py-3 flex items-start gap-2.5 border-b border-slate-50 last:border-0 hover:bg-slate-50 transition-colors ${n.read ? "" : "bg-indigo-50/40"}`}>
                <span className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${n.read ? "bg-slate-100 text-slate-500" : "bg-indigo-100 text-indigo-700"}`}>{ICON[n.event] || <Bell className="w-3.5 h-3.5" />}</span>
                <span className="min-w-0 flex-1">
                  <span className="block text-xs font-semibold text-slate-900">{n.title}</span>
                  {n.body && <span className="block text-[11px] text-slate-500 line-clamp-2">{n.body}</span>}
                  <span className="block text-[10px] text-slate-400 mt-0.5">
                    {n.created_at ? new Date(n.created_at + "Z").toLocaleString() : ""}
                    {Object.entries(n.channels || {}).map(([k, v]) => ` · ${k}: ${v}`).join("")}
                  </span>
                </span>
                {!n.read && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 mt-2 shrink-0" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
