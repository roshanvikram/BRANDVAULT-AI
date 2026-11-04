"use client";

import { useState } from "react";
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
  HelpCircle,
  ChevronDown,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth, initials } from "@/lib/auth";

const mainNavigation = [
  { name: "Command Center", href: "/dashboard", icon: ShieldCheck },
  { name: "Brand DNA Studio", href: "/brand-dna", icon: Dna },
  { name: "Content Intelligence", href: "/content-intelligence", icon: FileSearch },
  { name: "ClaimDNA", href: "/claim-dna", icon: CheckCircle2 },
  { name: "Visual DNA", href: "/visual-dna", icon: ImageIcon },
  { name: "Agent Control Center", href: "/agent-control", icon: Bot },
  { name: "Approval Hub", href: "/approval-hub", icon: UserCheck },
  { name: "Brand Passport", href: "/brand-passport", icon: Award },
  { name: "Risk Radar", href: "/risk-radar", icon: Radar },
];

const secondaryNavigation = [
  { name: "Settings", href: "/settings", icon: Sliders },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { user } = useAuth();

  return (
    <aside
      className={cn(
        "border-r border-[#E5E5E5] bg-white flex flex-col h-screen sticky top-0 select-none shadow-[1px_0_4px_rgba(0,0,0,0.02)] transition-all duration-200 z-50",
        collapsed ? "w-20" : "w-[240px]"
      )}
    >
      {/* 1. Brand Wordmark & Logo */}
      <div className="p-5 border-b border-[#F0F0F0] flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold text-sm tracking-wider shadow-sm group-hover:scale-105 transition-transform">
            BV
          </div>
          {!collapsed && (
            <div>
              <div className="font-bold text-sm tracking-tight text-[#0A0A0A]">BRANDVAULT</div>
              <div className="text-[9px] text-[#737373] tracking-widest font-mono uppercase">AI GOVERNANCE</div>
            </div>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-[#A3A3A3] hover:text-[#0A0A0A] p-1 rounded-md transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* 2. User Profile Snippet (Matching reference image) */}
      {!collapsed && (
        <div className="px-4 py-3 border-b border-[#F0F0F0] bg-[#FAFAFA]">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-xs font-mono font-bold shadow-sm uppercase">
                {initials(user?.full_name)}
              </div>
              <div className="text-left">
                <div className="text-xs font-bold text-[#0A0A0A] leading-tight">{user?.full_name || "Guest"}</div>
                <div className="text-[10px] text-[#737373] font-mono">{user?.role || "—"}</div>
              </div>
            </div>
            <MoreHorizontal className="w-4 h-4 text-[#A3A3A3]" />
          </div>
        </div>
      )}

      {/* 3. Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        {!collapsed && (
          <div className="px-3 pb-1 text-[10px] font-mono tracking-wider uppercase text-[#A3A3A3] font-bold">
            Platform Menu
          </div>
        )}
        {mainNavigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.name : undefined}
              className={cn(
                "flex items-center px-3.5 py-2.5 text-xs rounded-xl transition-all duration-150 group",
                isActive
                  ? "bg-[#0A0A0A] text-white font-semibold shadow-sm"
                  : "text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5]"
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4 transition-colors shrink-0",
                  isActive ? "text-white" : "text-[#737373] group-hover:text-[#0A0A0A]"
                )}
              />
              {!collapsed && (
                <span className="ml-3 truncate">{item.name}</span>
              )}
            </Link>
          );
        })}

        {!collapsed && (
          <div className="pt-4 px-3 pb-1 text-[10px] font-mono tracking-wider uppercase text-[#A3A3A3] font-bold">
            Preferences
          </div>
        )}
        {secondaryNavigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.name : undefined}
              className={cn(
                "flex items-center px-3.5 py-2.5 text-xs rounded-xl transition-all duration-150 group",
                isActive
                  ? "bg-[#0A0A0A] text-white font-semibold shadow-sm"
                  : "text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5]"
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4 transition-colors shrink-0",
                  isActive ? "text-white" : "text-[#737373] group-hover:text-[#0A0A0A]"
                )}
              />
              {!collapsed && (
                <span className="ml-3 truncate">{item.name}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* 4. Organization Switcher & Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-[#F0F0F0]">
          <div className="p-3 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-mono text-[#737373] uppercase font-bold">ORGANIZATION</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#0A0A0A]" />
            </div>
            <div className="text-xs font-bold text-[#0A0A0A]">NOVA TECH</div>
            <div className="text-[10px] text-[#737373] font-mono">Launch Price: ₹79,999</div>
          </div>
        </div>
      )}
    </aside>
  );
}
