"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Dna,
  FileSearch,
  BadgeCheck,
  Image as ImageIcon,
  Languages,
  Bot,
  ClipboardCheck,
  Award,
  Radar,
  Network,
  MessageSquare,
  Brain,
  Wand2,
  Settings,
  Rocket,
  PanelLeftClose,
  PanelLeftOpen,
  X,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useOrganization } from "@/lib/useOrganization";
import { useShell } from "./AppShell";

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: string;
}

// Grouped by the job a person is doing with subtle accent colors for each group
const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Overview",
    items: [
      { name: "Command Center", href: "/dashboard", icon: LayoutDashboard },
      { name: "Setup Guide", href: "/onboarding", icon: Rocket, badge: "Guide", badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    ],
  },
  {
    label: "Brand DNA",
    items: [
      { name: "Brand DNA Studio", href: "/brand-dna", icon: Dna },
      { name: "Brand Memory", href: "/brand-memory", icon: Brain },
      { name: "Knowledge Graph", href: "/knowledge-graph", icon: Network },
    ],
  },
  {
    label: "Analyse",
    items: [
      { name: "Content Intelligence", href: "/content-intelligence", icon: FileSearch },
      { name: "ClaimDNA", href: "/claim-dna", icon: BadgeCheck },
      { name: "Visual DNA", href: "/visual-dna", icon: ImageIcon },
      { name: "Translation Guard", href: "/translation-guard", icon: Languages, badge: "New", badgeColor: "bg-violet-50 text-violet-700 border-violet-200" },
    ],
  },
  {
    label: "Create",
    items: [
      { name: "AI Copy Studio", href: "/copy-studio", icon: Wand2, badge: "AI", badgeColor: "bg-indigo-50 text-indigo-700 border-indigo-200" },
      { name: "Brand Assistant", href: "/assistant", icon: MessageSquare },
    ],
  },
  {
    label: "Govern",
    items: [
      { name: "Approval Hub", href: "/approval-hub", icon: ClipboardCheck },
      { name: "Brand Passport", href: "/brand-passport", icon: Award },
      { name: "Risk Radar", href: "/risk-radar", icon: Radar },
      { name: "Agent Control", href: "/agent-control", icon: Bot },
    ],
  },
];

const COLLAPSE_KEY = "bv_sidebar_collapsed";

function NavLink({ item, active, collapsed }: { item: NavItem; active: boolean; collapsed: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      title={collapsed ? item.name : undefined}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative flex items-center h-9 rounded-xl text-[13px] transition-all duration-150 group",
        collapsed ? "justify-center px-0" : "px-3 justify-between",
        active
          ? "bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-700 text-white font-semibold shadow-[0_4px_16px_-2px_rgba(79,70,229,0.45)] ring-1 ring-indigo-500/50"
          : "text-slate-600 hover:text-indigo-700 hover:bg-indigo-50/70"
      )}
    >
      <div className="flex items-center min-w-0">
        <Icon
          aria-hidden
          className={cn(
            "w-4 h-4 shrink-0 transition-colors",
            active ? "text-white" : "text-slate-400 group-hover:text-indigo-600"
          )}
          strokeWidth={active ? 2.2 : 1.75}
        />
        {!collapsed && <span className="ml-2.5 truncate">{item.name}</span>}
      </div>

      {!collapsed && item.badge && (
        <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded-full border shadow-2xs", item.badgeColor)}>
          {item.badge}
        </span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const org = useOrganization();
  const { mobileNavOpen, setMobileNavOpen } = useShell();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
    } catch {
      /* storage unavailable: default expanded */
    }
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      try {
        localStorage.setItem(COLLAPSE_KEY, c ? "0" : "1");
      } catch {
        /* ignore */
      }
      return !c;
    });
  };

  // On mobile the drawer is always shown expanded.
  const isCollapsed = collapsed && !mobileNavOpen;

  return (
    <>
      {/* Mobile backdrop */}
      <div
        aria-hidden
        onClick={() => setMobileNavOpen(false)}
        className={cn(
          "fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm lg:hidden transition-opacity",
          mobileNavOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
      />
      <aside
        aria-label="Main navigation"
        className={cn(
          "fixed lg:sticky top-0 left-0 z-50 h-screen flex flex-col bg-white/55 backdrop-blur-2xl backdrop-saturate-150 border-r border-white/70 select-none",
          "transition-[transform,width] duration-200 ease-out",
          isCollapsed ? "lg:w-[68px]" : "lg:w-[256px]",
          "w-[272px]",
          mobileNavOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand + organisation */}
        <div className={cn("h-16 flex items-center border-b border-slate-200/60 shrink-0", isCollapsed ? "justify-center" : "px-4 justify-between")}>
          <Link href="/dashboard" className="flex items-center gap-2.5 min-w-0 group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 text-white flex items-center justify-center text-xs font-bold shadow-md shadow-indigo-500/30 shrink-0 group-hover:scale-105 transition-transform">
              BV
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <div className="text-[14px] font-bold text-slate-900 leading-tight tracking-tight">BrandVault AI</div>
                <div className="text-[11px] font-medium text-indigo-600 leading-tight truncate mt-0.5">
                  {org?.name || "Loading workspace…"}
                </div>
              </div>
            )}
          </Link>
          <button
            onClick={() => setMobileNavOpen(false)}
            className="lg:hidden p-2 -mr-2 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className={cn("flex-1 overflow-y-auto py-3.5 space-y-4", isCollapsed ? "px-2" : "px-3")}>
          {NAV_GROUPS.map((group, gi) => (
            <div key={group.label}>
              {isCollapsed ? (
                gi > 0 && <div className="mx-2 mb-3 border-t border-slate-100" />
              ) : (
                <div className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400">
                  {group.label}
                </div>
              )}
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink key={item.href} item={item} active={pathname === item.href || pathname.startsWith(item.href + "/")} collapsed={isCollapsed} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className={cn("border-t border-slate-200/60 py-3 space-y-1 shrink-0", isCollapsed ? "px-2" : "px-3")}>
          <NavLink
            item={{ name: "Settings", href: "/settings", icon: Settings }}
            active={pathname === "/settings"}
            collapsed={isCollapsed}
          />
          <button
            onClick={toggleCollapsed}
            className={cn(
              "hidden lg:flex items-center h-9 w-full rounded-xl text-[13px] text-slate-500 hover:text-slate-900 hover:bg-slate-100/80 transition-colors",
              isCollapsed ? "justify-center" : "px-3"
            )}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <PanelLeftOpen className="w-4 h-4 text-slate-400" strokeWidth={1.75} />
            ) : (
              <>
                <PanelLeftClose className="w-4 h-4 text-slate-400" strokeWidth={1.75} />
                <span className="ml-2.5 font-medium">Collapse</span>
              </>
            )}
          </button>

          {!isCollapsed && org && (
            <div className="mt-2 rounded-xl bg-white ring-1 ring-slate-200/80 shadow-[0_1px_2px_rgba(34,36,39,0.04)] p-3">
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5 min-w-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span className="truncate font-semibold text-slate-800">{org.name}</span>
                </span>
                <span className="text-slate-500 tabular-nums shrink-0">{org.rules_count} rules</span>
              </div>
              <div className="mt-1 text-[11px] text-slate-400">Brand DNA workspace</div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
