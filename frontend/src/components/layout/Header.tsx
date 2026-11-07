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
  "/brand-dna/products": { section: "Brand DNA Studio", title: "Product Truth" },
  "/brand-dna/knowledge-gaps": { section: "Brand DNA Studio", title: "Knowledge Gaps" },
  "/visual-dna/forensics": { section: "Visual DNA", title: "Asset Forensics" },
  "/brand-passport/verify": { section: "Brand Passport", title: "Campaign Integrity" },
  "/approval-hub/readiness": { section: "Approval Hub", title: "Launch Readiness" },
  "/approval-hub/insights": { section: "Approval Hub", title: "Reviewer Intelligence" },
  "/visual-dna/lifecycle": { section: "Asset Library", title: "Lifecycle & Expiry" },
  "/dashboard/consistency": { section: "Command Center", title: "Consistency Heatmap" },
  "/assistant/simulator": { section: "Brand Assistant", title: "Campaign Stress Testing" },
  "/content-intelligence/similarity": { section: "Content Intelligence", title: "Similarity Detector" },
  "/risk-radar/fraud": { section: "Risk Radar", title: "Brand Fraud Intelligence" },
  "/risk-radar/reputation": { section: "Risk Radar", title: "Reputation Early Warning" },
  "/brand-memory": { section: "Brand", title: "Brand Memory" },
  "/knowledge-graph": { section: "Brand", title: "Knowledge Graph" },
  "/content-intelligence": { section: "Analyse", title: "Content Intelligence" },
  "/claim-dna": { section: "Analyse", title: "ClaimDNA" },
  "/visual-dna": { section: "Analyse", title: "Visual DNA" },
  "/translation-guard": { section: "Analyse", title: "Translation Guard" },
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
    <header className="h-16 px-4 sm:px-6 lg:px-8 flex items-center gap-4 sticky top-0 z-30 select-none bg-white/85 backdrop-blur-xl border-b border-slate-200/80 shadow-[0_1px_3px_rgba(15,23,42,0.03)]">
      <button
        onClick={() => setMobileNavOpen(true)}
        className="lg:hidden p-2 -ml-2 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-slate-100"
        aria-label="Open navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 min-w-0 shrink-0 text-[13px]">
        <span className="hidden sm:inline font-medium text-slate-400">{page.section}</span>
        <span className="hidden sm:inline text-slate-300">/</span>
        <h1 className="font-bold text-slate-900 tracking-tight truncate">{page.title}</h1>
      </div>

      <div className="flex-1 flex justify-center min-w-0">
        <GlobalSearch />
      </div>

      <div className="flex items-center gap-1.5 shrink-0">
        <WorkspaceMenu />
        <NotificationsMenu />
        <HelpMenu />

        {/* User profile */}
        <div className="flex items-center gap-2.5 pl-3 ml-2 border-l border-slate-200">
          <div
            className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white flex items-center justify-center text-xs font-bold uppercase shadow-sm"
            aria-hidden
          >
            {initials(user?.full_name)}
          </div>
          <div className="hidden xl:block leading-tight">
            <div className="text-[13px] font-bold text-slate-900">{user?.full_name || "Guest"}</div>
            <div className="text-[11px] font-medium text-indigo-600">{user?.role || "—"}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
