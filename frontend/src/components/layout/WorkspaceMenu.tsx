"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Check, Building2, Loader2 } from "lucide-react";
import { fetchWorkspaces, Organization } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useClickOutside } from "@/lib/useClickOutside";

/**
 * Workspace indicator + menu. Shows the organisations returned by the backend
 * (GET /brand/workspaces) and marks the one the signed-in user belongs to as
 * active. A Creator/Reviewer is scoped to a single org, so this reflects real
 * tenancy rather than offering a switch the API would reject.
 */
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
        className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] text-xs font-mono font-semibold text-[#0A0A0A] hover:bg-[#E5E5E5] transition-colors"
      >
        <span className="uppercase">{label}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-[#737373] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-72 rounded-xl border border-[#E5E5E5] bg-white shadow-lg z-50 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-[#F0F0F0] text-[10px] font-mono uppercase font-bold text-[#A3A3A3]">
            Your Workspaces
          </div>
          <div className="max-h-72 overflow-y-auto py-1">
            {orgs === null ? (
              <div className="px-4 py-6 flex items-center justify-center text-[#737373]">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            ) : orgs.length === 0 ? (
              <div className="px-4 py-6 text-center text-xs text-[#737373] font-mono">No workspaces found.</div>
            ) : (
              orgs.map((o) => {
                const isActive = o.id === user?.org_id;
                return (
                  <div
                    key={o.id}
                    className={`px-4 py-2.5 flex items-start justify-between ${isActive ? "bg-[#FAFAFA]" : ""}`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <div className="w-7 h-7 rounded-lg bg-[#0A0A0A] text-white flex items-center justify-center shrink-0">
                        <Building2 className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-[#0A0A0A]">{o.name}</div>
                        <div className="text-[10px] font-mono text-[#737373] mt-0.5">
                          {o.guidelines_count} docs · {o.rules_count} rules · {o.facts_count} facts
                        </div>
                      </div>
                    </div>
                    {isActive && <Check className="w-4 h-4 text-[#0A0A0A] shrink-0 mt-0.5" />}
                  </div>
                );
              })
            )}
          </div>
          {active && (
            <div className="px-4 py-2 border-t border-[#F0F0F0] text-[10px] font-mono text-[#737373]">
              Signed in as <span className="text-[#0A0A0A] font-semibold">{user?.role}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
