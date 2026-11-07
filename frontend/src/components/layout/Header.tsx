"use client";

import { usePathname, useRouter } from "next/navigation";
import { LogOut, Menu } from "lucide-react";
import { useAuth, initials } from "@/lib/auth";
import { WorkspaceMenu } from "./WorkspaceMenu";
import { NotificationsMenu } from "./NotificationsMenu";
import { HelpMenu } from "./HelpMenu";
import { GlobalSearch } from "./GlobalSearch";
import { useShell } from "./AppShell";

const PAGE_TITLES: Record<string, { section: string; title: string }> = {
  "/dashboard": { section: "Overview", title: "Command Center" },
  "/onboarding": { section: "Overview", title: "Setup Guide" },
  "/brand-dna": { section: "Brand", title: "Brand DNA Studio" },
  "/brand-memory": { section: "Brand", title: "Brand Memory" },
  "/knowledge-graph": { section: "Brand", title: "Knowledge Graph" },
  "/content-intelligence": { section: "Analyse", title: "Content Intelligence" },
  "/claim-dna": { section: "Analyse", title: "ClaimDNA" },
  "/visual-dna": { section: "Analyse", title: "Visual DNA" },
  "/copy-studio": { section: "Create", title: "AI Copy Studio" },
  "/assistant": { section: "Create", title: "Brand Assistant" },
  "/approval-hub": { section: "Govern", title: "Approval Hub" },
  "/brand-passport": { section: "Govern", title: "Brand Passport" },
  "/risk-radar": { section: "Govern", title: "Risk Radar" },
  "/agent-control": { section: "Govern", title: "Agent Control" },
  "/settings": { section: "Workspace", title: "Settings" },
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { setMobileNavOpen } = useShell();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const page = PAGE_TITLES[pathname] || { section: "BrandVault", title: "Brand Governance" };

  return (
    <header className="glass-header h-14 px-4 sm:px-6 lg:px-8 flex items-center gap-4 sticky top-0 z-30 select-none">
      <button
        onClick={() => setMobileNavOpen(true)}
        className="lg:hidden p-2 -ml-2 rounded-md text-[#52525B] hover:text-[#0A0A0A] hover:bg-[#F4F4F5]"
        aria-label="Open navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      <div className="flex items-center gap-2 min-w-0 shrink-0 text-[13px]">
        <span className="hidden sm:inline text-[#71717A]">{page.section}</span>
        <span className="hidden sm:inline text-[#D4D4D8]">/</span>
        <h1 className="font-semibold text-[#0A0A0A] truncate">{page.title}</h1>
      </div>

      <div className="flex-1 flex justify-center min-w-0">
        <GlobalSearch />
      </div>

      <div className="flex items-center gap-1 shrink-0">
        <WorkspaceMenu />
        <NotificationsMenu />
        <HelpMenu />

        <div className="flex items-center gap-2.5 pl-3 ml-2 border-l border-[#E4E4E7]">
          <div
            className="w-7 h-7 rounded-full bg-[#F4F4F5] border border-[#E4E4E7] text-[#0A0A0A] flex items-center justify-center text-[11px] font-semibold uppercase"
            aria-hidden
          >
            {initials(user?.full_name)}
          </div>
          <div className="hidden xl:block leading-tight">
            <div className="text-[13px] font-medium text-[#0A0A0A]">{user?.full_name || "Guest"}</div>
            <div className="text-[11px] text-[#71717A]">{user?.role || "—"}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            aria-label="Sign out"
            className="p-2 rounded-md text-[#71717A] hover:text-[#0A0A0A] hover:bg-[#F4F4F5] transition-colors"
          >
            <LogOut className="w-4 h-4" strokeWidth={1.75} />
          </button>
        </div>
      </div>
    </header>
  );
}
