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
    <header className="h-14 border-b border-[#262626] bg-[#0A0A0A]/95 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-40 select-none">
      {/* Title & Breadcrumbs */}
      <div className="flex items-center space-x-3">
        <span className="text-xs font-mono text-[#737373]">BRANDVAULT</span>
        <span className="text-xs text-[#404040]">/</span>
        <h1 className="text-sm font-semibold text-[#FFFFFF] tracking-tight">{getPageTitle(pathname)}</h1>
      </div>

      {/* Center Tagline */}
      <div className="hidden lg:flex items-center space-x-2 text-xs text-[#737373] font-mono">
        <ShieldCheck className="w-3.5 h-3.5 text-[#A3A3A3]" />
        <span>Protect Every Word. Preserve Every Identity.</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#171717] border border-[#262626]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF] animate-pulse" />
          <span className="text-[11px] font-mono text-[#A3A3A3]">
            {health?.status === "healthy" ? "ENGINE ONLINE" : "OFFLINE"}
          </span>
        </div>

        {/* User Identity / Role */}
        <div className="flex items-center space-x-2 pl-2 border-l border-[#262626]">
          <div className="w-6 h-6 rounded border border-[#404040] bg-[#171717] flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-[#A3A3A3]" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-medium text-[#F5F5F5]">Roshan Vikram AV</div>
            <div className="text-[9px] font-mono text-[#737373] uppercase">Lead Engineer</div>
          </div>
        </div>
      </div>
    </header>
  );
}
