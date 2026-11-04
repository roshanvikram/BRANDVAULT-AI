"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldCheck,
  Dna,
  FileSearch,
  CheckCircle2,
  Image as ImageIcon,
  Bot,
  UserCheck,
  Award,
  Radar,
  Sliders
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigationItems = [
  { name: "Command Center", href: "/", icon: ShieldCheck, badge: "CORE" },
  { name: "Brand DNA Studio", href: "/brand-dna", icon: Dna, badge: null },
  { name: "Content Intelligence", href: "/content-intelligence", icon: FileSearch, badge: "AI" },
  { name: "ClaimDNA", href: "/claim-dna", icon: CheckCircle2, badge: "FACTS" },
  { name: "Visual DNA Inspector", href: "/visual-dna", icon: ImageIcon, badge: null },
  { name: "Agent Control Center", href: "/agent-control", icon: Bot, badge: "LIVE" },
  { name: "Approval Hub", href: "/approval-hub", icon: UserCheck, badge: "GOV" },
  { name: "Brand Passport", href: "/brand-passport", icon: Award, badge: "AUDIT" },
  { name: "Brand Risk Radar", href: "/risk-radar", icon: Radar, badge: null },
  { name: "Settings", href: "/settings", icon: Sliders, badge: null },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-[#E5E5E5] bg-[#FFFFFF] flex flex-col h-screen sticky top-0 select-none shadow-sm">
      {/* Brand Identity Header */}
      <div className="p-5 border-b border-[#E5E5E5]">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded border border-[#0A0A0A] bg-[#0A0A0A] flex items-center justify-center font-mono font-bold text-sm tracking-wider text-[#FFFFFF] shadow-sm">
            BV
          </div>
          <div>
            <div className="font-bold text-sm tracking-tight text-[#0A0A0A]">BRANDVAULT AI</div>
            <div className="text-[10px] text-[#737373] tracking-wide font-mono uppercase">Enterprise Governance</div>
          </div>
        </Link>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-mono tracking-wider uppercase text-[#737373] font-semibold">
          Governance Suite
        </div>
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3 py-2 text-xs rounded transition-all duration-150 group",
                isActive
                  ? "bg-[#0A0A0A] text-[#FFFFFF] font-medium shadow-sm"
                  : "text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] border border-transparent"
              )}
            >
              <div className="flex items-center space-x-2.5">
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-[#FFFFFF]" : "text-[#737373] group-hover:text-[#0A0A0A]"
                  )}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "text-[9px] px-1.5 py-0.5 rounded font-mono border",
                    isActive
                      ? "bg-[#262626] text-[#FFFFFF] border-[#404040]"
                      : "bg-[#F5F5F5] text-[#737373] border-[#E5E5E5]"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Team / Organization Footer */}
      <div className="p-4 border-t border-[#E5E5E5] bg-[#FFFFFF]">
        <div className="p-3 rounded bg-[#F5F5F5] border border-[#E5E5E5]">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-[#737373] uppercase font-semibold">ACTIVE WORKSPACE</span>
            <span className="w-2 h-2 rounded-full bg-[#0A0A0A]" />
          </div>
          <div className="text-xs font-bold text-[#0A0A0A] mt-1">NOVA TECH</div>
          <div className="text-[10px] text-[#737373] font-mono mt-0.5">Leader: Deepak Mouriya M</div>
        </div>
      </div>
    </aside>
  );
}
