"use client";

import { usePathname, useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { useAuth, initials } from "@/lib/auth";
import { WorkspaceMenu } from "./WorkspaceMenu";
import { NotificationsMenu } from "./NotificationsMenu";
import { HelpMenu } from "./HelpMenu";
import { GlobalSearch } from "./GlobalSearch";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Command Center",
  "/brand-dna": "Brand DNA Studio",
  "/knowledge-graph": "Knowledge Graph",
  "/assistant": "Brand Assistant",
  "/brand-memory": "Brand Memory",
  "/content-intelligence": "Content Intelligence",
  "/copy-studio": "AI Copy Studio",
  "/claim-dna": "ClaimDNA Verification",
  "/visual-dna": "Visual DNA Inspector",
  "/agent-control": "Agent Control Center",
  "/approval-hub": "Human Approval Hub",
  "/brand-passport": "Brand Passport Repository",
  "/risk-radar": "Brand Risk Radar",
  "/settings": "System Settings",
  "/onboarding": "Setup Guide",
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const title = PAGE_TITLES[pathname] || "Brand Governance";

  return (
    <header className="h-16 border-b border-white/60 bg-white/55 backdrop-blur-xl px-7 flex items-center justify-between sticky top-0 z-40 select-none shadow-[0_6px_20px_-12px_rgba(10,10,10,0.15)]">
      {/* Breadcrumb / current page */}
      <div className="flex items-center space-x-3 w-1/4">
        <span className="text-xs font-mono text-[#A3A3A3] uppercase">BrandVault</span>
        <span className="text-xs text-[#E5E5E5]">/</span>
        <h1 className="text-sm font-bold text-[#0A0A0A] tracking-tight">{title}</h1>
      </div>

      {/* Global search (real) */}
      <GlobalSearch />

      {/* Right action tools */}
      <div className="flex items-center space-x-4">
        <WorkspaceMenu />
        <NotificationsMenu />
        <HelpMenu />

        {/* Signed-in user + logout */}
        <div className="flex items-center space-x-2.5 pl-3 border-l border-[#E5E5E5]">
          <div className="w-8 h-8 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center text-xs font-mono font-bold shadow-sm uppercase">
            {initials(user?.full_name)}
          </div>
          <div className="hidden lg:block leading-tight">
            <div className="text-xs font-bold text-[#0A0A0A]">{user?.full_name || "Guest"}</div>
            <div className="text-[10px] font-mono text-[#737373]">{user?.role || "—"}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-2 rounded-xl text-[#404040] hover:text-[#0A0A0A] hover:bg-[#F5F5F5] transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
