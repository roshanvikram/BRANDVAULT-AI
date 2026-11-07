"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Check, Building2, Loader2 } from "lucide-react";
import { fetchWorkspaces, Organization } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useClickOutside } from "@/lib/useClickOutside";

export function WorkspaceMenu() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => setOpen(false), open);

  useEffect(() => {
    if (open && orgs === null) {
      fetchWorkspaces().then(setOrgs).catch(() => setOrgs([]));
    }
  }, [open, orgs]);

  const active = orgs?.find((o) => o.id === user?.org_id);
  const label = active?.name || "Workspace";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="hidden md:flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-semibold bg-slate-100/90 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 border border-slate-200 transition-colors"
      >
        <Building2 className="w-3.5 h-3.5 text-indigo-600" />
        <span>{label}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-slate-200 bg-white shadow-xl z-50 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-slate-100 text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50/60">
            Workspaces
          </div>
          <div className="max-h-72 overflow-y-auto py-1.5">
            {orgs === null ? (
              <div className="px-4 py-6 flex items-center justify-center text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              </div>
            ) : orgs.length === 0 ? (
              <div className="px-4 py-6 text-center text-xs text-slate-500">No workspaces found.</div>
            ) : (
              orgs.map((o) => {
                const isActive = o.id === user?.org_id;
                return (
                  <div
                    key={o.id}
                    className={`px-4 py-2.5 flex items-start justify-between transition-colors ${
                      isActive ? "bg-indigo-50/70" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                        isActive ? "bg-indigo-600 text-white shadow-sm" : "bg-slate-100 text-slate-500"
                      }`}>
                        <Building2 className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className={`text-xs font-bold ${isActive ? "text-indigo-900" : "text-slate-900"}`}>{o.name}</div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {o.guidelines_count} docs · {o.rules_count} rules · {o.facts_count} facts
                        </div>
                      </div>
                    </div>
                    {isActive && <Check className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />}
                  </div>
                );
              })
            )}
          </div>
          {active && (
            <div className="px-4 py-2 border-t border-slate-100 text-[11px] text-slate-500 bg-slate-50/40">
              Role: <span className="text-indigo-700 font-semibold">{user?.role}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
