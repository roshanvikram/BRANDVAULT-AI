"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Activity, ShieldCheck, User } from "lucide-react";
import { fetchHealth, HealthInfo } from "@/lib/api";

export function Header() {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const getPageTitle = (path: string) => {
    switch (path) {
      case "/":
        return "Command Center";
      case "/brand-dna":
        return "Brand DNA Studio";
      case "/content-intelligence":
        return "Content Intelligence";
      case "/claim-dna":
        return "ClaimDNA Verification";
      case "/visual-dna":
        return "Visual DNA Inspector";
      case "/agent-control":
        return "Agent Control Center";
      case "/approval-hub":
        return "Human Approval Hub";
      case "/brand-passport":
        return "Brand Passport Repository";
      case "/risk-radar":
        return "Brand Risk Radar";
      case "/settings":
        return "System Settings";
      default:
        return "Brand Governance";
    }
  };

  return (
    <header className="h-14 border-b border-[#E5E5E5] bg-[#FFFFFF]/95 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-40 select-none shadow-sm">
      {/* Title & Breadcrumbs */}
      <div className="flex items-center space-x-3">
        <span className="text-xs font-mono text-[#737373] font-semibold">BRANDVAULT</span>
        <span className="text-xs text-[#A3A3A3]">/</span>
        <h1 className="text-sm font-bold text-[#0A0A0A] tracking-tight">{getPageTitle(pathname)}</h1>
      </div>

      {/* Center Tagline */}
      <div className="hidden lg:flex items-center space-x-2 text-xs text-[#404040] font-mono">
        <ShieldCheck className="w-3.5 h-3.5 text-[#0A0A0A]" />
        <span>Protect Every Word. Preserve Every Identity.</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#F5F5F5] border border-[#E5E5E5]">
          <span className="w-2 h-2 rounded-full bg-[#0A0A0A] animate-pulse" />
          <span className="text-[11px] font-mono font-medium text-[#0A0A0A]">
            {health?.status === "healthy" ? "ENGINE ONLINE" : "OFFLINE"}
          </span>
        </div>

        {/* User Identity / Role */}
        <div className="flex items-center space-x-2 pl-2 border-l border-[#E5E5E5]">
          <div className="w-7 h-7 rounded border border-[#E5E5E5] bg-[#F5F5F5] flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-[#0A0A0A]" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-bold text-[#0A0A0A]">Roshan Vikram AV</div>
            <div className="text-[9px] font-mono text-[#737373] uppercase">Lead Engineer</div>
          </div>
        </div>
      </div>
    </header>
  );
}
