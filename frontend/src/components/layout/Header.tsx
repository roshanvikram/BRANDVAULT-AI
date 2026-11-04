"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import {
  Search,
  Bell,
  HelpCircle,
  ShieldCheck,
  ChevronDown,
  User,
  Sparkles
} from "lucide-react";
import { fetchHealth, HealthInfo } from "@/lib/api";

export function Header() {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

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
    <header className="h-16 border-b border-[#E5E5E5] bg-white px-7 flex items-center justify-between sticky top-0 z-40 select-none shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
      {/* 1. Breadcrumb / Current Page Name */}
      <div className="flex items-center space-x-3 w-1/4">
        <span className="text-xs font-mono text-[#A3A3A3] uppercase">BrandVault</span>
        <span className="text-xs text-[#E5E5E5]">/</span>
        <h1 className="text-sm font-bold text-[#0A0A0A] tracking-tight">{getPageTitle(pathname)}</h1>
      </div>

      {/* 2. Central Integrated Search Input (Matching Reference UI) */}
      <div className="flex-1 max-w-md mx-6">
        <div className="relative">
          <Search className="w-4 h-4 text-[#A3A3A3] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search guidelines, claims, rules, or campaigns... (⌘K)"
            className="w-full pl-10 pr-4 py-2 text-xs bg-[#F5F5F5] border border-transparent hover:border-[#E5E5E5] focus:border-[#0A0A0A] focus:bg-white rounded-xl text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* 3. Right Action Tools (Matching Reference UI) */}
      <div className="flex items-center space-x-4">
        {/* Workspace Dropdown */}
        <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] text-xs font-mono font-semibold text-[#0A0A0A] cursor-pointer hover:bg-[#E5E5E5] transition-colors">
          <span>NOVA TECH</span>
          <ChevronDown className="w-3.5 h-3.5 text-[#737373]" />
        </div>

        {/* Notifications Icon with Badge */}
        <div className="relative p-2 rounded-xl text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] cursor-pointer transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#0A0A0A] ring-2 ring-white" />
        </div>

        {/* Help / Docs */}
        <div className="p-2 rounded-xl text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] cursor-pointer transition-colors">
          <HelpCircle className="w-4 h-4" />
        </div>

        {/* User Avatar */}
        <div className="flex items-center space-x-2 pl-2 border-l border-[#E5E5E5]">
          <div className="w-8 h-8 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-xs font-mono font-bold shadow-sm">
            RV
          </div>
        </div>
      </div>
    </header>
  );
}
