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
}

// Grouped by the job a person is doing, so a 14-item menu stays scannable.
const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Overview",
    items: [
      { name: "Command Center", href: "/dashboard", icon: LayoutDashboard },
      { name: "Setup Guide", href: "/onboarding", icon: Rocket },
    ],
  },
  {
    label: "Brand",
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
    ],
  },
  {
    label: "Create",
    items: [
      { name: "AI Copy Studio", href: "/copy-studio", icon: Wand2 },
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
        "relative flex items-center h-9 rounded-lg text-[13px] transition-colors duration-150",
        collapsed ? "justify-center px-0" : "px-2.5",
        active
          ? "bg-[#F4F4F5] text-[#0A0A0A] font-medium"
          : "text-[#52525B] hover:text-[#0A0A0A] hover:bg-[#F4F4F5]/70"
      )}
    >
      {active && !collapsed && (
        <span aria-hidden className="absolute left-0 top-2 bottom-2 w-[2px] rounded-full bg-[#0A0A0A]" />
      )}
      <Icon
        aria-hidden
        className={cn("w-4 h-4 shrink-0", active ? "text-[#0A0A0A]" : "text-[#71717A]")}
        strokeWidth={1.75}
      />
      {!collapsed && <span className="ml-2.5 truncate">{item.name}</span>}
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
          "fixed inset-0 z-40 bg-[#0A0A0A]/30 lg:hidden transition-opacity",
          mobileNavOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
      />
      <aside
        aria-label="Main navigation"
        className={cn(
          "fixed lg:sticky top-0 left-0 z-50 h-screen flex flex-col bg-white border-r border-[#E4E4E7] select-none",
          "transition-[transform,width] duration-200 ease-out",
          isCollapsed ? "lg:w-[64px]" : "lg:w-[248px]",
          "w-[272px]",
          mobileNavOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand + organisation */}
        <div className={cn("h-14 flex items-center border-b border-[#E4E4E7] shrink-0", isCollapsed ? "justify-center" : "px-4 justify-between")}>
          <Link href="/dashboard" className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-md bg-[#0A0A0A] text-white flex items-center justify-center text-[11px] font-semibold shrink-0">
              BV
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <div className="text-[13px] font-semibold text-[#0A0A0A] leading-tight truncate">BrandVault AI</div>
                <div className="text-[11px] text-[#71717A] leading-tight truncate">{org?.name || "Loading workspace…"}</div>
              </div>
            )}
          </Link>
          <button
            onClick={() => setMobileNavOpen(false)}
            className="lg:hidden p-2 -mr-2 rounded-md text-[#71717A] hover:text-[#0A0A0A] hover:bg-[#F4F4F5]"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className={cn("flex-1 overflow-y-auto py-3", isCollapsed ? "px-2" : "px-3")}>
          {NAV_GROUPS.map((group, gi) => (
            <div key={group.label} className={cn(gi > 0 && "mt-4")}>
              {isCollapsed ? (
                gi > 0 && <div className="mx-2 mb-3 border-t border-[#E4E4E7]" />
              ) : (
                <div className="px-2.5 pb-1.5 text-[11px] font-medium text-[#A1A1AA]">{group.label}</div>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink key={item.href} item={item} active={pathname === item.href} collapsed={isCollapsed} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className={cn("border-t border-[#E4E4E7] py-3 space-y-0.5 shrink-0", isCollapsed ? "px-2" : "px-3")}>
          <NavLink
            item={{ name: "Settings", href: "/settings", icon: Settings }}
            active={pathname === "/settings"}
            collapsed={isCollapsed}
          />
          <button
            onClick={toggleCollapsed}
            className={cn(
              "hidden lg:flex items-center h-9 w-full rounded-lg text-[13px] text-[#52525B] hover:text-[#0A0A0A] hover:bg-[#F4F4F5]/70 transition-colors",
              isCollapsed ? "justify-center" : "px-2.5"
            )}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <PanelLeftOpen className="w-4 h-4 text-[#71717A]" strokeWidth={1.75} />
            ) : (
              <>
                <PanelLeftClose className="w-4 h-4 text-[#71717A]" strokeWidth={1.75} />
                <span className="ml-2.5">Collapse</span>
              </>
            )}
          </button>
          {!isCollapsed && org && (
            <div className="px-2.5 pt-2 text-[11px] text-[#71717A] tabular-nums">
              {org.rules_count} rules · {org.facts_count} approved facts
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
