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
  Sliders,
  ChevronRight
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
    <aside className="w-64 border-r border-[#262626] bg-[#0A0A0A] flex flex-col h-screen sticky top-0 select-none">
      {/* Brand Identity Header */}
      <div className="p-5 border-b border-[#262626]">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded border border-[#404040] bg-[#171717] flex items-center justify-center font-mono font-bold text-sm tracking-wider text-[#F5F5F5] group-hover:border-[#737373] transition-colors">
            BV
          </div>
          <div>
            <div className="font-semibold text-sm tracking-tight text-[#FFFFFF]">BRANDVAULT AI</div>
            <div className="text-[10px] text-[#737373] tracking-wide font-mono uppercase">Enterprise Governance</div>
          </div>
        </Link>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-mono tracking-wider uppercase text-[#737373]">
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
                  ? "bg-[#171717] text-[#FFFFFF] font-medium border border-[#404040]"
                  : "text-[#A3A3A3] hover:text-[#FFFFFF] hover:bg-[#171717] border border-transparent"
              )}
            >
              <div className="flex items-center space-x-2.5">
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-[#FFFFFF]" : "text-[#737373] group-hover:text-[#FFFFFF]"
                  )}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "text-[9px] px-1.5 py-0.5 rounded font-mono border",
                    isActive
                      ? "bg-[#262626] text-[#FFFFFF] border-[#737373]"
                      : "bg-[#0A0A0A] text-[#737373] border-[#262626]"
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
      <div className="p-4 border-t border-[#262626] bg-[#0A0A0A]">
        <div className="p-2.5 rounded bg-[#171717] border border-[#262626]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono text-[#A3A3A3]">ACTIVE WORKSPACE</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF]" />
          </div>
          <div className="text-xs font-semibold text-[#FFFFFF] mt-1">NOVA TECH</div>
          <div className="text-[10px] text-[#737373] font-mono mt-0.5">Leader: Deepak Mouriya M</div>
        </div>
      </div>
    </aside>
  );
}
