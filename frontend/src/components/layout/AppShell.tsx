"use client";

import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AuthProvider, RequireAuth } from "@/lib/auth";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

// Public routes render full-page without the app chrome.
const PUBLIC_ROUTES = ["/", "/login", "/signup", "/guide"];

interface ShellState {
  mobileNavOpen: boolean;
  setMobileNavOpen: (open: boolean) => void;
}

const ShellContext = createContext<ShellState>({ mobileNavOpen: false, setMobileNavOpen: () => {} });

export function useShell() {
  return useContext(ShellContext);
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => setMobileNavOpen(false), [pathname]);

  return (
    <AuthProvider>
      {isPublic ? (
        children
      ) : (
        <ShellContext.Provider value={{ mobileNavOpen, setMobileNavOpen }}>
          <div className="flex min-h-screen w-full">
            <Sidebar />
            <div className="flex-1 min-w-0 flex flex-col min-h-screen">
              <Header />
              <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
                <RequireAuth>{children}</RequireAuth>
              </main>
            </div>
          </div>
        </ShellContext.Provider>
      )}
    </AuthProvider>
  );
}
